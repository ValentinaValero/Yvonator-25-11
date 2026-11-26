import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.importar import importar
from backend.database import db

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setenv('YVONATOR_DB',str(tmp_path/'teste.sqlite3'))
    qs=[{'id':q,'enunciado':f'Pergunta {q}?','categoria':'teste'} for q in range(1,7)]
    ps=[{'id':i+1,'nome':f'Professor fictício {i+1}','respostas':{str(q):'sim' if (i>>(q-1))&1 else 'nao' for q in range(1,7)}} for i in range(32)]
    # A sexta pergunta é redundante, mas válida para alguns perfis.
    for p in ps:p['respostas']['6']=p['respostas']['1']
    f=tmp_path/'seed.json';f.write_text(json.dumps({'personagens':ps,'perguntas':qs}));importar(f)
    with TestClient(app) as c: yield c

def start(c):return c.post('/api/partidas').json()
def answer(c,s,a):return c.post(f'/api/partidas/{s["id_partida"]}/responder',json={'id_pergunta':s['pergunta']['id'],'resposta':a})
def confirm(c,s,ok):return c.post(f'/api/partidas/{s["id_partida"]}/confirmar-resultado',json={'id_resultado':s['resultado']['id_resultado'],'confirmado':ok})

def test_partida_completa(client):
    s=start(client);seen=set()
    assert client.get('/api/personagens').status_code==200
    while s['status']=='em_andamento':
        q=s['pergunta']['id'];assert q not in seen;seen.add(q)
        assert client.get(f'/api/partidas/{s["id_partida"]}/proxima-pergunta').json()==s
        s=answer(client,s,'sim').json()
    assert s['status']=='palpite' and s['resultado']['id_personagem']==32
    assert confirm(client,s,True).json()['status']=='confirmada'
    with db() as c:assert c.execute('SELECT COUNT(*) FROM resposta').fetchone()[0]==len(seen)

def test_desconhecido(client):
    s=start(client);seen=set()
    while s['status']=='em_andamento':
        assert s['pergunta']['id'] not in seen;seen.add(s['pergunta']['id']);s=answer(client,s,'naoSei').json()
    assert s['status']=='sem_resultado'

def test_rejeicao(client):
    s=start(client)
    while s['status']=='em_andamento':s=answer(client,s,'sim').json()
    x=confirm(client,s,False).json();assert x['status'] in ('em_andamento','palpite','sem_resultado')
    with db() as c:assert c.execute('SELECT confirmado FROM resultado').fetchone()[0]==0
    if x['status']=='palpite':assert x['resultado']['id_personagem']!=s['resultado']['id_personagem']

def test_validacao_e_reenvio(client):
    s=start(client);pid=s['id_partida'];q=s['pergunta']['id']
    assert answer(client,s,'talvez').status_code==422
    assert client.post(f'/api/partidas/{pid}/responder',json={'id_pergunta':999,'resposta':'sim'}).status_code==409
    a=answer(client,s,'sim');assert a.status_code==200
    assert answer(client,s,'sim').json()==a.json()
    assert answer(client,s,'nao').status_code==409
    assert client.get('/api/partidas/inexistente').status_code==404

def test_classificacao_nao_sei_e_contradicao():
    from backend.algorithms.compatibilidade import classificar
    ps=[{'id':1},{'id':2}];mat={(1,1):'sim',(2,1):'nao'}
    desconhecida=classificar(ps,mat,{1:'naoSei'},{1:1},set())
    assert [r['peso'] for r in desconhecida]==[.5,.5]
    rank=classificar(ps,mat,{1:'nao'},{1:1},set())
    assert rank[0]['personagem']['id']==2 and 0<rank[1]['peso']<rank[0]['peso']
    assert len(rank)==2

def test_rejeitar_com_pergunta_disponivel(client,monkeypatch):
    # Força um palpite antecipado apenas neste teste para exercitar a retomada.
    import backend.services.jogo as jogo
    original=jogo.pode_sugerir
    monkeypatch.setattr(jogo,'pode_sugerir',lambda rank,esgotou=False: bool(rank and rank[0]['acertos']))
    s=answer(client,start(client),'sim').json()
    assert s['status']=='palpite'
    monkeypatch.setattr(jogo,'pode_sugerir',original)
    x=confirm(client,s,False).json()
    assert x['status']=='em_andamento' and x['pergunta'] is not None
    assert x['quantidade_perguntas']==1
