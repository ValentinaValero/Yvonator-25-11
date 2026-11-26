"""Acrescenta perguntas de confirmação ao banco existente sem apagar partidas."""
import argparse
import json
from pathlib import Path
from .database import db, init_db


def adicionar(caminho):
    dados = json.loads(Path(caminho).read_text(encoding='utf-8'))
    perguntas = dados['perguntas']
    if not isinstance(perguntas, list) or not perguntas:
        raise ValueError('Lista de perguntas diferenciais vazia ou inválida.')
    init_db()
    novas = vinculos = 0
    with db() as c:
        if not c.execute('SELECT 1 FROM personagem LIMIT 1').fetchone():
            raise ValueError('Importe a base original antes das diferenciais.')
        for item in perguntas:
            enunciado = item['enunciado'].strip()
            nomes = item['personagens']
            if not enunciado or not isinstance(nomes, list) or not nomes or not all(isinstance(n,str) and n.strip() for n in nomes):
                raise ValueError('Pergunta diferencial ou personagens inválidos.')
            ids = []
            for nome in nomes:
                encontrados = c.execute('SELECT id FROM personagem WHERE nome=?',(nome,)).fetchall()
                if len(encontrados) != 1:
                    raise ValueError(f'Personagem ausente ou ambíguo: {nome!r}. Nenhuma alteração foi gravada.')
                ids.append(encontrados[0][0])
            existentes = c.execute("SELECT id FROM pergunta WHERE enunciado=? AND categoria='diferencial'",(enunciado,)).fetchall()
            if len(existentes)>1:
                raise ValueError('Pergunta diferencial duplicada no banco.')
            if existentes:
                qid = existentes[0][0]
            else:
                qid = c.execute("INSERT INTO pergunta(enunciado,categoria,prioridade) VALUES(?,'diferencial',2)",(enunciado,)).lastrowid
                novas += 1
            for pid in set(ids):
                anterior = c.execute('SELECT resposta FROM personagem_pergunta WHERE id_personagem=? AND id_pergunta=?',(pid,qid)).fetchone()
                if anterior and anterior[0] != 'sim':
                    raise ValueError('Vínculo conflitante; revise a base manualmente.')
                if not anterior:
                    c.execute('INSERT INTO personagem_pergunta VALUES(?,?,?)',(pid,qid,'sim'))
                    vinculos += 1
    return novas,vinculos


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('arquivo')
    args=parser.parse_args()
    novas,vinculos=adicionar(args.arquivo)
    print(f'Diferenciais adicionadas: {novas}; novos vínculos: {vinculos}. Partidas preservadas.')
