"""Importa a base JSON local; nunca inserir a pesquisa no Git público."""
import argparse,json
from pathlib import Path
from .database import db,init_db

def importar(path):
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    init_db()
    with db() as c:
        if c.execute('SELECT COUNT(*) FROM partida').fetchone()[0]:
            raise ValueError('Use um banco novo para importar outra versão; partidas existentes seriam afetadas.')
        for table in ('personagem_pergunta','pergunta','personagem'):
            c.execute(f'DELETE FROM {table}')
        for q in data['perguntas']:
            c.execute('INSERT INTO pergunta(id,enunciado,categoria,prioridade) VALUES(?,?,?,?)',(q['id'],q['enunciado'],q['categoria'],q.get('prioridade',1)))
        for p in data['personagens']:
            c.execute('INSERT INTO personagem VALUES(?,?,?,?,?)',(p['id'],p['nome'],p.get('materia'),p.get('categoria'),p.get('foto')))
            for q,a in p['respostas'].items():
                if a is not None:
                    c.execute('INSERT INTO personagem_pergunta VALUES(?,?,?)',(p['id'],int(q),a))
        from .atualizacao_v8 import atualizar
        atualizar(c)
    return len(data['personagens']),len(data['perguntas'])

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('arquivo'); a=parser.parse_args()
    p,q=importar(a.arquivo); print(f'Importados {p} personagens e {q} perguntas.')
