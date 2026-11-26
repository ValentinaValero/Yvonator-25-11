"""Simulação local com a matriz de pesquisa, sem imprimir nomes e sem alterar o banco real."""
import argparse, json, os, statistics, tempfile
from collections import Counter
from pathlib import Path
from fastapi.testclient import TestClient
from .main import app
from .importar import importar

def simular(path):
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    inicial=Counter(); final=Counter(); perguntas=[]; rejeicoes=0
    anterior=os.environ.get('YVONATOR_DB')
    try:
        with tempfile.TemporaryDirectory() as tmp:
            os.environ['YVONATOR_DB']=str(Path(tmp)/'simulacao.sqlite3')
            importar(path)
            with TestClient(app) as client:
                for pessoa in data['personagens']:
                    res=client.post('/api/partidas');res.raise_for_status();s=res.json()
                    primeira=None; feitas=set()
                    while s['status'] in ('em_andamento','palpite'):
                        pid=s['id_partida']
                        if s['status']=='em_andamento':
                            q=s['pergunta']['id']
                            assert q not in feitas, 'Pergunta repetida'
                            feitas.add(q)
                            res=client.post(f'/api/partidas/{pid}/responder',json={'id_pergunta':q,'resposta':pessoa['respostas'].get(str(q),'naoSei') or 'naoSei'})
                        else:
                            r=s['resultado']; correto=r['id_personagem']==pessoa['id']
                            if primeira is None: primeira='correto' if correto else 'incorreto'
                            rejeicoes+=not correto
                            res=client.post(f'/api/partidas/{pid}/confirmar-resultado',json={'id_resultado':r['id_resultado'],'confirmado':correto})
                        res.raise_for_status();s=res.json()
                    inicial[primeira or 'sem palpite']+=1;final[s['status']]+=1;perguntas.append(len(feitas))
    finally:
        if anterior is None:os.environ.pop('YVONATOR_DB',None)
        else:os.environ['YVONATOR_DB']=anterior
    return {'primeiro_palpite':dict(inicial),'status_final':dict(final),'perguntas_mediana':statistics.median(perguntas),'perguntas_media':statistics.mean(perguntas),'perguntas_min':min(perguntas),'perguntas_max':max(perguntas),'rejeicoes':rejeicoes}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('arquivo');a=parser.parse_args();print(json.dumps(simular(a.arquivo),ensure_ascii=False,indent=2))
