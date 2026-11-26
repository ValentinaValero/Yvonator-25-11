"""Exclui uma pergunta descontinuada e seus vínculos, preservando as demais partidas.

Uso: python -m backend.remover_pergunta "Enunciado exato da pergunta"
A remoção é transacional e pode ser repetida sem efeitos adicionais.
"""
import argparse
from .database import db


def remover(enunciado):
    if not enunciado or not enunciado.strip():
        raise ValueError('Informe o enunciado exato da pergunta.')
    with db() as c:
        perguntas = c.execute('SELECT id FROM pergunta WHERE enunciado=?', (enunciado,)).fetchall()
        if not perguntas:
            return 0, 0
        if len(perguntas) != 1:
            raise ValueError('Existem perguntas duplicadas. Nenhuma alteração efetuada.')
        qid = perguntas[0]['id']
        partidas = [dict(r) for r in c.execute('''
            SELECT pp.id_partida, pp.ordem,
                   r.id IS NOT NULL AS respondida,
                   p.status
              FROM partida_pergunta pp
              JOIN partida p ON p.id=pp.id_partida
              LEFT JOIN resposta r ON r.id_partida=pp.id_partida
                                  AND r.id_pergunta=pp.id_pergunta
             WHERE pp.id_pergunta=?
        ''', (qid,))]
        # Remover as respostas antes da reserva e dos vínculos evita violar as FKs.
        c.execute('DELETE FROM resposta WHERE id_pergunta=?', (qid,))
        c.execute('DELETE FROM partida_pergunta WHERE id_pergunta=?', (qid,))
        c.execute('DELETE FROM personagem_pergunta WHERE id_pergunta=?', (qid,))
        c.execute('DELETE FROM pergunta WHERE id=?', (qid,))
        # Histórico guarda IDs de perguntas, não os enunciados.
        c.execute('DELETE FROM historico WHERE descricao IN (?, ?)',
                  (f'Pergunta {qid} apresentada', f'Pergunta {qid} respondida'))
        from .services.jogo import avancar
        for partida in partidas:
            pid = partida['id_partida']
            # Recompacta as posições de maneira segura para o índice UNIQUE.
            c.execute('UPDATE partida_pergunta SET ordem=-ordem WHERE id_partida=?', (pid,))
            restantes = c.execute('''SELECT id_pergunta FROM partida_pergunta
                                    WHERE id_partida=? ORDER BY ordem DESC''', (pid,)).fetchall()
            for ordem, r in enumerate(restantes, 1):
                c.execute('UPDATE partida_pergunta SET ordem=? WHERE id_partida=? AND id_pergunta=?',
                          (ordem, pid, r['id_pergunta']))
            c.execute('''UPDATE partida SET quantidade_perguntas=(
                SELECT COUNT(*) FROM resposta WHERE id_partida=?
            ) WHERE id=?''', (pid, pid))
            if partida['status'] == 'em_andamento' and not partida['respondida']:
                avancar(c, pid)
        if c.execute('PRAGMA foreign_key_check').fetchone():
            raise ValueError('Inconsistência de referência no banco de dados.')
        return 1, len(partidas)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('enunciado')
    argumentos = parser.parse_args()
    removidas, afetadas = remover(argumentos.enunciado)
    print(f'Perguntas removidas: {removidas}; partidas atualizadas: {afetadas}.')
