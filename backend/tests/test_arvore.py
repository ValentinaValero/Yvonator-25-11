"""Regressões da árvore adaptativa, sem alterar o banco real."""
import sqlite3
from pathlib import Path
from types import SimpleNamespace
from backend.algorithms.compatibilidade import classificar, escolher_pergunta, ramo_ativo
from backend.services import jogo


def base_real():
    origem = sqlite3.connect(f"{(Path(__file__).resolve().parents[1]/'data'/'yvonator.sqlite3').as_uri()}?mode=ro", uri=True)
    c = sqlite3.connect(':memory:')
    origem.backup(c)
    origem.close()
    c.row_factory = sqlite3.Row
    return c


def dados(c):
    ps = jogo.allrows(c, 'SELECT * FROM personagem ORDER BY id')
    qs = jogo.allrows(c, 'SELECT * FROM pergunta WHERE status=1 ORDER BY id')
    mat = {(r[0],r[1]):r[2] for r in c.execute('SELECT * FROM personagem_pergunta')}
    return ps, qs, mat


def avaliar(ps, qs, mat, resp, excluidos=()):
    rank = classificar(ps,mat,resp,{q['id']:q['prioridade'] for q in qs},set(excluidos),qs)
    ramo,rec = ramo_ativo(rank,qs,mat,resp)
    q = escolher_pergunta(rank,qs,mat,set(resp),resp)
    return ramo,rec,q


def test_educacao_fisica_poda_disciplinas_na_base_real():
    with base_real() as c:
        ps,qs,mat = dados(c)
        pe = next(q['id'] for q in qs if 'leciona Educação Física' in q['enunciado'])
        assert sum(mat.get((p['id'],pe))=='sim' for p in ps)==2
        ramo,rec,q = avaliar(ps,qs,mat,{pe:'sim'})
        assert not rec
        assert all(mat.get((i['personagem']['id'],pe)) in ('sim',None) for i in ramo)
        assert q and q['categoria'] != 'disciplina'
        # Mesmo quando o jogador desconhece todas as outras perguntas gerais,
        # nenhuma disciplina sem sobreposição volta ao jogo.
        resp = {pe:'sim'}
        while q:
            assert q['id'] not in resp
            assert q['categoria'] != 'disciplina'
            resp[q['id']] = 'naoSei'
            _,rec,q = avaliar(ps,qs,mat,resp)
            assert not rec


def test_poda_sim_nao_cursos_sobrepostos_e_ausencia():
    qs = [dict(id=i,enunciado=t,categoria=g,prioridade=1) for i,t,g in [
        (1,'Leciona Educação Física?','disciplina'),(2,'Leciona Matemática?','disciplina'),
        (3,'Leciona Português?','disciplina'),(4,'Usa óculos?','aparência')]]
    ps = [{'id':i} for i in range(1,5)]
    linhas = [('sim','sim','nao','sim'),('sim','nao','nao','sim'),('nao','nao','sim','nao'),(None,None,None,'sim')]
    mat = {(i,j):a for i,linha in enumerate(linhas,1) for j,a in enumerate(linha,1) if a is not None}
    ramo,rec,q = avaliar(ps,qs,mat,{1:'sim'})
    assert {i['personagem']['id'] for i in ramo} == {1,2,4}
    assert not rec and q['id']==2  # sobreposição real continua válida
    ramo,rec,q = avaliar(ps,qs,mat,{1:'sim',2:'nao'})
    assert {i['personagem']['id'] for i in ramo} == {2,4} and not rec
    ramo,rec,q = avaliar(ps,qs,mat,{1:'naoSei'})
    assert len(ramo)==4 and not rec
    # Um conflito ou a rejeição de todos os perfis exatos abre a alternativa
    # mais próxima, mas perfis rejeitados não retornam.
    ramo,rec,q = avaliar(ps,qs,mat,{1:'sim',4:'nao'},excluidos={4})
    assert rec and {i['personagem']['id'] for i in ramo}=={1,2}
    ramo,rec,q = avaliar(ps,qs,mat,{1:'sim'},excluidos={1,2,4})
    assert rec and {i['personagem']['id'] for i in ramo}=={3}


def test_partidas_completas_com_base_real():
    with base_real() as c:
        ps,qs,mat = dados(c)
        for p in ps:
            s = jogo.novo(c)
            feitas = set()
            while s['status']=='em_andamento':
                qid = s['pergunta']['id']
                assert qid not in feitas
                feitas.add(qid)
                s = jogo.responder(c,s['id_partida'],SimpleNamespace(
                    id_pergunta=qid,resposta=mat.get((p['id'],qid),'naoSei')))
            assert s['status']=='palpite' and s['resultado']['id_personagem']==p['id']
            s = jogo.confirmar(c,s['id_partida'],SimpleNamespace(
                id_resultado=s['resultado']['id_resultado'],confirmado=True))
            assert s['status']=='confirmada'
