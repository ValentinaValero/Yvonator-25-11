from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from ..database import db
from ..schemas import RespostaEntrada, ConfirmacaoEntrada
from ..services import jogo
router=APIRouter(prefix='/api')

IMG_DIR = Path(__file__).resolve().parents[2] / 'Yvonator_pasta' / 'IMG'
FOTO_DIR = IMG_DIR / 'professores'
FORMATOS_FOTO = (('.webp', 'image/webp'), ('.jpg', 'image/jpeg'),
                 ('.jpeg', 'image/jpeg'), ('.png', 'image/png'))

@router.get('/personagens')
def personagens():
    with db() as c: return jogo.allrows(c,'SELECT * FROM personagem ORDER BY nome')

@router.get('/personagens/{id}')
def personagem(id:int):
    with db() as c:
        p=jogo.one(c,'SELECT * FROM personagem WHERE id=?',(id,))
        if not p: raise HTTPException(404,'Personagem não encontrado')
        return p

@router.get('/personagens/{id}/foto')
def foto_personagem(id: int):
    # O ID é validado; nenhum caminho informado pelo cliente é usado.
    with db() as c:
        if not jogo.one(c, 'SELECT id FROM personagem WHERE id=?', (id,)):
            raise HTTPException(404, 'Personagem não encontrado')
    # Sem cache para reconhecer fotos adicionadas/substituídas durante o jogo.
    headers = {'Cache-Control': 'no-store'}
    for extensao, tipo in FORMATOS_FOTO:
        arquivo = FOTO_DIR / f'professor_{id:02d}{extensao}'
        if arquivo.is_file():
            return FileResponse(arquivo, media_type=tipo, headers=headers)
    return FileResponse(IMG_DIR / 'professor_padrao.svg', media_type='image/svg+xml', headers=headers)

@router.post('/partidas',status_code=201)
def iniciar():
    with db() as c: return jogo.novo(c)

@router.get('/partidas/{id}')
@router.get('/partidas/{id}/proxima-pergunta')
@router.get('/partidas/{id}/resultado')
def consultar(id:str):
    # GET é somente leitura; a próxima pergunta é reservada no POST anterior.
    with db() as c: return jogo.estado(c,id)

@router.post('/partidas/{id}/responder')
def responder(id:str,body:RespostaEntrada):
    with db() as c: return jogo.responder(c,id,body)

@router.post('/partidas/{id}/confirmar-resultado')
def confirmar(id:str,body:ConfirmacaoEntrada):
    with db() as c: return jogo.confirmar(c,id,body)

@router.get('/partidas/{id}/classificacao')
def classificacao(id:str):
    with db() as c:
        p=jogo.partida(c,id)
        if p['status']=='em_andamento': raise HTTPException(409,'Classificação disponível após o palpite')
        rank,_,_=jogo.ranking(c,id)
        return [{'id_personagem':x['personagem']['id'],'nome':x['personagem']['nome'],'compatibilidade':round(x['peso']*100,2)} for x in rank]
