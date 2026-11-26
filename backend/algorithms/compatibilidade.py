"""Classificação tolerante a erros; seleção contextual de perguntas."""
from math import exp, log
from collections import Counter
import unicodedata

FATOR = 3.0
MIN_EVIDENCIAS = 4
LIMIAR = .80
MARGEM = .25


def normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto.casefold())
                   if unicodedata.category(c) != 'Mn')


def grupo(q):
    return normalizar(q['categoria'])


def pergunta_professor(q):
    t = normalizar(q['enunciado'])
    return grupo(q) == 'funcao' and t.startswith('seu personagem e professor')


def pergunta_genero(q):
    return grupo(q) == 'genero'


def classificar(personagens, matriz, respostas, prioridades, excluidos, perguntas=None):
    grupos = {q['id']: grupo(q) for q in (perguntas or [])}
    items = []
    for p in personagens:
        if p['id'] in excluidos:
            continue
        score = 0.0
        acertos = erros = 0
        for q, a in respostas.items():
            esperado = matriz.get((p['id'], q))
            if a == 'naoSei' or esperado is None:
                continue
            # O sim numa disciplina tem mais informação que um não isolado.
            g = grupos.get(q)
            multiplicador = 1.
            if g == 'disciplina':
                multiplicador = 1. if a == 'sim' else .9
            delta = log(FATOR) * prioridades.get(q, 1) * multiplicador
            if a == esperado:
                score += delta
                acertos += 1
            else:
                score -= delta
                erros += 1
        items.append(dict(personagem=p, score=score, acertos=acertos, erros=erros))
    if not items:
        return []
    maximo = max(i['score'] for i in items)
    total = sum(exp(i['score']-maximo) for i in items)
    for i in items:
        i['peso'] = exp(i['score']-maximo)/total
    return sorted(items,key=lambda i:(-i['peso'],i['personagem']['id']))


def ramo_ativo(ranking, perguntas, matriz, respostas):
    """Poda dinâmica: um ramo contém somente perfis sem contradições conhecidas.

    Se ele esvaziar (erro de resposta, negativa diferencial, palpite rejeitado),
    reabre apenas os perfis com o menor custo de contradição. Ausência de dado
    nunca vira um Não. O ranking global segue disponível para recuperação.
    """
    if not ranking:
        return [], False
    por_id = {q['id']: q for q in perguntas}
    regras = {qid: a for qid, a in respostas.items()
              if a in ('sim', 'nao') and qid in por_id}

    def custo(item):
        pid = item['personagem']['id']
        total = 0
        for qid, a in regras.items():
            conhecido = matriz.get((pid, qid))
            if conhecido is None or conhecido == a:
                continue
            g = grupo(por_id[qid])
            # Preserva a área confirmada antes de relaxar atributos isolados.
            total += 3 if (g == 'disciplina' and a == 'sim') or g == 'diferencial' else 1
        return total

    custos = [(custo(i), i) for i in ranking]
    minimo = min(c for c, _ in custos)
    ativos = [dict(i) for c, i in custos if c == minimo]
    # Normaliza dentro do ramo sem alterar o ranking global.
    maximo = max(i['score'] for i in ativos)
    total = sum(exp(i['score'] - maximo) for i in ativos)
    for i in ativos:
        i['peso'] = exp(i['score'] - maximo) / total
    return ativos, minimo > 0


def escolher_pergunta(ranking, perguntas, matriz, feitas, respostas=None):
    respostas = respostas or {}
    foco, recuperando = ramo_ativo(ranking, perguntas, matriz, respostas)
    if not foco:
        return None
    disponiveis = [q for q in perguntas if q['id'] not in feitas
                   and q.get('status', 1) and grupo(q) != 'diferencial' and not pergunta_professor(q)]
    genero = next((q for q in disponiveis if pergunta_genero(q)), None)
    if genero and not feitas:
        return genero
    por_id = {q['id']: q for q in perguntas}
    conhecidas = {qid:a for qid,a in respostas.items() if a in ('sim','nao') and qid in por_id}
    desconhecidas = Counter(grupo(por_id[qid]) for qid,a in respostas.items()
                            if a == 'naoSei' and qid in por_id)
    disc_sim = any(grupo(por_id[qid]) == 'disciplina' and a == 'sim'
                   for qid,a in conhecidas.items())
    papel_nao = any(pergunta_professor(por_id[qid]) and a == 'nao'
                    for qid,a in conhecidas.items())
    idade_sim = any(grupo(por_id[qid]) == 'idade' and a == 'sim'
                    for qid,a in conhecidas.items())
    tecnica = any(grupo(por_id[qid]) == 'modalidade' and a == 'sim' and
                  ('ensino tecnico' in normalizar(por_id[qid]['enunciado']) or
                   'materias lecionadas sao do tecnico' in normalizar(por_id[qid]['enunciado']))
                  for qid,a in conhecidas.items())

    def valores(qid, candidatos):
        return {matriz.get((i['personagem']['id'],qid)) for i in candidatos}

    def valor(q, candidatos):
        sim = sum(i['peso'] for i in candidatos if matriz.get((i['personagem']['id'],q['id'])) == 'sim')
        nao = sum(i['peso'] for i in candidatos if matriz.get((i['personagem']['id'],q['id'])) == 'nao')
        return 4*sim*nao*q['prioridade']

    def fator(q):
        g = grupo(q)
        f = {'aparencia':3.0, 'disciplina':1.15, 'modalidade':1.25,
             'etapa':1.1, 'idade':1.05, 'perfil':.65, 'funcao':1.0}.get(g,1.)
        if papel_nao and g == 'funcao':
            f *= 3.2  # compatibilidade com partidas antigas
        if disc_sim and g == 'disciplina':
            f *= .55
        if tecnica and g == 'disciplina' and any(x in normalizar(q['enunciado'])
                for x in ('curso ds','curso adm','tecnico de ds','tecnico de adm')):
            f *= 2.
        return f * .35 ** min(desconhecidas[g] // 2, 2)

    opcoes = []
    for q in disponiveis:
        if idade_sim and grupo(q) == 'idade' and not recuperando:
            continue
        # Somente perguntas com dois ramos comprovados na base ativa.
        # Não usa a população global para desempatar ou pontuar disciplinas.
        if {'sim','nao'}.issubset(valores(q['id'], foco)):
            opcoes.append((valor(q,foco)*fator(q),-q['id'],q))
    if opcoes:
        return max(opcoes)[2]

    # Um perfil isolado pode precisar de uma confirmação independente antes
    # do palpite. Nunca volta a listar disciplinas descartadas para confirmar.
    if len(foco) == 1 and (foco[0]['acertos'] < 2 or foco[0]['acertos'] <= foco[0]['erros']):
        for q in disponiveis:
            if grupo(q) not in ('aparencia','perfil','idade','etapa','teste'):
                continue
            if idade_sim and grupo(q) == 'idade' and not recuperando:
                continue
            v = valores(q['id'], foco)
            if v not in ({'sim'},{'nao'}) or not {'sim','nao'}.issubset(valores(q['id'],ranking)):
                continue
            opcoes.append((valor(q,ranking)*fator(q),-q['id'],q))
    return max(opcoes,default=(0,0,None))[2]


def pode_sugerir(ranking, esgotou=False):
    if not ranking:
        return False
    top = ranking[0]
    segundo = ranking[1]['peso'] if len(ranking)>1 else 0
    evidencias = top['acertos'] + top['erros']
    if top['acertos'] < 2 or top['acertos'] <= top['erros']:
        return False
    if esgotou:
        # Não transformar um empate ou vantagem insignificante em certeza.
        return top['peso'] >= .40 and top['peso']-segundo >= .10
    return evidencias >= MIN_EVIDENCIAS and top['peso'] >= LIMIAR and top['peso']-segundo >= MARGEM


def diferenciais_do_personagem(pid, perguntas, matriz):
    return [q for q in perguntas if grupo(q) == 'diferencial'
            and matriz.get((pid, q['id'])) == 'sim']


def escolher_diferencial(ranking, perguntas, matriz, feitas):
    """Confirmação final ainda não apresentada para o líder."""
    if not ranking:
        return None
    pid = ranking[0]['personagem']['id']
    candidatas = [q for q in diferenciais_do_personagem(pid, perguntas, matriz)
                  if q['id'] not in feitas]
    return max(candidatas, key=lambda q: (q['prioridade'], -q['id']), default=None)
