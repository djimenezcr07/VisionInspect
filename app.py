from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
import base64
import os
import sys
import warnings
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError
from flask import Flask, jsonify, render_template, request, send_from_directory

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"build"))
try:
    import vision_engine
    ENGINE_ERROR=None
except (ImportError,OSError) as exc:
    vision_engine=None
    ENGINE_ERROR=str(exc)

app=Flask(__name__)
app.config['MAX_CONTENT_LENGTH']=8*1024*1024
DEFAULTS={"foreground":90,"darkness":75,"min_area":35,"min_radius":40}
RANGES={"foreground":(30,220),"darkness":(0,200),"min_area":(1,100000),"min_radius":(10,2000)}
SAMPLES={"limpia":"pieza_limpia.png","manchas":"pieza_manchas.png","sin_pieza":"sin_pieza.png"}

@app.get('/')
def index(): return render_template('index.html',engine_available=vision_engine is not None,defaults=DEFAULTS)
@app.get('/api/status')
def status(): return jsonify(available=vision_engine is not None,version=getattr(vision_engine,'__version__',None),message=None if vision_engine else 'Motor C++ no disponible. Compilá el módulo siguiendo el README.')
@app.get('/samples/<name>')
def sample(name):
    if name not in SAMPLES.values(): return ('No encontrado',404)
    return send_from_directory(ROOT/'examples',name)

def parse_parameters(form):
    result={}
    for key,(lower,upper) in RANGES.items():
        try: value=int(form.get(key,DEFAULTS[key]))
        except (ValueError,TypeError): raise ValueError(f"El parámetro {key} debe ser un número entero.")
        if not lower<=value<=upper: raise ValueError(f"El parámetro {key} debe estar entre {lower} y {upper}.")
        result[key]=value
    return result

def read_image(file):
    data=file.read(8*1024*1024+1)
    if not data: raise ValueError('El archivo está vacío.')
    if len(data)>8*1024*1024: raise ValueError('La imagen supera 8 MB.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error',Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as src:
                fmt=src.format
                if fmt not in ('PNG','JPEG'): raise ValueError('Usá una imagen PNG o JPEG.')
                if not (64<=src.width<=4096 and 64<=src.height<=4096): raise ValueError('Cada dimensión debe estar entre 64 y 4096 píxeles.')
                img=ImageOps.exif_transpose(src)
                if img.mode in ('RGBA','LA') or 'transparency' in img.info:
                    rgba=img.convert('RGBA'); background=Image.new('RGBA',rgba.size,(30,35,38,255)); img=Image.alpha_composite(background,rgba).convert('RGB')
                else: img=img.convert('RGB')
                return np.asarray(img),fmt
    except (UnidentifiedImageError,OSError,Image.DecompressionBombError,Image.DecompressionBombWarning) as exc: raise ValueError('No se pudo leer la imagen; verificá que no esté dañada.') from exc

@app.errorhandler(413)
def too_large(_): return jsonify(error='El archivo supera el límite de 8 MB.'),413

@app.post('/api/inspect')
def inspect():
    if vision_engine is None: return jsonify(error='Motor C++ no disponible. Compilá el módulo siguiendo el README.'),503
    if 'image' not in request.files: return jsonify(error='Seleccioná una imagen para analizar.'),400
    try:
        params=parse_parameters(request.form); file=request.files['image']; rgb,fmt=read_image(file.stream)
        bgr=rgb[:,:,::-1].copy(); result,annotated=vision_engine.inspect(bgr,**params)
        result.update(fecha_utc=datetime.now(timezone.utc).isoformat(),imagen=Path(file.filename or 'imagen').name,ancho_px=int(rgb.shape[1]),alto_px=int(rgb.shape[0]),formato=fmt,parametros=params,version_motor=vision_engine.__version__,limitaciones='Demostración con piezas claras sobre fondo oscuro e iluminación uniforme. Las regiones no son defectos confirmados y requieren revisión humana; no sustituye una inspección industrial validada.')
        out=BytesIO(); Image.fromarray(annotated[:,:,::-1].copy()).save(out,format='PNG')
        return jsonify(report=result,annotated='data:image/png;base64,'+base64.b64encode(out.getvalue()).decode('ascii'))
    except (ValueError,RuntimeError) as exc: return jsonify(error=str(exc)),400
    except Exception:
        app.logger.exception('Error durante la inspección')
        return jsonify(error='No se pudo completar el análisis. Probá otra imagen o revisá los parámetros.'),500

if __name__=='__main__': app.run(host='127.0.0.1',port=int(os.environ.get('PORT','5078')),debug=False)
