# Yvonator 5 — Perfil e faixa etária

Pré-requisito: instalação da versão 4, com base original, gênero e diferenciais já importados. Faça backup do projeto e do banco SQLite com o servidor desligado.

1. Extraia o ZIP na raiz do projeto (mescle as pastas). Substitua `backend/algorithms/compatibilidade.py`.
2. Coloque `yvonator_perfil_local.json` em `backend/data/`, junto aos três JSONs anteriores. Não apague nenhum deles.
3. Revise as informações e a autorização para uso no jogo. Na raiz do projeto, em PowerShell:

```powershell
.\.venv\Scripts\python.exe -m backend.adicionar_perfil backend/data/yvonator_perfil_local.json
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

4. Inicie uma nova partida em http://127.0.0.1:8000/.

A importação é complementar, transacional e repetível. Em caso de conflito ou nomes divergentes, aborta sem alterar vínculos. Não execute `backend.importar` novamente. A importação não apaga partidas anteriores. Para testar, execute ` .\.venv\Scripts\python.exe -m pytest -q backend/tests `.

## Dados e algoritmo

- 3 perguntas de perfil: filhos, viagem para fora, nascimento em outra cidade ou estado (coluna combinada na pesquisa).
- 7 faixas de idade mutuamente exclusivas: menos de 20; 20–29; 30–49; 50–59; 60–69; 70–79; 80+. Não há registros nas faixas extremas, portanto não são selecionadas com a base atual. As idades refletem a pesquisa e precisam de revisão periódica. O JSON contém apenas faixas, não idades exatas.
- A expressão “viajou para fora” foi preservada porque a coluna não especifica o destino. A coluna de nascimento não distingue cidade de estado. Uma ocorrência de “Siim” foi normalizada para “sim”. As duas linhas duplicadas concordam nos quatro campos novos; foram consolidadas como na base original.
- As novas perguntas entram na seleção dinâmica. Após um sim em uma faixa etária, outras faixas são dispensadas, salvo recuperação de um ramo incompatível. Um não exclui aquela faixa do foco consistente, sem eliminar irreversivelmente personagens. “Não sei” não pontua. Função e gênero permanecem como primeiras perguntas. Diferenciais continuam reservadas para confirmar o palpite.
- Não foi alterado front-end, esquema SQLite ou GitHub. Não publique o JSON nem o banco no repositório público.

## Validação local

30 testes automatizados aprovados (26 existentes e 4 novos). Simulação de 41 partidas em banco temporário, usando respostas da própria pesquisa: 41 primeiros palpites corretos, 0 errados, 0 sem resultado; mediana 8, média 7,78 perguntas. Controle sem as novas perguntas: 39 primeiros palpites corretos, 2 sem resultado, média 8,83. Nenhuma faixa adicional após um sim nas simulações. Importação: 10 perguntas, 410 vínculos; segunda importação: 0 e 0. Não são testes com jogadores reais nem validação visual em navegador.
