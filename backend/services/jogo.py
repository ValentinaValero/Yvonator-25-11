from uuid import uuid4
from fastapi import HTTPException
from ..algorithms.compatibilidade import classificar, escolher_pergunta, escolher_diferencial, pode_sugerir, grupo, diferenciais_do_personagem, ramo_ativo

def one(c, sql, args=()):
    row=c.execute(sql,args).fetchone()
    return dict(row) if row else None

def allrows(c, sql, args=()):
    return [dict(r) for r in c.execute(sql,args)]

def partida(c,pid):
    r=one(c,'SELECT * FROM partida WHERE id=?',(pid,))
    if not r: raise HTTPException(404,'Partida não encontrada')
    return r

def evento(c,pid,texto):
    c.execute('INSERT INTO historico(id_partida,descricao) VALUES(?,?)',(pid,texto))

def novo(c):
    if not one(c,'SELECT id FROM personagem LIMIT 1') or not one(c,'SELECT id FROM pergunta WHERE status=1 LIMIT 1'):
        raise HTTPException(503,'Base de personagens ou perguntas não importada')
    pid=str(uuid4())
    c.execute('INSERT INTO partida(id) VALUES(?)',(pid,))
    evento(c,pid,'Partida iniciada')
    avancar(c,pid)
    return estado(c,pid)

def ranking(c,pid):
    ps=allrows(c,'SELECT * FROM personagem ORDER BY id')
    qs=allrows(c,'SELECT * FROM pergunta ORDER BY id')
    mat={(r[0],r[1]):r[2] for r in c.execute('SELECT id_personagem,id_pergunta,resposta FROM personagem_pergunta')}
    resp=dict(c.execute('SELECT id_pergunta,resposta FROM resposta WHERE id_partida=?',(pid,)).fetchall())
    rejeitados={r[0] for r in c.execute('SELECT id_personagem FROM resultado WHERE id_partida=? AND confirmado=0',(pid,))}
    rank=classificar(ps,mat,resp,{q['id']:q['prioridade'] for q in qs},rejeitados,qs)
    return rank,[q for q in qs if q['status']],mat

def pendente(c,pid):
    return one(c,'''SELECT p.id,p.enunciado,p.categoria,pp.ordem FROM partida_pergunta pp JOIN pergunta p ON p.id=pp.id_pergunta LEFT JOIN resposta r ON r.id_partida=pp.id_partida AND r.id_pergunta=pp.id_pergunta WHERE pp.id_partida=? AND r.id IS NULL''',(pid,))

def resultado(c,pid):
    return one(c,'''SELECT r.id AS id_resultado,r.id_personagem,r.compatibilidade,r.confirmado,p.nome,p.materia,p.categoria,p.foto FROM resultado r JOIN personagem p ON p.id=r.id_personagem WHERE r.id_partida=? AND (r.confirmado IS NULL OR r.confirmado=1) ORDER BY r.id DESC LIMIT 1''',(pid,))

def estado(c,pid):
    p=partida(c,pid)
    return {'id_partida':pid,'status':p['status'],'quantidade_perguntas':p['quantidade_perguntas'],'pergunta':pendente(c,pid) if p['status']=='em_andamento' else None,'resultado':resultado(c,pid) if p['status'] in ('palpite','confirmada') else None}

def reservar_pergunta(c,pid,q,feitas):
    c.execute('INSERT INTO partida_pergunta VALUES(?,?,?)',(pid,q['id'],len(feitas)+1))
    evento(c,pid,f'Pergunta {q["id"]} apresentada' + (' (diferencial)' if grupo(q)=='diferencial' else ''))


def apresentar_palpite(c,pid,top):
    c.execute('INSERT INTO resultado(id_partida,id_personagem,compatibilidade) VALUES(?,?,?)',
              (pid,top['personagem']['id'],round(top['peso']*100,2)))
    c.execute("UPDATE partida SET status='palpite' WHERE id=?",(pid,))
    evento(c,pid,'Palpite apresentado')


def avancar(c,pid,apos_rejeicao=False):
    p=partida(c,pid)
    if p['status']!='em_andamento' or pendente(c,pid): return
    rank,qs,mat=ranking(c,pid)
    feitas={r[0] for r in c.execute('SELECT id_pergunta FROM partida_pergunta WHERE id_partida=?',(pid,))}
    resp=dict(c.execute('SELECT id_pergunta,resposta FROM resposta WHERE id_partida=?',(pid,)).fetchall())
    rank_global = rank
    rank, _ = ramo_ativo(rank_global, qs, mat, resp)
    ultima=one(c,"""SELECT p.id,p.categoria,r.resposta FROM resposta r JOIN pergunta p ON p.id=r.id_pergunta
        JOIN partida_pergunta pp ON pp.id_partida=r.id_partida AND pp.id_pergunta=r.id_pergunta
        WHERE r.id_partida=? ORDER BY pp.ordem DESC LIMIT 1""",(pid,))
    # A pergunta diferencial já foi reservada quando havia confiança suficiente.
    # Sim reforça o líder; Não sei não altera seu peso. Não voltar às gerais.
    if (rank and not apos_rejeicao and ultima and grupo(ultima)=='diferencial'
            and ultima['resposta'] in ('sim','naoSei')
            and mat.get((rank[0]['personagem']['id'],ultima['id']))=='sim'
            and any(q['id']==ultima['id'] for q in qs)):
        apresentar_palpite(c,pid,rank[0])
        return
    q=escolher_pergunta(rank_global,qs,mat,feitas,resp)
    # Mantém a pergunta estrutural inicial e retoma investigação após um não.
    ultima_negativa=bool(ultima and grupo(ultima)=='diferencial' and ultima['resposta']=='nao')
    if q and (grupo(q)=='genero' or apos_rejeicao or ultima_negativa):
        reservar_pergunta(c,pid,q,feitas)
        return
    if pode_sugerir(rank,esgotou=q is None):
        top=rank[0]
        diferencas=diferenciais_do_personagem(top['personagem']['id'],qs,mat)
        dif=escolher_diferencial(rank,qs,mat,feitas)
        if dif:
            reservar_pergunta(c,pid,dif,feitas)
            return
        # Sem diferencial registrada, mantém o fluxo anterior. Se já houve
        # uma confirmação para este perfil, não permite palpite tardio sem
        # nova diferencial: isso quebraria a regra da última pergunta.
        if not diferencas:
            apresentar_palpite(c,pid,top)
            return
    if q:
        reservar_pergunta(c,pid,q,feitas)
    else:
        c.execute("UPDATE partida SET status='sem_resultado',data_fim=CURRENT_TIMESTAMP WHERE id=?",(pid,))
        evento(c,pid,'Sem evidência suficiente, confirmação final disponível ou candidatos restantes')

def responder(c,pid,entrada):
    p=partida(c,pid)
    anterior=one(c,'SELECT resposta FROM resposta WHERE id_partida=? AND id_pergunta=?',(pid,entrada.id_pergunta))
    if anterior:
        if anterior['resposta']==entrada.resposta: return estado(c,pid)
        raise HTTPException(409,'Pergunta já respondida')
    q=pendente(c,pid)
    if p['status']!='em_andamento' or not q or q['id']!=entrada.id_pergunta:
        raise HTTPException(409,'Esta não é a pergunta atual')
    c.execute('INSERT INTO resposta(id_partida,id_pergunta,resposta) VALUES(?,?,?)',(pid,q['id'],entrada.resposta))
    c.execute('UPDATE partida SET quantidade_perguntas=quantidade_perguntas+1 WHERE id=?',(pid,))
    evento(c,pid,f'Pergunta {q["id"]} respondida')
    avancar(c,pid)
    return estado(c,pid)

def confirmar(c,pid,entrada):
    p=partida(c,pid)
    r=one(c,'SELECT * FROM resultado WHERE id=? AND id_partida=?',(entrada.id_resultado,pid))
    if not r: raise HTTPException(404,'Resultado não encontrado')
    if r['confirmado'] is not None:
        if bool(r['confirmado'])==entrada.confirmado: return estado(c,pid)
        raise HTTPException(409,'Resultado já avaliado')
    if p['status']!='palpite': raise HTTPException(409,'Não há palpite pendente')
    c.execute('UPDATE resultado SET confirmado=? WHERE id=?',(int(entrada.confirmado),r['id']))
    evento(c,pid,'Palpite confirmado' if entrada.confirmado else 'Palpite rejeitado')
    if entrada.confirmado:
        c.execute("UPDATE partida SET status='confirmada',data_fim=CURRENT_TIMESTAMP WHERE id=?",(pid,))
    else:
        c.execute("UPDATE partida SET status='em_andamento' WHERE id=?",(pid,))
        avancar(c,pid,apos_rejeicao=True)
    return estado(c,pid)
