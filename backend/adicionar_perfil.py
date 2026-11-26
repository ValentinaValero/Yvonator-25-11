"""Acrescenta dados de perfil autorizados, sem substituir a base ou partidas."""
import argparse
import json
from pathlib import Path
from .database import db, init_db

# Faixas mutuamente exclusivas; a idade é a informada na pesquisa.
FAIXAS = {
    'menor20': 'Seu personagem tem menos de 20 anos?',
    '20-29': 'Seu personagem tem entre 20 e 29 anos?',
    '30-49': 'Seu personagem tem entre 30 e 49 anos?',
    '50-59': 'Seu personagem tem entre 50 e 59 anos?',
    '60-69': 'Seu personagem tem entre 60 e 69 anos?',
    '70-79': 'Seu personagem tem entre 70 e 79 anos?',
    '80+': 'Seu personagem tem 80 anos ou mais?',
}
CAMPOS = {
    'filhos': 'Seu personagem tem filhos?',
    'viajou_para_fora': 'Seu personagem já viajou para fora?',
    'nasceu_em_outro_estado_ou_cidade': 'Seu personagem nasceu em outra cidade ou estado?',
}
PRIORIDADE = 1.0


def adicionar(caminho):
    dados = json.loads(Path(caminho).read_text(encoding='utf-8'))
    registros = dados['personagens']
    if not isinstance(registros, list) or not registros:
        raise ValueError('Lista de personagens vazia ou inválida.')
    mapa = {}
    for item in registros:
        nome = item['nome']
        if not isinstance(nome, str) or not nome.strip() or nome in mapa:
            raise ValueError('Nome inválido ou duplicado.')
        faixa = item['faixa_idade']
        if faixa is not None and faixa not in FAIXAS:
            raise ValueError('Faixa de idade inválida.')
        for campo in CAMPOS:
            if item[campo] not in ('sim', 'nao', None):
                raise ValueError('Resposta de perfil inválida.')
        mapa[nome] = item

    init_db()
    novas = vinculos = 0
    with db() as c:
        pessoas = c.execute('SELECT id,nome FROM personagem').fetchall()
        nomes = [p['nome'] for p in pessoas]
        if len(nomes) != len(set(nomes)) or set(nomes) != set(mapa):
            raise ValueError('Os personagens não correspondem ao banco. Nenhuma alteração gravada.')
        definicoes = [('idade', faixa, texto) for faixa, texto in FAIXAS.items()]
        definicoes += [('perfil', campo, texto) for campo, texto in CAMPOS.items()]
        for categoria, chave, texto in definicoes:
            existentes = c.execute('SELECT id,categoria,prioridade,status FROM pergunta WHERE enunciado=?', (texto,)).fetchall()
            if len(existentes) > 1:
                raise ValueError('Pergunta duplicada no banco.')
            if existentes:
                q = existentes[0]
                legado = categoria == 'idade' and chave in ('menor20', '20-29') and c.execute("SELECT 1 FROM pergunta WHERE enunciado=? AND categoria='idade' AND status=1", ('Seu personagem tem menos de 30 anos?',)).fetchone()
                if q['categoria'] != categoria or q['prioridade'] != PRIORIDADE or (not q['status'] and not legado):
                    raise ValueError('Pergunta existente com configuração divergente.')
                qid = q['id']
            else:
                qid = c.execute('INSERT INTO pergunta(enunciado,categoria,prioridade) VALUES(?,?,?)',(texto,categoria,PRIORIDADE)).lastrowid
                novas += 1
            for p in pessoas:
                item = mapa[p['nome']]
                if categoria == 'idade':
                    faixa = item['faixa_idade']
                    resposta = None if faixa is None else ('sim' if faixa == chave else 'nao')
                else:
                    resposta = item[chave]
                anterior = c.execute('SELECT resposta FROM personagem_pergunta WHERE id_personagem=? AND id_pergunta=?',(p['id'],qid)).fetchone()
                if anterior:
                    if anterior[0] != resposta:
                        raise ValueError('Vínculo existente divergente. Nenhuma alteração gravada.')
                elif resposta is not None:
                    c.execute('INSERT INTO personagem_pergunta VALUES(?,?,?)',(p['id'],qid,resposta))
                    vinculos += 1
    return novas, vinculos


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('arquivo')
    args = parser.parse_args()
    novas, vinculos = adicionar(args.arquivo)
    print(f'Perguntas adicionadas: {novas}; novos vínculos: {vinculos}. Partidas preservadas.')
