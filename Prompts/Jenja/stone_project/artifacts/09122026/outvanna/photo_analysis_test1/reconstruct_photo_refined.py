from pathlib import Path
import json, hashlib, math
import numpy as np
from scipy.optimize import least_squares
from PIL import Image, ImageDraw, ImageFont

out=Path(__file__).resolve().parent
source=out.parent.parent/'invanna/test1/photo_2026-11-13_20-58-53.jpg'
im=Image.open(source).convert('RGB')
# Manual picks of the visible thin marker line, not the broad inner shadow.
# Pixel picking uncertainty approximately 2-3 px; no automated precision claim.
p=np.array([[305,139],[240,155.5],[190,182.5],[140,226],[110,267.5],
 [92,310],[83.5,350],[80.5,375],[84.5,415],[96.5,455],[117.5,495],
 [144.5,530],[179,563],[218.5,589.5],[262,610],[303,621]],dtype=float)
# Refine marker picks using narrow intensity minima outside the cut edge.
# Offsets inspected in grayscale radial profiles, not a uniform contour offset.
indices=np.array([1,2,3,4,5,8,9,10,11,12,13,14])
offsets=np.array([4,6,5,3,2,1,3,5,7,7,6,2],dtype=float)
seeds=p[indices].copy()
normal=seeds-np.array([320,382]);normal/=np.linalg.norm(normal,axis=1)[:,None]
p=seeds+normal*offsets[:,None]
# User permits a preliminary horizontal no-tilt model. Additional explicit
# approximation: equal local X/Y scale, no projective depth variation.
# Straight inner edges near the left end: source y=140 and y=624, 630 mm apart.
# Outer left edge leans from (26,69) to (48,694); remove this affine shear.
s=484/630
k=22/625
b=140-90*s
affine=(s,k*s,26+k*(b-69),0,s,b)
rect=im.transform((1630,810),Image.Transform.AFFINE,affine,
                  resample=Image.Resampling.BICUBIC,fillcolor='white')
assert not (out/'rectified_assumption_v2.png').exists(), 'Preserve prior output'
rect.save(out/'rectified_assumption_v2.png')
q=np.column_stack(((p[:,0]-26-k*(p[:,1]-69))/s,(p[:,1]-b)/s))
def fit(points):
    z=least_squares(lambda z:np.linalg.norm(points-z[:2],axis=1)-z[2],[372,404,311]).x
    residual=np.linalg.norm(points-z[:2],axis=1)-z[2]
    return z,float(np.sqrt(np.mean(residual**2)))
z,rms=fit(q);cx,cy,r=z
ref=json.loads((out.parent.parent/'circle_analysis_33/circle_old_original.json').read_text())
reference_r=ref['radius_mm']
# Coincident fitted centres compare curvature only, not placement on the bath.
layer=Image.new('RGBA',rect.size)
d=ImageDraw.Draw(layer)
blue='#0068df'; orange='#b94d00'
for rad,color in [(reference_r,blue),(r,orange)]:
    d.ellipse((cx-rad,cy-rad,cx+rad,cy+rad),outline=color,width=2)
d.line((cx-9,cy,cx+9,cy),fill=blue,width=2)
d.line((cx,cy-9,cx,cy+9),fill=blue,width=2)
for x,y in q:
    d.ellipse((x-3,y-3,x+3,y+3),outline=orange,width=2)
d.line((cx,cy,cx+r/math.sqrt(2),cy-r/math.sqrt(2)),fill=orange,width=2)
d.line((700,90,700,720),fill=blue,width=2)
for y in [90,720]:d.line((689,y,711,y),fill=blue,width=2)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
d.text((cx+12,cy+8),'O',font=font,fill=blue)
d.text((710,390),'630 мм',font=font,fill=blue)
annotated=Image.alpha_composite(rect.convert('RGBA'),layer).convert('RGB')
canvas=Image.new('RGB',(1630,965),'white');canvas.paste(annotated,(0,155))
dt=ImageDraw.Draw(canvas)
dt.text((24,12),'Условная реконструкция. Сравнение формы с совмещёнными центрами.',font=font,fill='black')
dt.text((24,48),f'Синий: исходный рисунок R ≈ {reference_r:.1f} мм. Коричневый: подбор маркера R ≈ {r:.0f} мм.',font=font,fill='black')
dt.text((24,84),'Точки — ручное считывание маркера. Масштаб X = Y; перспектива полностью не определена.',font=font,fill='black')
dt.text((24,118),'Разница радиусов здесь не доказывает размерное расхождение реальной ванны.',font=font,fill='black')
canvas.save(out/'marker_vs_source_circle_v2.png')
# Inspect selected marker points on the untouched source to avoid mistaking shadow for line.
check=im.copy();dc=ImageDraw.Draw(check)
for x,y in p:dc.ellipse((x-3,y-3,x+3,y+3),outline='#00ffff',width=1)
check.crop((40,110,380,650)).resize((680,1080)).save(out/'marker_picks_check_v2.png')
data=dict(source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
 measured_opening_width_mm=630,source_inner_straight_y=[140,624],source_pixels_per_mm=s,
 inverse_image_affine=list(affine),model='Conditional affine shear correction; equal X/Y scale, no depth scale change',
 marker_points_source_px=p.tolist(),marker_points_rectified_mm=q.tolist(),
 marker_center_mm=[cx,cy],marker_radius_mm=r,marker_fit_rms_mm=rms,
 source_drawing_radius_mm=reference_r,radius_difference_mm=r-reference_r,
 registration='Centres superimposed only for shape comparison; physical alignment unknown',
 manual_point_uncertainty_px='approximately 2-3; not a statistical confidence interval',
 limitations='Not a unique perspective correction. Unknown horizontal foreshortening and tracing alignment. Do not use to modify CNC.')
(out/'analysis_v2.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in data.items() if 'points' not in k},ensure_ascii=False,indent=2))
