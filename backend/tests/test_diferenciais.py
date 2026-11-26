import json
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.importar import importar
from backend.adicionar_diferenciais import adicionar
from backend.database import db
from backend.algorithms.compatibilidade import classificar, escolher_pergunta

@pytest.fixture
def base(tmp_path,monkeypatch):
    monkeypatch.setenv('YVONATOR_DB',str(tmp_path/'teste.sqlite3'))
    qs=[{'id':q,'enunciado':f'Pergunta geral {q}?','categoria':'teste'} for q in range(1,8)]
    ps=[{'id':i+1,'nome':f'Personagem {i+1}','respostas':{str(q):'sim' if (i>>((q-1)%5))&1 else 'nao' for q in range(1,8)}} for i in range(32)]
    seed=tmp_path/'seed.json';seed.write_text(json.dumps({'personagens':ps,'perguntas':qs}));importar(seed)
    dif=tmp_path/'dif.json';dif.write_text(json.dumps({'perguntas':[{'enunciado':'Confirmação do perfil 32?','personagens':['Personagem 32']},{'enunciado':'Confirmação do perfil 1?','personagens':['Personagem 1']}]}))
    with TestClient(app) as client:
        yield client,dif


def responder(c,s,a):
    r=c.post(f'/api/partidas/{s["id_partida"]}/responder',json={'id_pergunta':s['pergunta']['id'],'resposta':a});r.raise_for_status();return r.json()


def ate_diferencial(base):
    c,dif=base;assert adicionar(dif)==(2,2)
    s=c.post('/api/partidas').json();feitas=set()
    while s['status']=='em_andamento' and s['pergunta']['categoria']!='diferencial':
        assert s['pergunta']['id'] not in feitas;feitas.add(s['pergunta']['id']);s=responder(c,s,'sim')
    assert s['status']=='em_andamento' and s['pergunta']['enunciado']=='Confirmação do perfil 32?'
    assert len(feitas)>=4
    return c,s,feitas

@pytest.mark.parametrize('a',['sim','naoSei'])
def test_diferencial_final_do_lider(base,a):
    c,s,_=ate_diferencial(base)
    assert c.get(f'/api/partidas/{s["id_partida"]}').json()==s
    s=responder(c,s,a)
    assert s['status']=='palpite' and s['resultado']['id_personagem']==32


def test_nao_reabre_investigacao(base):
    c,s,feitas=ate_diferencial(base);qid=s['pergunta']['id'];pid=s['id_partida']
    s=responder(c,s,'nao')
    assert s['status']!='palpite' or s['resultado']['id_personagem']!=32
    if s['status']=='em_andamento':
        assert s['pergunta']['categoria']!='diferencial'
        assert s['pergunta']['id'] not in feitas|{qid}
    with db() as conn:
        from backend.services.jogo import ranking
        rank,_,_=ranking(conn,pid)
        assert any(i['personagem']['id']==32 for i in rank)


def test_migracao_aditiva_e_idempotente(base):
    c,dif=base;s=c.post('/api/partidas').json()
    assert adicionar(dif)==(2,2);assert adicionar(dif)==(0,0)
    assert c.get(f'/api/partidas/{s["id_partida"]}').json()==s
    with db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM pergunta WHERE categoria='diferencial'").fetchone()[0]==2
        assert conn.execute("SELECT COUNT(*) FROM personagem_pergunta pp JOIN pergunta p ON p.id=pp.id_pergunta WHERE p.categoria='diferencial'").fetchone()[0]==2


def test_diferenciais_nunca_na_selecao_normal():
    qs=[dict(id=1,enunciado='Geral?',categoria='teste',prioridade=1),dict(id=2,enunciado='Final?',categoria='diferencial',prioridade=2)]
    ps=[{'id':1},{'id':2}];mat={(1,1):'sim',(2,1):'nao',(1,2):'sim',(2,2):'nao'}
    rank=classificar(ps,mat,{}, {1:1,2:2},set(),qs)
    assert escolher_pergunta(rank,qs,mat,{1},{1:'sim'}) is None


def test_desconhecido_neutro_e_nao_penaliza_apenas_vinculado():
    qs=[dict(id=2,categoria='diferencial',prioridade=2)];ps=[{'id':1},{'id':2},{'id':3}];mat={(1,2):'sim'}
    r=classificar(ps,mat,{2:'naoSei'},{2:2},set(),qs);assert all(abs(x['peso']-1/3)<1e-9 for x in r)
    r=classificar(ps,mat,{2:'nao'},{2:2},set(),qs);assert r[0]['peso']==r[1]['peso'] and r[-1]['personagem']['id']==1 and r[-1]['peso']>0


def test_sem_diferencial_segue_normalmente(base):
    c,dif=base;adicionar(dif);s=c.post('/api/partidas').json();feitas=set();i=15
    while s['status']=='em_andamento':
        q=s['pergunta'];assert q['categoria']!='diferencial' and q['id'] not in feitas;feitas.add(q['id']);s=responder(c,s,'sim' if (i>>((q['id']-1)%5))&1 else 'nao')
    assert s['status']=='palpite' and s['resultado']['id_personagem']==16


@pytest.mark.parametrize('a',['sim','naoSei'])
def test_confirmacao_final_nao_volta_para_perguntas_gerais(base,a,monkeypatch):
    c,s,_=ate_diferencial(base)
    from backend.services import jogo
    def nao_reavaliar(*args,**kwargs):
        pytest.fail('Uma confirmação final aceita não deve passar pela seleção geral novamente.')
    monkeypatch.setattr(jogo,'escolher_pergunta',nao_reavaliar)
    s=responder(c,s,a)
    assert s['status']=='palpite' and s['resultado']['id_personagem']==32


def test_diferencial_ja_usada_nao_permite_palpite_tardio(base,monkeypatch):
    c,s,_=ate_diferencial(base)
    pid=s['id_partida'];qid=s['pergunta']['id']
    from backend.services import jogo
    # Cria o estado de recuperação com uma pergunta geral após a negativa.
    with db() as conn:
        conn.execute('INSERT INTO resposta(id_partida,id_pergunta,resposta) VALUES(?,?,?)',(pid,qid,'nao'))
        feitas={r[0] for r in conn.execute('SELECT id_pergunta FROM partida_pergunta WHERE id_partida=?',(pid,))}
        geral=next((i for i in range(1,8) if i not in feitas),None)
        assert geral is not None
        conn.execute('INSERT INTO partida_pergunta VALUES(?,?,?)',(pid,geral,len(feitas)+1))
        conn.execute('INSERT INTO resposta(id_partida,id_pergunta,resposta) VALUES(?,?,?)',(pid,geral,'sim'))
        rank,qs,mat=jogo.ranking(conn,pid)
        top=next(i for i in rank if i['personagem']['id']==32)
        monkeypatch.setattr(jogo,'ranking',lambda *_:([top],qs,mat))
        monkeypatch.setattr(jogo,'escolher_pergunta',lambda *a:None)
        monkeypatch.setattr(jogo,'pode_sugerir',lambda *a,**k:True)
        jogo.avancar(conn,pid)
        assert jogo.estado(conn,pid)['status']=='sem_resultado'


def test_escolhe_outra_diferencial_sem_repetir():
    from backend.algorithms.compatibilidade import escolher_diferencial
    qs=[dict(id=i,categoria='diferencial',prioridade=2) for i in (1,2,3)]
    rank=[{'personagem':{'id':1}}]
    mat={(1,1):'sim',(1,2):'sim',(2,3):'sim'}
    assert escolher_diferencial(rank,qs,mat,{1})['id']==2
    assert escolher_diferencial(rank,qs,mat,{1,2}) is None
