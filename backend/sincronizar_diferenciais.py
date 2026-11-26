"""Sincroniza as perguntas diferenciais ativas com o JSON, preservando o histórico."""
import argparse
import json
from pathlib import Path
from .database import db


def sincronizar(caminho):
    dados = json.loads(Path(caminho).read_text(encoding='utf-8-sig'))
    perguntas = dados['perguntas']
    if not isinstance(perguntas, list):
        raise ValueError('O campo perguntas deve ser uma lista.')

    with db() as c:
        if not c.execute('SELECT 1 FROM personagem LIMIT 1').fetchone():
            raise ValueError('Importe a base original primeiro.')
        desejadas = {}
        for item in perguntas:
            texto = item['enunciado'].strip()
            nomes = item['personagens']

              # Ignorar perguntas provisórias
            if 'sem pergunta diferencial' in texto.casefold() or texto.casefold().startswith('a definir'):
                continue

            if not texto or not isinstance(nomes, list) or not nomes:
                raise ValueError('Pergunta ou lista de personagens inválida.')

            ids = desejadas.setdefault(texto, set())


            for nome in nomes:
                if not isinstance(nome, str) or not nome.strip():
                    raise ValueError('Nome inválido.')
                linhas = c.execute('SELECT id FROM personagem WHERE nome=?', (nome,)).fetchall()
                if len(linhas) != 1:
                    raise ValueError(f'Personagem ausente ou ambíguo: {nome!r}')
                ids.add(linhas[0][0])

        antigas = c.execute("SELECT id,enunciado,status FROM pergunta WHERE categoria='diferencial' ORDER BY status DESC,id").fetchall()
        ativas_antes = {r['id'] for r in antigas if r['status']}
        manter = set()
        novas = 0
        for texto, ids in desejadas.items():
            vinculos = {(pid, 'sim') for pid in ids}
            qid = None
            for q in antigas:
                if q['enunciado'] != texto:
                    continue
                existentes = {tuple(r) for r in c.execute('SELECT id_personagem,resposta FROM personagem_pergunta WHERE id_pergunta=?', (q['id'],))}
                if existentes == vinculos:
                    qid = q['id']
                    break
            if qid is None:
                qid = c.execute("INSERT INTO pergunta(enunciado,categoria,prioridade,status) VALUES(?,'diferencial',2,1)", (texto,)).lastrowid
                c.executemany('INSERT INTO personagem_pergunta(id_personagem,id_pergunta,resposta) VALUES(?,?,?)', [(pid,qid,'sim') for pid in sorted(ids)])
                novas += 1
            manter.add(qid)
        c.execute("UPDATE pergunta SET status=0 WHERE categoria='diferencial'")
        c.executemany('UPDATE pergunta SET status=1 WHERE id=?', [(qid,) for qid in manter])
    return len(manter), novas, len(ativas_antes - manter)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('arquivo')
    args = parser.parse_args()
    try:
        ativas, novas, desativadas = sincronizar(args.arquivo)
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as e:
        parser.exit(1, f'Erro: {e}. Nenhuma alteração nas diferenciais foi gravada.\n')
    print(f'Diferenciais ativas: {ativas}; novas: {novas}; desativadas: {desativadas}.')
