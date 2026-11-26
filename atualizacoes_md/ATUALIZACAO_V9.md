# Yvonator V9 — árvore de decisão adaptativa

## O que mudou

A seleção passa a considerar somente os personagens do ramo ativo, isto é, os perfis que não contradizem as respostas conhecidas. O ranking probabilístico global é mantido internamente para recuperação, mas não determina as próximas perguntas de um ramo consistente.

- **Sim / Não:** eliminam do ramo os personagens com resposta cadastrada oposta.
- **Não sei:** não elimina ninguém e diminui a prioridade da categoria após sucessivos desconhecimentos.
- **Dado ausente:** não é interpretado como Não; o perfil permanece possível.
- **Perguntas:** devem dividir efetivamente os candidatos do ramo em Sim e Não. Disciplinas sem sobreposição comprovada deixam de ser perguntadas. Professores que lecionam mais de uma disciplina continuam contemplados.
- **Confirmação:** quando sobra um perfil com pouca evidência, o jogo pode solicitar uma característica independente antes do palpite. As perguntas diferenciais existentes permanecem como confirmação final, conforme a lógica anterior.
- **Recuperação:** se não restar nenhum perfil sem contradições, o jogo reabre apenas os perfis com menor custo de contradição. Uma contradição com disciplina respondida Sim ou diferencial custa 3, as demais custam 1. Personagens já rejeitados não retornam. Não é necessário cadastrar manualmente uma árvore nova quando a base for atualizada.
- A compatibilidade utilizada para decidir o palpite é relativa ao ramo ativo, não uma probabilidade de acerto garantido.

## Instalação (recomendada: pacote somente código)

1. Pare o servidor com Ctrl+C. Faça uma cópia do projeto.
2. Extraia o ZIP de atualização na raiz atual, onde ficam `backend` e `Yvonator_pasta`, e aceite substituir os arquivos indicados.
3. Ative seu ambiente virtual habitual, se necessário. Na raiz, execute:

   ```powershell
   python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
   ```

4. Abra http://localhost:8000 e inicie uma nova partida.

Não é necessária migração ou reimportação do banco. As fotos, características, histórico de partidas e arquivos de interface não foram modificados. O pacote completo é uma cópia atualizada do ZIP recebido, sem `.git`, `.venv` e caches gerados; se já alterou o projeto depois do envio, use o pacote somente código para preservar essas alterações.

## Arquivos

- `backend/algorithms/compatibilidade.py`: poda dos ramos, seleção local e recuperação.
- `backend/services/jogo.py`: palpite e confirmação restritos ao ramo ativo.
- `backend/tests/test_arvore.py`: regressões e simulação com a base real.

## Validação

`python -m pytest -q backend/tests`: 49 testes aprovados e 1 suíte legada ignorada. A simulação automática com os 41 personagens do banco recebido identificou 41/41 no primeiro palpite, usando precisamente os dados cadastrados (5–8 perguntas, mediana 6). Também foram verificados o caso Educação Física, disciplinas sobrepostas, dados ausentes, Não sei e recuperação. Não corresponde a um teste humano com respostas imprecisas.

O teste JavaScript anterior `test_delay.mjs` falha também no ZIP original porque seu DOM simulado não implementa `closest`, usado pela interface atual. Não foi alterado nesta atualização; não houve teste visual no navegador.
