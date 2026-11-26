from contextlib import asynccontextmanager
from pathlib import Path
import sqlite3
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from .database import init_db, db
from .atualizacao_v8 import atualizar
from .routes.api import router

@asynccontextmanager
async def lifespan(app):
    init_db()
    with db() as c:
        atualizar(c)
    yield

app=FastAPI(title='Yvonator',version='1.0.0',lifespan=lifespan)
app.include_router(router)

@app.exception_handler(sqlite3.OperationalError)
async def erro_db(request:Request, exc:sqlite3.OperationalError):
    return JSONResponse(status_code=503,content={'detail':'Banco de dados temporariamente indisponível'})

@app.get('/',include_in_schema=False)
def inicio():
    return RedirectResponse('/jogo/HTML/inicio.html')

FRONT=Path(__file__).resolve().parent.parent/'Yvonator_pasta'
if FRONT.is_dir():
    app.mount('/jogo',StaticFiles(directory=FRONT),name='jogo')
