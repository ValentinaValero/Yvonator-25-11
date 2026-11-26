# Back-end do Yvonator

## Estrutura

```
backend/
  main.py                 # aplicação e front estático
  database.py             # esquema relacional, conexão e transação
  schemas.py              # validação Pydantic
  importar.py             # importação JSON local
  simular.py              # simulação da pesquisa
  algorithms/compatibilidade.py
  services/jogo.py        # estados e regras da partida
  routes/api.py           # endpoints REST
  tests/test_api.py
  requirements.txt
  .env.example
```

Usamos SQL parametrizado, IDs UUID para partidas, chaves estrangeiras, unicidade por pergunta/partida e transações SQLite com `BEGIN IMMEDIATE` para impedir respostas concorrentes conflitantes. O esquema SQL e o acesso centralizado permitem migrar posteriormente, mas será necessário adaptar driver, placeholders, DDL e estratégia transacional; não é uma migração automática. Schemas e rotas ficam separados da lógica.

## Modelo relacional

- `personagem` N:N `pergunta`, por `personagem_pergunta` (resposta conhecida sim/não; ausência da linha = desconhecida).
- `partida` 1:N `partida_pergunta`, que registra a ordem e impede repetição.
- `partida_pergunta` 1:0..1 `resposta`, incluindo `naoSei` e data.
- `partida` 1:N `resultado`, um candidato por tentativa; `confirmado` nulo (pendente), 0 (rejeitado), 1 (confirmado). Apenas um pendente por partida.
- `partida` 1:N `historico`, eventos de início, perguntas, respostas, palpites e fim.

Estados: `em_andamento`, `palpite`, `confirmada`, `sem_resultado`. Partidas interrompidas pelo navegador permanecem em andamento; expiração automática é uma extensão futura.

## Etapa 3 — Compatibilidade e seleção

Cada candidato inicia com peso igual. Cada resposta conhecida equivalente à matriz multiplica o peso por 3, e uma divergência divide por 3. `naoSei` ou característica desconhecida não altera a pontuação. Os pesos são calculados em escala logarítmica e normalizados; eles são **indicadores relativos, não probabilidades calibradas**. Uma resposta isolada não elimina candidatos. Uma rejeição explícita de palpite exclui apenas aquele personagem da partida, nunca da base.

Se `p_sim` e `p_nao` forem as somas de pesos normalizados para uma pergunta ainda não feita, a utilidade é `4 * p_sim * p_nao * prioridade`. Discriminar candidatos de peso semelhante é favorecido; dados faltantes reduzem a utilidade. Empates de seleção têm desempate por ID para permitir reprodução. Não há sequência fixa.

Sugere resultado quando há pelo menos quatro evidências conhecidas para o líder, peso ≥75%, margem ≥20 pontos percentuais e mais correspondências do que divergências. Se as perguntas úteis acabarem, exige líder único com evidência positiva predominante, mas permite palpite de baixa confiança. Se não houver líder único com evidência suficiente, termina sem resultado. Após rejeição, faz outra pergunta útil se disponível. Os parâmetros estão em `algorithms/compatibilidade.py` e foram definidos como valores iniciais, não aprovados por estudo com usuários.

## Etapa 4 — API REST

Todos os endpoints usam JSON. Base URL: `http://127.0.0.1:8000`. O Swagger em `/docs` permite testar as rotas sem o front.

| Método | Caminho | Entrada JSON / parâmetros | Saída 2xx | Erros típicos |
|---|---|---|---|---|
| GET | `/api/personagens` | nenhuma | lista de personagens | 503 |
| GET | `/api/personagens/{id}` | id inteiro | personagem | 404, 422, 503 |
| POST | `/api/partidas` | sem corpo (ou `{}`) | estado, 201 | 503 |
| GET | `/api/partidas/{id}` | UUID da partida | estado | 404, 503 |
| GET | `/api/partidas/{id}/proxima-pergunta` | UUID da partida | estado com pergunta atual | 404, 503 |
| POST | `/api/partidas/{id}/responder` | `id_pergunta` inteiro; `resposta` sim/nao/naoSei | estado atualizado | 404, 409, 422, 503 |
| GET | `/api/partidas/{id}/resultado` | UUID da partida | estado com resultado, se houver | 404, 503 |
| POST | `/api/partidas/{id}/confirmar-resultado` | `id_resultado` inteiro; `confirmado` booleano | estado atualizado | 404, 409, 422, 503 |
| GET | `/api/partidas/{id}/classificacao` | UUID da partida | lista ordenada (bloqueada durante investigação) | 404, 409, 503 |

Exemplo de estado (IDs e texto ilustrativos; a API e a base fornecem os reais):

```json
{"id_partida":"00000000-0000-4000-8000-000000000001","status":"em_andamento","quantidade_perguntas":0,"pergunta":{"id":1,"enunciado":"Seu personagem atua no ensino médio?","categoria":"etapa","ordem":1},"resultado":null}
```

Resposta: `{"id_pergunta":1,"resposta":"sim"}`. Quando houver palpite, `pergunta` será nula e `resultado` terá `id_resultado`, `id_personagem`, `nome`, `materia`, `categoria`, `foto`, `compatibilidade` (percentual relativo do modelo) e `confirmado` (nulo, 0 ou 1).

Confirmação: `{"id_resultado":1,"confirmado":false}`. A mesma solicitação repetida com os mesmos dados é idempotente (retorna estado atual); resposta diferente para pergunta já respondida recebe 409. 404 indica id inexistente; 422, corpo/tipo inválido; 503, base indisponível ou não importada. Erros de domínio retornam `{"detail":"mensagem"}`; erros Pydantic retornam lista de detalhes.

## Etapa 5 — Front-end

O script de integração modifica somente a entrada de temática, as tags dos scripts e a ação inline de acerto. O `fetch` usa URL relativa à origem, e a aplicação FastAPI serve o front estático. Erros de rede / JSON inesperado apresentam mensagem e opção de reconsulta/retry. A reconsulta após falha de envio verifica se a resposta chegou antes de liberar nova seleção. O navegador não calcula compatibilidade. O modal de falha só aparece quando não há resultado sustentado pelos dados. Não foram alterados estilos ou animações já existentes.

## Etapa 6 — Verificação

Na raiz do repositório:

```sh
python -m pytest -q backend/tests
python -m backend.simular backend/data/yvonator_dados_locais.json
```

Resultados desta entrega: 41 personagens, 46 perguntas. Na simulação (respostas automaticamente retiradas da própria matriz, sem erros humanos): 39 primeiros palpites corretos, nenhum incorreto, 2 sem palpite por empate indistinguível; mediana 6, média 8,20, mínimo 5, máximo 44 perguntas. Não é uma medida de acurácia em produção. Os testes API usam dados fictícios e banco temporário. Foram verificados ainda a sintaxe dos três scripts JavaScript com Node e os cinco trechos HTML contra os arquivos originais recuperados do GitHub. Não foi executado teste visual ou automatizado em um navegador com o front completo. Faça a validação manual com o repositório local: iniciar, responder sim/não/não sei, atualizar página, confirmar, rejeitar palpite, recomeçar, desligar temporariamente a API e revisar os estados de erro.
