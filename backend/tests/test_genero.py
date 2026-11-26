import json
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.importar import importar
from backend.adicionar_genero import adicionar, ENUNCIADO, PRIORIDADE
from backend.database import db
from backend.algorithms.compatibilidade import classificar, escolher_pergunta

@pytest.fixture
def base(tmp_path,monkeypatch):
    monkeypatch.setenv('YVONATOR_DB',str(tmp_path/'teste.sqlite3'))
    qs=[{'id':1,'enunciado':'Seu personagem é professor(a)?','categoria':'função'}, {'id':2,'enunciado':'Usa óculos?','categoria':'aparência'}]
    ps=[{'id':i+1,'nome':f'P{i+1}','respostas':{'1':'sim' if i<2 else 'nao','2':'sim' if i%2 else 'nao'}} for i in range(4)]
    seed=tmp_path/'seed.json';seed.write_text(json.dumps({'personagens':ps,'perguntas':qs}));importar(seed)
    path=tmp_path/'genero.json';path.write_text(json.dumps({'personagens':[{'nome':f'P{i+1}','genero':g} for i,g in enumerate(['F','F','M','M'])]}))
    return path

@pytest.mark.parametrize('resposta',['sim','nao','naoSei'])
def test_primeira_pergunta_genero(base,resposta):
    adicionar(base)
    with TestClient(app) as c:
        s=c.post('/api/partidas').json()
        assert s['pergunta']['enunciado']==ENUNCIADO
        qid=s['pergunta']['id']
        r=c.post(f'/api/partidas/{s["id_partida"]}/responder',json={'id_pergunta':qid,'resposta':resposta});r.raise_for_status()
        assert r.json()['pergunta']['id']==2


def test_migracao_preserva_partida(base):
    with TestClient(app) as c:
        s=c.post('/api/partidas').json()
        assert adicionar(base)==(1,4)
        assert adicionar(base)==(0,0)
        assert c.get(f'/api/partidas/{s["id_partida"]}').json()==s
    with db() as c:
        assert c.execute('SELECT COUNT(*) FROM partida').fetchone()[0]==1


def test_genero_foco_e_neutralidade():
    ps=[{'id':i} for i in range(1,5)]
    qs=[dict(id=1,enunciado=ENUNCIADO,categoria='genero',prioridade=PRIORIDADE),dict(id=2,enunciado='Geral?',categoria='aparência',prioridade=1),dict(id=3,enunciado='Outra?',categoria='aparência',prioridade=1)]
    mat={(i,1):'sim' if i<=2 else 'nao' for i in range(1,5)}
    mat.update({(i,2):'sim' if i==1 else 'nao' for i in range(1,5)})
    mat.update({(i,3):'sim' if i>2 else 'nao' for i in range(1,5)})
    pri={q['id']:q['prioridade'] for q in qs}
    r=classificar(ps,mat,{1:'sim'},pri,set(),qs)
    assert {v['personagem']['id'] for v in r[:2]}=={1,2} and len(r)==4
    assert escolher_pergunta(r,qs,mat,{1},{1:'sim'})['id']==2
    r=classificar(ps,mat,{1:'naoSei'},pri,set(),qs)
    assert all(abs(v['peso']-.25)<1e-9 for v in r)
    r=classificar(ps,mat,{1:'sim'},pri,{1,2},qs)
    assert {v['personagem']['id'] for v in r}=={3,4}


def test_barba_deduzida_da_base_sem_regra_universal():
    qs=[dict(id=1,enunciado=ENUNCIADO,categoria='genero',prioridade=PRIORIDADE),
        dict(id=2,enunciado='Seu personagem tem barba?',categoria='aparência',prioridade=100),
        dict(id=3,enunciado='Seu personagem usa óculos?',categoria='aparência',prioridade=1)]
    ps=[{'id':i} for i in range(1,5)]
    mat={(i,1):'sim' if i<=2 else 'nao' for i in range(1,5)}
    mat.update({(i,2):'sim' if i>2 else 'nao' for i in range(1,5)})
    mat.update({(i,3):'sim' if i%2 else 'nao' for i in range(1,5)})
    pri={q['id']:q['prioridade'] for q in qs}
    rank=classificar(ps,mat,{1:'sim'},pri,set(),qs)
    assert escolher_pergunta(rank,qs,mat,{1},{1:'sim'})['id']==3
    # Se a base mudar, a relação deixa de valer.
    mat[(1,2)]='sim'
    rank=classificar(ps,mat,{1:'sim'},pri,set(),qs)
    assert escolher_pergunta(rank,qs,mat,{1},{1:'sim'})['id']==2


def test_comprimento_cabelo_nao_repetido():
    qs=[dict(id=i,enunciado=t,categoria='aparência',prioridade=p) for i,t,p in [
        (1,'Seu personagem tem cabelo curto?',1),(2,'Seu personagem tem cabelo longo?',100),
        (3,'Seu personagem usa óculos?',1)]]
    ps=[{'id':i} for i in range(1,5)]
    mat={(i,1):'sim' if i<=2 else 'nao' for i in range(1,5)}
    mat.update({(i,2):'nao' if i<=2 else 'sim' for i in range(1,5)})
    mat.update({(i,3):'sim' if i%2 else 'nao' for i in range(1,5)})
    pri={q['id']:q['prioridade'] for q in qs}
    rank=classificar(ps,mat,{1:'sim'},pri,set(),qs)
    assert escolher_pergunta(rank,qs,mat,{1},{1:'sim'})['id']==3
    assert escolher_pergunta(rank,qs,mat,{1,3},{1:'sim',3:'naoSei'}) is None
