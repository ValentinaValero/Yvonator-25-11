> **V8:** Consulte [ATUALIZACAO_V8.md](ATUALIZACAO_V8.md) para os procedimentos atuais de instalação, as novas regras e os testes.

# Yvonator | Integração do back-end

Esta entrega é uma **sobreposição de arquivos**, não uma cópia integral do repositório. Foi preparada a partir do front `ValentinaValero/Yvonator`, branch `main`, árvore `5c3c99bd00264715a32d7801b8ecfbe01360c315`. Nenhuma alteração foi enviada ao GitHub. Os arquivos de imagem, CSS e HTML existentes permanecem no repositório; o script `integrar.py` altera apenas cinco trechos de quatro HTMLs.

## Instalação (Python 3.10+; recomendado 3.11 ou 3.12)

1. Abra a pasta do repositório local (aquela que contém `Yvonator_pasta`). Se ainda não possui a cópia, use `git clone https://github.com/ValentinaValero/Yvonator.git` e `cd Yvonator`.
2. Extraia o ZIP nesta raiz, preservando as pastas. Substitua `JS/perguntas.js` e `JS/resultado.js` quando solicitado (faça backup ou use uma branch local).
3. Execute estes comandos na raiz:

```sh
python -m venv .venv
```

Windows PowerShell: `.venv\Scripts\Activate.ps1` (ou use diretamente `.venv\Scripts\python.exe` no lugar de `python`). macOS/Linux: `source .venv/bin/activate`.

```sh
python -m pip install -r backend/requirements.txt
python integrar.py
```

4. Crie `backend/data/` e coloque nela o arquivo separado `yvonator_dados_locais.json`. **Não publique a base da pesquisa, o JSON, o SQLite nem fotos sem autorização.** A pasta `backend/data/` é ignorada pelo Git.

```sh
python -m backend.importar backend/data/yvonator_dados_locais.json
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

5. Abra **http://127.0.0.1:8000/** para jogar. Não abra os HTMLs diretamente nem pelo Live Server: a interface e a API devem compartilhar a mesma origem. Swagger: http://127.0.0.1:8000/docs.

Se a importação encontrar partidas existentes, ela é recusada para não alterar retrospectivamente o histórico. Para testar uma versão nova, encerre o servidor e configure outro arquivo SQLite (variável de ambiente `YVONATOR_DB`) ou faça backup do banco e use um banco novo. A `.env.example` é apenas referência. Adicione também `.venv/` ao seu `.gitignore` local, se necessário.

## Etapa 1 — Diagnóstico do front

| Arquivo | Papel original | Integração |
|---|---|---|
| `HTML/inicio.html` | Abertura e botão que leva a temática | Sem alteração |
| `HTML/tematica.html` | Escolhe Professores | Parâmetro `?nova=1` para iniciar nova partida |
| `HTML/perguntas.html` | Texto fixo no `<p>` e três radios de valores `sim`, `nao`, `naoSei` | Script como módulo, texto preenchido pela API |
| `JS/perguntas.js` | Vazio | Implementa criação, consulta, resposta, carregamento e recuperação de erros |
| `HTML/resultado.html` | `<strong>` vazio, foto provisória, labels `acertou` e `errou`, modal | Remove navegação inline de Acertou; script como módulo |
| `JS/resultado.js` | Abre modal de erro e usa listener de `errou` | Registra confirmação/rejeição, atualiza resultado e continua investigação |
| `HTML/personagem.html` | Tela final com imagem e botão de recomeçar; referenciava script que pressupunha `errou` | Script como módulo com tratamento próprio da página |
| `HTML/teste.html` | Experimento visual do título | Sem alteração |
| `CSS/*.css` e `IMG/*.png` | Aparência, fontes, transições, animações do modal e gênio | Sem alteração |

O código atual não armazenava respostas nem partidas. A API é a fonte de verdade; o navegador guarda apenas o UUID da partida no `sessionStorage`. Acrescentamos `JS/api.js` para comunicação compartilhada. O script de integração verifica os trechos reais antes de gravar qualquer mudança; pode ser executado novamente sem duplicar mudanças.

Fluxo: início → temática → perguntas → resultado → personagem (acerto). Se o jogador rejeitar, retorna às perguntas quando houver uma pergunta que diferencie candidatos; caso contrário, tenta um novo palpite sustentado pelos dados ou encerra sem resultado. No encerramento sem resultado, utiliza-se o modal original.

## Etapa 2 — Dados e modelagem

A planilha `Página1`, A1:Q43, contém 42 linhas com nome, 17 colunas e 41 nomes distintos após remoção de espaços e normalização de maiúsculas/acentos. As linhas 19 e 40 têm nome repetido e divergências. Foram consolidadas provisoriamente em um personagem; respostas contraditórias viraram desconhecidas, usando concordância por pergunta. Confirme se é de fato a mesma pessoa antes de usar a base em definitivo.

A partir de categorias de função, disciplina, modalidade, etapa, cor/comprimento/tipo de cabelo e acessório facial, foram geradas 46 perguntas (22 disciplina, 16 aparência, 4 função, 2 modalidade e 2 etapa). São perguntas derivadas das colunas, não transcrições de enunciados prontos. Categorias com barra são multivaloradas; `Ambos` indica médio e fundamental; `NULL` e células vazias são desconhecidas, não negativas. Foram normalizados acentos e a abreviação `Ed. Financeira`; `R. Matemática` permaneceu separada por ser ambígua. Perguntas constantes foram descartadas. Há 49 pares personagem/pergunta sem resposta conhecida na matriz final. Não inferimos características de professores que não tinham informação registrada.

A primeira versão não usa idade, gênero, filhos, viagem, cidade/estado natal nem textos diferenciais não revisados. Decisão de minimização de dados pessoais e de evitar transformar comentários subjetivos em afirmações sobre todos os demais. Para adicionar depois, revise pertinência e autorização, formule perguntas neutras e preencha explicitamente `sim`, `nao` ou deixe ausente quando desconhecido. `FOTO?` não é um caminho de imagem; todos os campos `foto` estão nulos, porque não há retratos no repositório nem na planilha analisada. O placeholder existente é exibido. Para retratos autorizados, aponte `foto` para `/jogo/IMG/fotos/arquivo.jpg` no JSON antes de importar.

A matriz de dados não deve ir ao repositório público. O jogo foi preparado para execução local, sem autenticação. Para disponibilizar em rede, primeiro revise autorizações, proteção de endpoints, retenção dos dados, controle de acesso e uso de HTTPS.

Consulte `backend/README.md` para relacionamentos, algoritmo, endpoints, testes e critérios de confiança.
