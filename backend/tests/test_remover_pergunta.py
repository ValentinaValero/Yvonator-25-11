"""Garante que uma pergunta aposentada não comprometa partidas em andamento."""
from backend.database import db, init_db
from backend.remover_pergunta import remover
from backend.services import jogo


def preparar(monkeypatch, tmp_path):
    monkeypatch.setenv('YVONATOR_DB', str(tmp_path/'teste.sqlite3'))
    init_db()
    with db() as c:
        c.executemany('INSERT INTO personagem(id,nome) VALUES(?,?)', [(1,'A'),(2,'B')])
        c.executemany('INSERT INTO pergunta(id,enunciado,categoria,prioridade) VALUES(?,?,?,1)', [
            (1,'Pergunta inicial?','aparência'),
            (2,'Pergunta a retirar?','perfil'),
            (3,'Pergunta final?','aparência')])
        c.executemany('INSERT INTO personagem_pergunta VALUES(?,?,?)', [
            (1,1,'sim'),(2,1,'nao'),(1,2,'sim'),(2,2,'nao'),(1,3,'sim'),(2,3,'nao')])
        c.execute("INSERT INTO partida(id,quantidade_perguntas) VALUES('respondida',3)")
        c.executemany('INSERT INTO partida_pergunta VALUES(?,?,?)',
                      [('respondida',1,1),('respondida',2,2),('respondida',3,3)])
        c.executemany('INSERT INTO resposta(id_partida,id_pergunta,resposta) VALUES(?,?,?)',
                      [('respondida',1,'sim'),('respondida',2,'sim'),('respondida',3,'sim')])
        c.execute("INSERT INTO partida(id,quantidade_perguntas) VALUES('pendente',1)")
        c.executemany('INSERT INTO partida_pergunta VALUES(?,?,?)', [('pendente',1,1),('pendente',2,2)])
        c.execute("INSERT INTO resposta(id_partida,id_pergunta,resposta) VALUES('pendente',1,'sim')")
        c.executemany('INSERT INTO historico(id_partida,descricao) VALUES(?,?)', [
            ('respondida','Pergunta 2 apresentada'),('respondida','Pergunta 2 respondida'),
            ('respondida','Pergunta 1 respondida')])


def test_remocao_transacional_preserva_jogo_e_ordens(monkeypatch, tmp_path):
    preparar(monkeypatch, tmp_path)
    assert remover('Pergunta a retirar?') == (1,2)
    assert remover('Pergunta a retirar?') == (0,0)
    with db() as c:
        assert c.execute('SELECT COUNT(*) FROM pergunta').fetchone()[0] == 2
        assert c.execute('SELECT COUNT(*) FROM personagem_pergunta').fetchone()[0] == 4
        assert c.execute('SELECT COUNT(*) FROM resposta').fetchone()[0] == 3
        assert c.execute('SELECT quantidade_perguntas FROM partida WHERE id=?',('respondida',)).fetchone()[0] == 2
        assert list(map(tuple,c.execute("SELECT id_pergunta,ordem FROM partida_pergunta WHERE id_partida='respondida' ORDER BY ordem"))) == [(1,1),(3,2)]
        assert c.execute('SELECT descricao FROM historico').fetchall()[0][0] == 'Pergunta 1 respondida'
        assert not c.execute('PRAGMA foreign_key_check').fetchall()
        assert c.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        # A pergunta pendente removida é substituída sem travar a sessão.
        s = jogo.estado(c,'pendente')
        assert s['status'] in ('em_andamento','palpite','sem_resultado')
        assert not s['pergunta'] or s['pergunta']['id'] != 2
        if s['pergunta']:
            assert s['pergunta']['ordem'] == 2
