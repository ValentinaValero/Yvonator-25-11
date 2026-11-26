# Testes legados de uma versão anterior ao ZIP: dependem de funções, rotas e
# seed que já não existem na V7 recebida. Preservados para consulta histórica.
import pytest
pytest.skip('Suíte V5 legada: API/seed ausentes na versão recebida', allow_module_level=True)

import json
from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import app
from backend.importar import importar
from backend.database import db
from backend.algorithms.compatibilidade import MAX_PERGUNTAS, classificar, escolher_diferencial, candidatos_ativos

SEED=Path(__file__).resolve().parents[1]/'data'/'yvonator_dados_locais.json'

def iniciar(tmp_path, monkeypatch):
    monkeypatch.setenv('YVONATOR_DB',str(tmp_path/'v5.sqlite3'))
    importar(SEED)
    return TestClient(app)

def test_limite_e_sem_evidencia(tmp_path,monkeypatch):
    with iniciar(tmp_path,monkeypatch) as c:
        s=c.post('/api/partidas').json(); ids=[]
        while s['status']=='em_andamento':
            q=s['pergunta']['id'];assert q not in ids;ids.append(q)
            s=c.post(f'/api/partidas/{s["id_partida"]}/responder',json={'id_pergunta':q,'resposta':'naoSei'}).json()
        assert s['status']=='sem_resultado' and len(ids)<=MAX_PERGUNTAS

def test_voltar(tmp_path,monkeypatch):
    with iniciar(tmp_path,monkeypatch) as c:
        s=c.post('/api/partidas').json();pid=s['id_partida'];qid=s['pergunta']['id']
        assert c.post(f'/api/partidas/{pid}/voltar',json={}).status_code==409
        s=c.post(f'/api/partidas/{pid}/responder',json={'id_pergunta':qid,'resposta':'sim'}).json()
        assert s['quantidade_perguntas']==1 and s['pergunta']['id']!=qid
        s=c.post(f'/api/partidas/{pid}/voltar',json={}).json()
        assert s['status']=='em_andamento' and s['quantidade_perguntas']==0 and s['pergunta']['id']==qid
        s=c.post(f'/api/partidas/{pid}/responder',json={'id_pergunta':qid,'resposta':'nao'}).json()
        assert s['quantidade_perguntas']==1
        with db(escrita=False) as con:
            assert con.execute('select resposta from resposta where id_partida=?',(pid,)).fetchone()[0]=='nao'

def test_restricao_consultas(tmp_path,monkeypatch):
    monkeypatch.setenv('YVONATOR_ADMIN_TOKEN','segredo-teste')
    with iniciar(tmp_path,monkeypatch) as c:
        assert c.get('/api/personagens').status_code==403
        assert c.get('/api/personagens',headers={'Authorization':'Bearer segredo-teste'}).status_code==200
        assert c.post('/api/partidas').status_code==201

def test_diferencial_desempata_sem_inventar_negativas():
    ps=[{'id':1},{'id':2}];qs=[dict(id=1,categoria='diferencial',prioridade=2,enunciado='Confirma?')]
    mat={(1,1):'sim'};rank=classificar(ps,mat,{}, {1:2},set(),qs)
    assert len(candidatos_ativos(rank))==2
    assert escolher_diferencial(rank,qs,mat,set(),desempate=True)['id']==1
    r=classificar(ps,mat,{1:'sim'},{1:2},set(),qs)
    assert r[0]['personagem']['id']==1 and r[1]['erros']==0

def test_base_completa_e_diferencial_compartilhada():
    d=json.loads(SEED.read_text(encoding='utf8')); assert len(d['personagens'])==41
    q=next(q for q in d['perguntas'] if q['enunciado']=='Seu personagem já trabalhou como policial?')
    valores=[p['respostas'].get(str(q['id'])) for p in d['personagens']]
    assert valores.count('sim')==2 and valores.count(None)==39
