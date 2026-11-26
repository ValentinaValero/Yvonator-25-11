"""Atualiza somente enunciados/status; conserva IDs, vínculos e histórico."""
from .algorithms.compatibilidade import pergunta_professor, grupo


def novo_enunciado(q):
    t = q['enunciado']
    especiais = {
        'As matérias lecionadas são técnicas?': 'As matérias lecionadas são do técnico?',
        'Seu personagem atua na pedagogia?': 'Seu personagem faz parte da equipe pedagógica?',
        'Seu personagem atua como PAE?': 'Seu personagem trabalha como PAE?',
        'Seu personagem atua em Curso ADM?': 'Leciona matérias do técnico de ADM?',
        'Seu personagem atua em Curso DS?': 'Leciona matérias do técnico de DS?',
        'Seu personagem atua em Educação especial?': 'Seu personagem trabalha com educação especial?',
        'Seu personagem atua no ensino técnico?': 'As matérias lecionadas são do técnico?',
        'Seu personagem atua no ensino regular?': 'As matérias lecionadas são do regular?',
        'Seu personagem atua no ensino médio?': 'Seu personagem dá aulas no ensino médio?',
        'Seu personagem atua no ensino fundamental?': 'Seu personagem dá aulas no ensino fundamental?',
    }
    if t in especiais and grupo(q) != 'diferencial':
        return especiais[t]
    if grupo(q) == 'disciplina' and t.startswith('Seu personagem atua em '):
        materia = t.removeprefix('Seu personagem atua em ')
        materia = {'robótica?': 'Robótica?', 'Cidadania e civismo?': 'Cidadania e Civismo?'}.get(materia, materia)
        # Mantém o nome original da disciplina, inclusive abreviações existentes.
        return 'Seu personagem leciona ' + materia
    return t


def atualizar(c):
    """Idempotente, inclusive para bases importadas posteriormente."""
    qs = [dict(r) for r in c.execute('SELECT * FROM pergunta')]
    alteradas = 0
    retiradas = []
    for q in qs:
        texto = novo_enunciado(q)
        if texto != q['enunciado']:
            c.execute('UPDATE pergunta SET enunciado=? WHERE id=?', (texto, q['id']))
            alteradas += 1
        if pergunta_professor(q):
            retiradas.append(q['id'])
            if q['status']:
                c.execute('UPDATE pergunta SET status=0 WHERE id=?', (q['id'],))
                alteradas += 1
    # Substitui apenas perguntas antigas pendentes (sem resposta), sem apagar
    # respostas ou partidas. As posições e a contagem permanecem coerentes.
    from .services.jogo import avancar, evento
    for qid in retiradas:
        partidas = [r[0] for r in c.execute('''SELECT pp.id_partida FROM partida_pergunta pp
            JOIN partida p ON p.id=pp.id_partida
            LEFT JOIN resposta r ON r.id_partida=pp.id_partida AND r.id_pergunta=pp.id_pergunta
            WHERE pp.id_pergunta=? AND p.status='em_andamento' AND r.id IS NULL''', (qid,))]
        for pid in partidas:
            c.execute('DELETE FROM partida_pergunta WHERE id_partida=? AND id_pergunta=?', (pid,qid))
            evento(c,pid,'Pergunta sobre ser professor substituída na atualização V8')
            avancar(c,pid)
    return alteradas


if __name__ == '__main__':
    from .database import db
    with db() as c:
        print(f'Alterações V8: {atualizar(c)}')
