import sqlite3
from pathlib import Path
from backend.algorithms.compatibilidade import classificar, escolher_pergunta, pergunta_professor
from backend.atualizacao_v8 import atualizar
from backend.services import jogo


def q(i,texto,categoria,p=1):
    return dict(id=i,enunciado=texto,categoria=categoria,prioridade=p)


def escolher(qs, linhas, respostas):
    ps=[{'id':i} for i in range(1,len(linhas)+1)]
    mat={(i,a['id']):r for i,linha in enumerate(linhas,1) for a,r in zip(qs,linha)}
    rank=classificar(ps,mat,respostas,{a['id']:a['prioridade'] for a in qs},set(),qs)
    return escolher_pergunta(rank,qs,mat,set(respostas),respostas),rank


def test_aparencia_e_adaptacao_sem_alterar_classificacao():
    qs=[q(1,'Usa óculos?','aparência'),q(2,'Tem barba?','aparência'),q(3,'Tem cabelo longo?','aparência'),q(4,'Leciona Matemática?','disciplina')]
    linhas=[('sim','sim','sim','sim'),('nao','nao','nao','nao'),('sim','nao','sim','nao'),('nao','sim','nao','sim')]
    assert escolher(qs,linhas,{})[0]['categoria']=='aparência'
    assert escolher(qs,linhas,{1:'naoSei'})[0]['categoria']=='aparência'
    prox,rank=escolher(qs,linhas,{1:'naoSei',2:'naoSei'})
    # Dois desconhecimentos reduzem a preferência; uma categoria igualmente
    # informativa pode passar à frente.
    assert prox['id']==4
    assert all(r['peso']==.25 for r in rank)


def test_cursos_recebem_prioridade_apos_tecnico():
    qs=[q(1,'As matérias lecionadas são do técnico?','modalidade'),q(2,'Leciona matérias do técnico de DS?','disciplina'),q(3,'Leciona Matemática?','disciplina')]
    linhas=[('sim','sim','nao'),('sim','nao','sim'),('sim','sim','sim'),('sim','nao','nao')]
    assert escolher(qs,linhas,{1:'sim'})[0]['id']==2


def test_modalidades_independentes():
    qs=[q(1,'As matérias lecionadas são do técnico?','modalidade'),q(2,'As matérias lecionadas são do regular?','modalidade')]
    linhas=[('sim','sim'),('sim','nao'),('nao','sim'),('nao','nao')]
    assert escolher(qs,linhas,{1:'sim'})[0]['id']==2


def test_base_v8_integridade_e_primeira_pergunta():
    caminho=Path(__file__).resolve().parents[1]/'data'/'yvonator.sqlite3'
    origem=sqlite3.connect(f'{caminho.as_uri()}?mode=ro',uri=True)
    c=sqlite3.connect(':memory:');origem.backup(c);origem.close();c.row_factory=sqlite3.Row
    try:
        assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        num_personagens=c.execute('SELECT COUNT(*) FROM personagem').fetchone()[0]
        num_vinculos=c.execute('SELECT COUNT(*) FROM personagem_pergunta').fetchone()[0]
        assert num_personagens>0 and num_vinculos>0
        # Simula uma migração em uma base com as perguntas antigas e uma partida pendente.
        c.execute('UPDATE pergunta SET status=1 WHERE id=1')
        c.execute("UPDATE pergunta SET enunciado='Seu personagem atua no ensino técnico?' WHERE id=27")
        c.execute("INSERT INTO partida(id) VALUES('legada')")
        c.execute("INSERT INTO partida_pergunta VALUES('legada',1,1)")
        assert atualizar(c)==2
        assert atualizar(c)==0
        assert c.execute('SELECT status FROM pergunta WHERE id=1').fetchone()[0]==0
        assert c.execute('SELECT enunciado FROM pergunta WHERE id=27').fetchone()[0]=='As matérias lecionadas são do técnico?'
        assert jogo.estado(c,'legada')['pergunta']['categoria']=='genero'
        s=jogo.novo(c)
        assert s['pergunta']['categoria']=='genero'
        assert not pergunta_professor(s['pergunta'])
        assert c.execute('SELECT COUNT(*) FROM personagem_pergunta').fetchone()[0]==num_vinculos
        assert c.execute('SELECT COUNT(*) FROM personagem').fetchone()[0]==num_personagens
    finally:
        c.close()
