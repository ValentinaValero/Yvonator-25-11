# Yvonator 6 — Confirmação diferencial final e idade abaixo de 30

Atualização complementar à versão 5. Não requer novos JSONs nem alterações no CSS, HTML ou JavaScript.

1. Pare o Uvicorn com Ctrl+C e faça backup da pasta do projeto e do SQLite.
2. Extraia o ZIP na raiz do Yvonator, substituindo os arquivos correspondentes.
3. Execute `.\.venv\Scripts\python.exe -m backend.atualizar_idade`.
4. Inicie `.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8001`.
5. Abra http://127.0.0.1:8001/ e inicie uma nova partida.

Quando o algoritmo decide sugerir um personagem que possui diferencial ativa, reserva a pergunta antes de mostrar o palpite. Sim ou Não sei nessa etapa leva diretamente ao palpite do líder vinculado; Não reinicia a investigação. Não sei não altera o peso. Se uma diferencial já foi feita e houve investigação posterior, o personagem só pode ser sugerido após outra diferencial não utilizada. Se não houver outra, o jogo pode terminar sem palpite para preservar a regra e evitar repetição. Personagens sem diferencial ativa continuam com o fluxo normal. A base complementar original cobre 13 de 41 perfis; não foram criadas perguntas diferenciais novas.

A migração une as faixas antigas menor de 20 e 20–29 em menos de 30, mantendo seus registros e desativando as perguntas antigas. As demais faixas permanecem iguais. Respostas desconhecidas permanecem desconhecidas. O comando pode ser repetido sem duplicar vínculos e depende dos dados de perfil da versão 5 já importados. A migração de idade é a única alteração de dados; mantém partidas e histórico.

Testes: `.\.venv\Scripts\python.exe -m pytest -q` (35 aprovados no ambiente de desenvolvimento). Simulações com base original e complementos: 41 de 41 primeiros palpites corretos; 13 de 13 personagens com diferencial ativa tiveram a diferencial imediatamente antes do palpite; 7 registros abaixo de 30. São respostas da própria base, não resultados em produção. Não foi testado o navegador ou o ambiente Windows local do usuário. Nenhuma alteração no GitHub.
