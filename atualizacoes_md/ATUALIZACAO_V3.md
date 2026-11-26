# Yvonator 3.0 — Pergunta diferencial final

Compatível com a instalação anterior (inclui as melhorias do motor v2). Nenhuma alteração em HTML, CSS ou JavaScript, nem no esquema SQLite. As perguntas gerais continuam sendo escolhidas dinamicamente; ao atingir os critérios de palpite do motor, o líder recebe uma confirmação específica se houver uma pergunta associada e ativa ainda não usada para aquele candidato. Se não houver, o fluxo anterior continua. Não foi criado um mecanismo separado para desempatar perfis que não atingem os critérios de palpite.

- Sim: aumenta a pontuação do candidato (peso configurado em 2, fator 3²), e o jogo pode apresentar o palpite se os critérios permanecerem satisfeitos.
- Não: reduz a pontuação (divide por 9), não exclui definitivamente e prioriza nova pergunta geral se houver. O mesmo perfil só poderá ser sugerido após nova resposta geral favorável e se o critério de palpite for atingido. Sem informação suficiente, o jogo admite que não sabe ou investiga outro candidato.
- Não sei: neutro e segue com o palpite se os critérios já estiverem satisfeitos.
- Ausência de informação sobre outros personagens: não é um Não. Só os perfis expressamente vinculados recebem expectativa Sim. Cada pergunta é usada no máximo uma vez por partida, e só uma confirmação é escolhida por candidato. A pergunta utiliza os mesmos botões da interface.

## Instalação (Windows / PowerShell)

1. Pare o servidor com Ctrl+C. Faça backup da pasta Yvonator (em especial backend/data/yvonator.sqlite3).
2. Extraia o ZIP na raiz do projeto, onde estão backend e Yvonator_pasta. Aceite substituir os arquivos de código. Não crie uma segunda pasta backend.
3. Baixe separadamente yvonator_diferenciais_locais.json. Revise as 13 perguntas e respectivos vínculos, valide com os professores e remova as entradas que não estiverem autorizadas antes de usá-las. Coloque o arquivo em backend/data/.
4. No terminal aberto na raiz, execute:

```powershell
.\.venv\Scripts\python.exe -m backend.adicionar_diferenciais backend/data/yvonator_diferenciais_locais.json
.\.venv\Scripts\python.exe -m pytest -q backend/tests
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

A primeira execução deve informar 13 novas perguntas e 13 novos vínculos se o JSON estiver intacto. Reexecutar o mesmo comando não duplica perguntas ou vínculos. O script adiciona dados em transação e preserva as partidas e os dados existentes. Não remova nem reimporte o banco original. Se o arquivo for editado depois da importação, o script só acrescenta entradas; não apaga ou desativa perguntas antigas.

Acesse http://127.0.0.1:8000/ e comece uma nova partida. O arquivo de dados e o SQLite não devem ser enviados ao GitHub público; ficam na pasta ignorada backend/data/. A API serve as perguntas durante o jogo, portanto só disponibilize a versão pública após autorização e revisão dos dados.

## Validação e limites

19 testes automatizados aprovados. Em 41 simulações com as respostas conhecidas da pesquisa e banco temporário, 39 primeiros palpites corretos, 2 sem palpite, 0 errados; 13 diferenciais exibidas, todas imediatamente antes do palpite correto, mediana de 8 perguntas. Não representa precisão com jogadores reais; não houve teste visual em navegador. Foram selecionadas 13 reformulações da coluna PERGUNTA DIFERENCIAL, priorizando práticas de aula, funções e interesses não sensíveis. Informações pessoais, descrições depreciativas ou ambíguas e outras entradas não revisadas ficaram de fora. Os demais personagens mantêm o fluxo padrão. Nenhuma alteração foi enviada ao GitHub.
