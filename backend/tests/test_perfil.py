import json
import pytest
from backend.database import db
from backend.importar import importar
from backend.adicionar_perfil import adicionar, FAIXAS, CAMPOS
from backend.algorithms.compatibilidade import classificar, escolher_pergunta
from backend.services.jogo import novo

@pytest.fixture
def base(tmp_path, monkeypatch):
    monkeypatch.setenv('YVONATOR_DB',str(tmp_path/'teste.sqlite3'))
    seed=tmp_path/'seed.json'
    seed.write_text(json.dumps({'personagens':[{'id':i,'nome':f'P{i}','respostas':{'1':'sim' if i%2 else 'nao', '2':'sim' if i%2 else 'nao'}} for i in range(1,5)],'perguntas':[{'id':1,'enunciado':'Seu personagem é professor(a)?','categoria':'função'},{'id':2,'enunciado':'Usa óculos?','categoria':'aparência'}]}))
    importar(seed)
    path=tmp_path/'perfil.json'
    path.write_text(json.dumps({'personagens':[dict(nome=f'P{i}',faixa_idade=f,filhos=None if i==4 else 'sim',viajou_para_fora='sim',nasceu_em_outro_estado_ou_cidade='nao') for i,f in enumerate(['20-29','30-49','80+',None],1)]}))
    return path

def test_migracao_aditiva_e_repetivel(base):
    with db() as c:
        partida=novo(c)
    assert adicionar(base)==(10,32)
    assert adicionar(base)==(0,0)
    with db() as c:
        assert c.execute('SELECT COUNT(*) FROM partida WHERE id=?',(partida['id_partida'],)).fetchone()[0]==1
        assert c.execute('SELECT COUNT(*) FROM pergunta').fetchone()[0]==12
        assert c.execute("SELECT COUNT(*) FROM personagem_pergunta pp JOIN pergunta p ON p.id=pp.id_pergunta WHERE p.categoria='idade' AND pp.id_personagem=4").fetchone()[0]==0
        assert c.execute("SELECT COUNT(*) FROM personagem_pergunta pp JOIN pergunta p ON p.id=pp.id_pergunta WHERE p.categoria='idade' AND resposta='sim'").fetchone()[0]==3
        assert c.execute("SELECT COUNT(*) FROM personagem_pergunta WHERE id_pergunta=1").fetchone()[0]==4

def test_conflito_rollback(base):
    adicionar(base)
    data=json.loads(base.read_text()); data['personagens'][0]['faixa_idade']='80+';base.write_text(json.dumps(data))
    with pytest.raises(ValueError):adicionar(base)
    with db() as c:
        assert c.execute("SELECT resposta FROM personagem_pergunta pp JOIN pergunta p ON p.id=pp.id_pergunta WHERE p.enunciado=? AND pp.id_personagem=1",(FAIXAS['20-29'],)).fetchone()[0]=='sim'

def test_faixas_exclusivas():
    qs=[dict(id=i,enunciado=t,categoria=g,prioridade=1.) for i,t,g in [(1,FAIXAS['20-29'],'idade'),(2,FAIXAS['30-49'],'idade'),(3,CAMPOS['filhos'],'perfil')]]
    ps=[{'id':i} for i in range(1,5)]
    mat={(i,q):a for i,vs in enumerate([['sim','nao','sim'],['sim','nao','nao'],['nao','sim','sim'],['nao','sim','nao']],1) for q,a in enumerate(vs,1)}
    pri={q['id']:q['prioridade'] for q in qs}
    for resp in ('sim','nao'):
        r=classificar(ps,mat,{1:resp},pri,set(),qs)
        assert escolher_pergunta(r,qs,mat,{1},{1:resp})['id']==3
        assert escolher_pergunta(r,qs,mat,{1,3},{1:resp,3:'naoSei'}) is None
    r=classificar(ps,mat,{1:'naoSei'},pri,set(),qs)
    assert escolher_pergunta(r,qs,mat,{1},{1:'naoSei'})['id']==2

def test_perfil_independente():
    qs=[dict(id=i,enunciado=t,categoria='perfil',prioridade=1.) for i,t in enumerate(CAMPOS.values(),1)]
    ps=[{'id':i} for i in range(1,5)]
    mat={(i,q):a for i,vs in enumerate([['sim','sim','nao'],['sim','nao','nao'],['nao','sim','sim'],['nao','nao','sim']],1) for q,a in enumerate(vs,1)}
    r=classificar(ps,mat,{1:'sim'},{q['id']:1 for q in qs},set(),qs)
    assert escolher_pergunta(r,qs,mat,{1},{1:'sim'})['id']==2


def test_migracao_menor30(base):
    from backend.atualizar_idade import atualizar, NOVA
    adicionar(base)
    with db() as c:
        s=novo(c)
    assert atualizar()==3
    assert atualizar()==0
    assert adicionar(base)==(0,0)
    with db() as c:
        vals=dict(c.execute('SELECT id_personagem,resposta FROM personagem_pergunta pp JOIN pergunta p ON p.id=pp.id_pergunta WHERE p.enunciado=?',(NOVA,)))
        assert vals=={1:'sim',2:'nao',3:'nao'}
        assert c.execute('SELECT COUNT(*) FROM pergunta WHERE categoria=\'idade\' AND status=1').fetchone()[0]==6
        assert c.execute('SELECT COUNT(*) FROM partida WHERE id=?',(s['id_partida'],)).fetchone()[0]==1
