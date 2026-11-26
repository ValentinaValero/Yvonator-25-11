"""Consolida as duas faixas abaixo de 30 anos sem apagar histórico."""
from .database import db
from .adicionar_perfil import FAIXAS

NOVA = 'Seu personagem tem menos de 30 anos?'


def atualizar():
    with db() as c:
        antigas = []
        for faixa in ('menor20', '20-29'):
            rows = c.execute('SELECT id FROM pergunta WHERE categoria=? AND enunciado=?', ('idade', FAIXAS[faixa])).fetchall()
            if len(rows) != 1:
                raise ValueError('Importe primeiro os dados de perfil da versão 5; faixa ausente ou duplicada.')
            antigas.append(rows[0][0])
        rows = c.execute('SELECT id,categoria,prioridade FROM pergunta WHERE enunciado=?', (NOVA,)).fetchall()
        if len(rows)>1 or (rows and (rows[0]['categoria']!='idade' or rows[0]['prioridade']!=1.0)):
            raise ValueError('Configuração conflitante da nova faixa.')
        qid = rows[0]['id'] if rows else c.execute('INSERT INTO pergunta(enunciado,categoria,prioridade) VALUES(?,?,?)',(NOVA,'idade',1.0)).lastrowid
        count=0
        for p in c.execute('SELECT id FROM personagem').fetchall():
            pid=p[0]
            valores = dict(c.execute('SELECT id_pergunta,resposta FROM personagem_pergunta WHERE id_personagem=? AND id_pergunta IN (?,?)',(pid,*antigas)))
            if list(valores.values()).count('sim')>1:
                raise ValueError('Faixas originais conflitantes.')
            r='sim' if 'sim' in valores.values() else ('nao' if len(valores)==2 and all(v=='nao' for v in valores.values()) else None)
            old=c.execute('SELECT resposta FROM personagem_pergunta WHERE id_personagem=? AND id_pergunta=?',(pid,qid)).fetchone()
            if old and old[0]!=r:
                raise ValueError('Vínculo existente divergente. Nenhuma alteração gravada.')
            if not old and r is not None:
                c.execute('INSERT INTO personagem_pergunta VALUES(?,?,?)',(pid,qid,r)); count+=1
        c.execute('UPDATE pergunta SET status=0 WHERE id IN (?,?)',antigas)
        c.execute('UPDATE pergunta SET status=1 WHERE id=?',(qid,))
    return count


if __name__=='__main__':
    print(f'Faixa abaixo de 30 anos ativada. Novos vínculos: {atualizar()}. Histórico preservado.')
