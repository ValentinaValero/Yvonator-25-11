# Yvonator — V7: fotos dos professores

Atualização exclusivamente visual, com suporte de um novo endpoint HTTP. Não altera o algoritmo, os JSONs ou o SQLite, nem exige migração. As telas resultado.html e personagem.html utilizam a mesma função JavaScript para mostrar as fotos.

## Aplicar no Windows (recomendado)
1. Pare o servidor (Ctrl+C). Faça backup da pasta atual.
2. Extraia o ZIP em uma pasta separada. Na pasta do projeto atual, copie/substitua apenas:
   - `backend/routes/api.py`
   - `backend/tests/test_fotos.py` (opcional, para testes)
   - `Yvonator_pasta/JS/api.js`
   - `Yvonator_pasta/HTML/resultado.html` e `Yvonator_pasta/HTML/personagem.html`
   - `Yvonator_pasta/IMG/professor_padrao.svg` e a pasta `Yvonator_pasta/IMG/professores/`
   - `LISTA_DE_FOTOS.md` e este arquivo.
3. Abra `LISTA_DE_FOTOS.md` e salve as imagens na pasta `Yvonator_pasta/IMG/professores/` conforme o ID indicado, por exemplo `professor_01.jpg`.
4. Com o terminal na raiz do projeto atual, inicie o servidor como antes:
   ` .\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8001 `
5. Acesse http://127.0.0.1:8001/ ou o endereço de rede que você já utiliza. Se a tela estava aberta, atualize-a; para uma cópia mais antiga do JS em cache, use Ctrl+F5 no computador.

## Fotos
- Formatos aceitos: WebP, JPG, JPEG e PNG, com extensão em minúsculas. Use a extensão verdadeira do arquivo. Caso haja múltiplos arquivos do mesmo ID, a prioridade é WebP > JPG > JPEG > PNG.
- Recomendação: 600 × 600 pixels, se possível; não é obrigatório. O CSS existente preserva a proporção da foto sem esticar.
- Sem fotografia ou se a foto não carregar no navegador, aparece uma silhueta padrão. A troca de arquivo é reconhecida na próxima consulta ou recarga da tela, sem reconstruir o banco.
- Se a coluna `foto` de um personagem for preenchida futuramente, a URL explícita continua tendo prioridade como no código original. Na base enviada, todos os 41 valores estão vazios.
- Use fotos autorizadas para o contexto escolar. As fotos são servidas pelo site a qualquer visitante que tenha acesso ao servidor; não publique sem autorização. Remova metadados desnecessários antes de usar.

## Sobre o ZIP completo
O pacote contém uma cópia do banco de dados do ZIP recebido, mas não substitua seu banco atual (pode ter novas partidas). Não inclui `.venv`, `.git` ou caches Python; mantenha as pastas existentes. Para uma instalação nova, crie um ambiente com `python -m venv .venv` e instale ` .\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt `. Não reimporte dados se já existe um SQLite funcional.

## Verificação
- 42 testes Python passaram (35 preexistentes e 7 novos de fotos), executados com `python -m pytest -q --ignore=backend/tests/test_v5.py`.
- A execução completa já falhava antes da atualização: `test_v5.py` importa `MAX_PERGUNTAS`, que não existe no algoritmo V6 recebido. Não alteramos esses testes ou o algoritmo fora do escopo.
- A função JavaScript foi testada isoladamente no Node.js (associação, troca de ID e fallback). O teste visual em Chromium foi bloqueado pelo ambiente; falta validar as telas em navegador real e nos tablets.
- O arquivo SQLite foi comparado byte a byte ao original e permaneceu idêntico.
