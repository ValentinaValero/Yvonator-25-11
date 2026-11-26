# Yvonator — V8

## Instalação

1. Pare o servidor (`Ctrl+C`) e guarde uma cópia da pasta do projeto.
2. Se recebeu o pacote completo, extraia a pasta `Yvonator` em um novo local. Se já alterou fotos, características ou jogou depois do ZIP original, prefira o pacote **somente código**: extraia o conteúdo diretamente na raiz do projeto atual, permitindo substituir os arquivos de código indicados. Ele não contém o SQLite nem as imagens.
3. Abra a raiz do projeto no VS Code. Use o ambiente virtual que já utiliza e execute `python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000`. Se precisar instalar as dependências: `python -m pip install -r backend/requirements.txt`.
4. Abra `http://localhost:8000` e inicie uma partida nova. Se a aparência antiga persistir, recarregue a página sem cache (`Ctrl+F5`).

A migração dos enunciados e da pergunta desativada é automática ao iniciar o servidor. Também pode ser executada manualmente, com o servidor parado, via `python -m backend.atualizacao_v8`. Ela é idempotente; não é preciso reimportar a pesquisa. Uma partida antiga com a pergunta de professor ainda pendente recebe outra pergunta. As respostas já gravadas são conservadas.

## Alterações

- A primeira pergunta agora é sobre gênero, se cadastrada; a pergunta sobre ser professor foi desativada, não apagada.
- Características de aparência recebem maior prioridade de seleção. Disciplina, modalidade, etapa e idade continuam disponíveis. Perfil pessoal tem prioridade menor.
- Dois `Não sei` em uma categoria multiplicam sua prioridade de seleção por 0,35; quatro por 0,1225. Isso não altera a pontuação de compatibilidade nem elimina personagens.
- A seleção continua dinâmica, com dedução de perguntas redundantes a partir da base. Modalidades técnicas e regulares não são tratadas como excludentes. Após confirmar matérias técnicas, DS/ADM ganham um multiplicador de 2 na seleção.
- As perguntas diferenciais e as regras de confirmação final foram conservadas; os critérios de compatibilidade não foram modificados.
- 28 enunciados gerais foram padronizados, incluindo os quatro textos aprovados. Os nomes das disciplinas e suas respostas foram mantidos. As curiosidades diferenciais foram preservadas.
- A resposta fica destacada durante pelo menos 700 ms enquanto a API trabalha, depois a próxima pergunta aparece com 300 ms adicionais de bloqueio. A proteção vale também para respostas consecutivas; conexão lenta pode aumentar o intervalo. A animação respeita a preferência de movimento reduzido.
- Imagens, tela de resultado, tema, esquema SQLite e API foram preservados.

## Verificação

No banco recebido: 41 personagens, 2.412 vínculos de características, 50 partidas, 692 respostas e 41 registros de resultado foram comparados registro por registro e permaneceram idênticos. A verificação de integridade do SQLite passou. Uma pergunta antiga pendente foi substituída, com registro no histórico.

| Cenário de simulação (41 personagens por cenário) | V7 | V8 |
|---|---:|---:|
| Respostas conforme todos os dados conhecidos — primeiro palpite correto | 41/41 | 41/41 |
| Média de perguntas nesse cenário | 8,22 | 7,54 |
| Respostas apenas de aparência e gênero — acertos | 20/41 | 20/41 |
| Média de perguntas nesse cenário, incluindo partidas sem resultado | 36,68 | 31,24 |
| Todas as respostas Não sei — palpites indevidos | 0 | 0 |

As simulações refletem a base, não garantem acerto com jogadores reais. Aparência e gênero apenas não distinguem todos os perfis. Não foram inventadas características novas.

`python -m pytest -q`: 46 testes passaram, uma suíte legada V5 foi sinalizada como ignorada porque depende de rotas, funções e arquivo de dados ausentes já no ZIP original. O teste isolado `node backend/tests/test_delay.mjs` passou, incluindo bloqueio e recuperação após erro. O Chromium do ambiente de teste bloqueou a navegação local; ainda é necessário validar o visual e os toques em um tablet real. O Node é necessário apenas para esse teste opcional, não para executar o jogo.

O pacote completo não contém `.venv`, `.git` nem caches Python. Guarde esses diretórios da sua instalação original, se existirem. Mantenha o banco e as fotos do projeto privados; não publique dados pessoais sem autorização.
