import os, sqlite3
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCHEMA = '''
CREATE TABLE IF NOT EXISTS personagem(id INTEGER PRIMARY KEY, nome TEXT NOT NULL, materia TEXT, categoria TEXT, foto TEXT);
CREATE TABLE IF NOT EXISTS pergunta(id INTEGER PRIMARY KEY, enunciado TEXT NOT NULL, categoria TEXT NOT NULL, prioridade REAL NOT NULL CHECK(prioridade>0), status INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS personagem_pergunta(id_personagem INTEGER REFERENCES personagem(id), id_pergunta INTEGER REFERENCES pergunta(id), resposta TEXT NOT NULL CHECK(resposta IN ('sim','nao')), PRIMARY KEY(id_personagem,id_pergunta));
CREATE TABLE IF NOT EXISTS partida(id TEXT PRIMARY KEY, data_inicio TEXT DEFAULT CURRENT_TIMESTAMP, data_fim TEXT, status TEXT DEFAULT 'em_andamento' CHECK(status IN ('em_andamento','palpite','confirmada','sem_resultado')), quantidade_perguntas INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS partida_pergunta(id_partida TEXT REFERENCES partida(id), id_pergunta INTEGER REFERENCES pergunta(id), ordem INTEGER NOT NULL, PRIMARY KEY(id_partida,id_pergunta), UNIQUE(id_partida,ordem));
CREATE TABLE IF NOT EXISTS resposta(id INTEGER PRIMARY KEY, id_partida TEXT NOT NULL, id_pergunta INTEGER NOT NULL, resposta TEXT NOT NULL CHECK(resposta IN ('sim','nao','naoSei')), data_resposta TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE(id_partida,id_pergunta), FOREIGN KEY(id_partida,id_pergunta) REFERENCES partida_pergunta(id_partida,id_pergunta));
CREATE TABLE IF NOT EXISTS resultado(id INTEGER PRIMARY KEY, id_partida TEXT REFERENCES partida(id), id_personagem INTEGER REFERENCES personagem(id), compatibilidade REAL NOT NULL, confirmado INTEGER CHECK(confirmado IN (0,1)), UNIQUE(id_partida,id_personagem));
CREATE UNIQUE INDEX IF NOT EXISTS palpite_pendente ON resultado(id_partida) WHERE confirmado IS NULL;
CREATE TABLE IF NOT EXISTS historico(id INTEGER PRIMARY KEY, id_partida TEXT REFERENCES partida(id), descricao TEXT NOT NULL, data_evento TEXT DEFAULT CURRENT_TIMESTAMP);
'''

@contextmanager
def db():
    path = Path(os.getenv('YVONATOR_DB', str(ROOT/'data'/'yvonator.sqlite3')))
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    try:
        con.execute('BEGIN IMMEDIATE')
        yield con
        con.commit()
    except BaseException:
        con.rollback()
        raise
    finally:
        con.close()

def init_db():
    with db() as con:
        con.executescript(SCHEMA)
