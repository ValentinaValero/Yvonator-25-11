"""Importa somente a pergunta de gênero e seus vínculos; preserva partidas."""
import argparse
import json
from pathlib import Path
from .database import db, init_db

ENUNCIADO = 'Seu personagem é do gênero feminino?'
PRIORIDADE = 1.5


def adicionar(caminho):
    dados = json.loads(Path(caminho).read_text(encoding='utf-8'))
    registros = dados['personagens']
    if not isinstance(registros, list) or not registros:
        raise ValueError('Lista de personagens vazia ou inválida.')
    mapa = {}
    for item in registros:
        nome, genero = item['nome'], item['genero']
        if not isinstance(nome, str) or not nome.strip() or nome in mapa or genero not in ('F', 'M', None):
            raise ValueError('Registro duplicado ou gênero inválido.')
        mapa[nome] = {'F':'sim', 'M':'nao', None:None}[genero]
    init_db()
    with db() as c:
        personagens = c.execute('SELECT id,nome FROM personagem').fetchall()
        nomes = [p['nome'] for p in personagens]
        if not nomes or len(nomes) != len(set(nomes)) or set(nomes) != set(mapa):
            raise ValueError('Os personagens do arquivo não correspondem ao banco. Revise a base antes de importar.')
        perguntas = c.execute("SELECT id,enunciado,prioridade,status FROM pergunta WHERE categoria IN ('genero','gênero')").fetchall()
        if len(perguntas)>1 or (perguntas and (perguntas[0]['enunciado'] != ENUNCIADO or perguntas[0]['prioridade'] != PRIORIDADE or not perguntas[0]['status'])):
            raise ValueError('Já existe uma pergunta de gênero diferente ou inativa. Revise antes de continuar.')
        nova = int(not perguntas)
        qid = perguntas[0]['id'] if perguntas else c.execute("INSERT INTO pergunta(enunciado,categoria,prioridade) VALUES(?,'genero',?)",(ENUNCIADO,PRIORIDADE)).lastrowid
        vinculos=0
        for p in personagens:
            a=mapa[p['nome']]
            anterior=c.execute('SELECT resposta FROM personagem_pergunta WHERE id_personagem=? AND id_pergunta=?',(p['id'],qid)).fetchone()
            if anterior:
                if anterior[0]!=a:
                    raise ValueError('Vínculo existente divergente. Nenhuma alteração gravada.')
            elif a is not None:
                c.execute('INSERT INTO personagem_pergunta VALUES(?,?,?)',(p['id'],qid,a))
                vinculos+=1
    return nova,vinculos


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('arquivo')
    args=parser.parse_args()
    nova,vinculos=adicionar(args.arquivo)
    print(f'Perguntas adicionadas: {nova}; novos vínculos: {vinculos}. Partidas preservadas.')
