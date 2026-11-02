from pathlib import Path
from PIL import Image, ImageDraw
p=Path(__file__).resolve().parents[1]/'examples';p.mkdir(exist_ok=True)
def base():
 im=Image.new('RGB',(640,480),(32,39,42));d=ImageDraw.Draw(im);d.ellipse((165,65,475,375),fill=(189,194,188),outline=(212,216,210),width=3);return im
im=base();im.save(p/'pieza_limpia.png')
im=base();d=ImageDraw.Draw(im);d.ellipse((253,160,276,183),fill=(37,41,39));d.ellipse((348,241,375,266),fill=(48,48,44));im.save(p/'pieza_manchas.png')
im=Image.new('RGB',(640,480),(32,39,42));ImageDraw.Draw(im).rectangle((235,120,400,310),fill=(180,185,180));im.save(p/'sin_pieza.png')
print('Imágenes sintéticas generadas en',p)
