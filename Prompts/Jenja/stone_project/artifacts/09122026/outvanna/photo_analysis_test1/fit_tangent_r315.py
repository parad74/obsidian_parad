from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares
from PIL import Image,ImageDraw,ImageFont

p=Path(__file__).resolve().parent
data=json.loads((p/'analysis_v2.json').read_text(encoding='utf-8'))
q=np.array(data['marker_points_rectified_mm'])
R=315.;cy=405.;top=90.;bottom=720.
cx=float(least_squares(lambda x:np.linalg.norm(q-[x[0],cy],axis=1)-R,[370.]).x[0])
errors=np.linalg.norm(q-[cx,cy],axis=1)-R
reference_cx=62.5+315
assert cy-R==top and cy+R==bottom
im=Image.open(p/'rectified_assumption_v2.png').crop((0,0,825,810)).convert('RGB')
d=ImageDraw.Draw(im)
blue='#0068df';orange='#b94d00'
# Blue reference assumes a centred 1605 mm opening within 1730 mm.
for x,color in [(reference_cx,blue),(cx,orange)]:
    d.ellipse((x-R,cy-R,x+R,cy+R),outline=color,width=2)
    d.line((x-6,cy,x+6,cy),fill=color,width=2)
    d.line((x,cy-6,x,cy+6),fill=color,width=2)
# Tangent joins, not free radius estimation.
for y in [top,bottom]:
    d.line((cx,y,825,y),fill=orange,width=2)
    d.ellipse((cx-5,y-5,cx+5,y+5),outline=orange,width=2)
for x,y in q:d.ellipse((x-2,y-2,x+2,y+2),outline=orange,width=1)
d.line((cx,top,cx,bottom),fill=orange,width=1)
d.line((cx,cy,cx+R,cy),fill=orange,width=2)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',21)
def label(x,y,text):
    box=d.textbbox((x,y),text,font=font)
    d.rectangle((box[0]-3,box[1]-2,box[2]+3,box[3]+2),fill='white')
    d.text((x,y),text,font=font,fill=orange)
label(cx+85,cy-30,'R = 315 мм')
label(cx+12,cy+12,'O')
label(cx+12,top+24,'Касание: Y = 90 мм')
label(cx+12,bottom-52,'Касание: Y = 720 мм')
canvas=Image.new('RGB',(825,965),'white');canvas.paste(im,(0,155));dc=ImageDraw.Draw(canvas)
for y,t in [(10,'R315: плавное сопряжение сверху и снизу, ширина 630 мм'),
 (42,'Коричневый: подбор центра по маркеру при R = 315 мм'),
 (74,'Синий: опорная круговая модель выреза 1605 × 630 мм'),
 (106,f'Центр подбора: X ≈ {cx:.1f} мм; Y = 405 мм. Фото условно выровнено.')]:
    dc.text((12,y),t,font=font,fill='black')
dest=p/'tangent_r315.png';assert not dest.exists();canvas.save(dest)
result=dict(radius_mm=R,center_mm=[cx,cy],reference_center_mm=[reference_cx,cy],
 horizontal_center_shift_mm=cx-reference_cx,join_top_mm=[cx,top],join_bottom_mm=[cx,bottom],
 opening_width_mm=bottom-top,marker_radial_rms_mm=float(np.sqrt(np.mean(errors**2))),
 marker_max_radial_error_mm=float(np.max(np.abs(errors))),
 continuity='Position and tangent direction continuous at both joins (G1), not curvature continuity.',
 assumption='Uses prior conditional photo affine mapping and manual marker points. Fits X only; R=315 and Y=405 fixed.',
 reference='Circular centred 1605x630 opening; this is NOT the existing superellipse DXF.')
(p/'tangent_r315.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
