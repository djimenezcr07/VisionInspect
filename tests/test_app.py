from io import BytesIO
from pathlib import Path
import json
import numpy as np
import pytest
from PIL import Image
import app as web

ROOT=Path(__file__).resolve().parents[1]
@pytest.fixture
def client():
    web.app.config.update(TESTING=True)
    return web.app.test_client()

def send(client,name,**params):
    with (ROOT/'examples'/name).open('rb') as f: data=f.read()
    return client.post('/api/inspect',data={'image':(BytesIO(data),name),**params},content_type='multipart/form-data')

def test_motor_import():
    assert web.vision_engine is not None, web.ENGINE_ERROR
    assert web.vision_engine.__version__=='1.0.0'

def test_clean_and_dark_spots(client):
    clean=send(client,'pieza_limpia.png'); assert clean.status_code==200
    a=clean.get_json(); assert a['report']['pieza_detectada'] and a['report']['regiones']==[]
    assert a['report']['radio_px'] in range(150,160) and a['annotated'].startswith('data:image/png;base64,')
    spotted=send(client,'pieza_manchas.png'); result=spotted.get_json()['report']; assert result['pieza_detectada'] and len(result['regiones'])==2
    for x in result['regiones']: assert 0<=x['x']<640 and 0<=x['y']<480 and x['area_px2']>0
    assert result['parametros']['darkness']==75 and result['imagen']=='pieza_manchas.png'
    assert 'revisión' in result['limitaciones']
    json.dumps(result)

def test_no_piece_and_parameter_effect(client):
    blank=send(client,'sin_pieza.png'); assert blank.status_code==200 and not blank.get_json()['report']['pieza_detectada']
    high=send(client,'pieza_manchas.png',min_area='5000'); assert high.status_code==200 and high.get_json()['report']['regiones']==[]
    assert send(client,'pieza_manchas.png',min_area='0').status_code==400

def test_bad_uploads(client):
    assert client.post('/api/inspect').status_code==400
    assert client.post('/api/inspect',data={'image':(BytesIO(b'bad'),'x.png')}).status_code==400
    assert client.post('/api/inspect',data={'image':(BytesIO(b''),'empty.png')}).status_code==400
    buf=BytesIO();Image.new('RGB',(20,20)).save(buf,format='PNG');buf.seek(0)
    assert client.post('/api/inspect',data={'image':(buf,'small.png')}).status_code==400
    buf=BytesIO();Image.new('RGB',(100,100)).save(buf,format='BMP');buf.seek(0)
    assert client.post('/api/inspect',data={'image':(buf,'fake.png')}).status_code==400

def test_engine_errors_and_no_engine(client,monkeypatch):
    monkeypatch.setattr(web,'vision_engine',None)
    assert client.get('/api/status').get_json()['available'] is False
    assert client.post('/api/inspect').status_code==503

def test_native_checks_invalid_inputs():
    with pytest.raises(ValueError): web.vision_engine.inspect(np.zeros((40,40,3),dtype=np.uint8))
    with pytest.raises(ValueError): web.vision_engine.inspect(np.zeros((100,100,3),dtype=np.uint8),min_area=0)

def test_transparent_image_composites_on_dark():
    buf=BytesIO();Image.new('RGBA',(100,100),(255,0,0,0)).save(buf,format='PNG');buf.seek(0)
    image,fmt=web.read_image(buf); assert fmt=='PNG' and image[0,0].tolist()==[30,35,38]

def test_jpeg_upload_and_report(client):
    buf=BytesIO(); Image.open(ROOT/'examples'/'pieza_manchas.png').convert('RGB').save(buf,format='JPEG',quality=95);buf.seek(0)
    response=client.post('/api/inspect',data={'image':(buf,'pieza.jpg')},content_type='multipart/form-data')
    assert response.status_code==200
    report=response.get_json()['report']
    assert report['formato']=='JPEG' and report['pieza_detectada'] and len(report['regiones'])==2
