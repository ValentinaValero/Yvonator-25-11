# Yvonator 4.0 — gênero e redução de redundância

Requer a instalação anterior (v3) com a base original e, para manter as confirmações finais, a importação das diferenciais da v3.

1. Pare o servidor (Ctrl+C) e faça backup da pasta e do banco SQLite.
2. Extraia os arquivos do ZIP na raiz do Yvonator, mesclando a pasta backend e substituindo os arquivos indicados.
3. Revise o arquivo separado `yvonator_genero_local.json` e confirme que os dados podem ser usados no jogo com autorização dos personagens. Copie-o para `backend/data/`. Não publique o JSON nem o banco SQLite em repositório público.
4. No terminal PowerShell, na raiz do projeto, rode:

```powershell
.\.venv\Scripts\python.exe -m backend.adicionar_genero backend/data/yvonator_genero_local.json
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

Abra http://127.0.0.1:8000/ e inicie uma nova partida. Não é necessário chamar `integrar.py` nem reimportar a base original. O importador de gênero é aditivo, transacional e idempotente. Em caso de nomes diferentes ou registros incompatíveis, ele interrompe a importação sem gravar vínculos parciais.

## Comportamento

- Primeira pergunta: Seu personagem é professor(a)?
- Segunda pergunta: Seu personagem é do gênero feminino?
- Sim/Não prioriza os grupos F/M registrados na planilha; Não sei não altera as pontuações. Nenhum gênero é inferido por nome, foto ou aparência. A pergunta é binária porque a base atual contém exclusivamente F e M; uma categoria não registrada não deve ser convertida automaticamente em M.
- O peso da evidência de gênero é 1,5 vezes o peso comum em escala logarítmica. Candidatos divergentes ficam com peso menor, sem exclusão definitiva. O foco da seleção de perguntas considera o gênero em conjunto com a função e as disciplinas afirmadas, podendo reabrir outros caminhos quando necessário.
- A seleção prioriza perguntas que dividem os candidatos consistentes com todas as respostas conhecidas. Uma pergunta previsível pela coorte registrada (por função, gênero ou pelo mesmo domínio da pergunta anterior, como comprimento do cabelo) é adiada; dados desconhecidos não viram respostas negativas. Se o ramo fica inconsistente ou pouco provável, o sistema pode reabrir perguntas para recuperar erros. A regra não presume relações universais entre gênero e aparência.
- Perguntas diferenciais continuam reservadas para a confirmação do candidato mais provável.

## Testes

26 testes automatizados passaram. Em 41 simulações com a base original, as 13 diferenciais e a nova pergunta, a segunda pergunta foi de gênero em todas as partidas. Houve 39 primeiros palpites corretos e 2 partidas sem palpite, zero primeiros palpites errados e mediana de 8 perguntas (média 8,83). Nenhuma das 22 partidas com resposta afirmativa à pergunta de gênero apresentou a pergunta sobre barba. As 13 confirmações diferenciais foram a última pergunta antes do palpite. Simulações com respostas da pesquisa não substituem testes reais. Nenhuma alteração no front-end, sem teste visual no navegador.
