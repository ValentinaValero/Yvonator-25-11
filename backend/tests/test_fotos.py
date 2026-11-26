"""A foto é resolvida sem modificar os personagens nem a partida."""
import pytest
from backend.tests.test_api import client, start, answer, confirm
from backend.routes import api


def test_foto_ausente_e_id_invalido(client, tmp_path, monkeypatch):
    monkeypatch.setattr(api, 'FOTO_DIR', tmp_path)
    res = client.get('/api/personagens/1/foto')
    assert res.status_code == 200
    assert res.headers['content-type'].startswith('image/svg+xml')
    assert res.headers['cache-control'] == 'no-store'
    assert res.content == (api.IMG_DIR / 'professor_padrao.svg').read_bytes()
    assert client.get('/api/personagens/999/foto').status_code == 404


@pytest.mark.parametrize('ext,tipo', api.FORMATOS_FOTO)
def test_foto_dinamica(client, tmp_path, monkeypatch, ext, tipo):
    monkeypatch.setattr(api, 'FOTO_DIR', tmp_path)
    url = '/api/personagens/1/foto'
    assert client.get(url).headers['content-type'].startswith('image/svg+xml')
    # Testa o roteamento de bytes; decodificação é exercitada no navegador.
    f = tmp_path / ('professor_01' + ext)
    f.write_bytes(b'foto de teste')
    res = client.get(url)
    assert res.content == b'foto de teste'
    assert res.headers['content-type'] == tipo
    f.write_bytes(b'foto substituida')
    assert client.get(url).content == b'foto substituida'
    f.unlink()
    assert client.get(url).headers['content-type'].startswith('image/svg+xml')


def test_prioridade_e_associacao(client, tmp_path, monkeypatch):
    monkeypatch.setattr(api, 'FOTO_DIR', tmp_path)
    (tmp_path / 'professor_01.jpg').write_bytes(b'primeiro-jpg')
    (tmp_path / 'professor_01.webp').write_bytes(b'primeiro-webp')
    (tmp_path / 'professor_02.png').write_bytes(b'segundo')
    assert client.get('/api/personagens/1/foto').content == b'primeiro-webp'
    assert client.get('/api/personagens/2/foto').content == b'segundo'


def test_palpite_e_confirmacao_mantem_id(client):
    s = start(client)
    while s['status'] == 'em_andamento':
        s = answer(client, s, 'sim').json()
    assert s['status'] == 'palpite'
    id = s['resultado']['id_personagem']
    assert client.get(f'/api/personagens/{id}/foto').status_code == 200
    x = confirm(client, s, True).json()
    assert x['status'] == 'confirmada'
    assert x['resultado']['id_personagem'] == id
    assert x['resultado']['foto'] is None
