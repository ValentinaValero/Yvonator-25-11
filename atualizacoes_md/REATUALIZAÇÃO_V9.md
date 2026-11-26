YVONATOR V9 — ÁRVORE ADAPTATIVA

Leia ATUALIZACAO_V9.md.
Pare o servidor (Ctrl+C) e faça backup do projeto.
Use preferencialmente o ZIP somente código: extraia na raiz do seu projeto,
onde ficam backend e Yvonator_pasta, aceitando substituir os arquivos.
Não é necessário alterar o banco, reinstalar nem importar os professores.

Na raiz do projeto, com o ambiente virtual ativo:
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

Abra http://localhost:8000 e comece uma nova partida.
