from pathlib import Path
import base64, hashlib, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.optimize import least_squares

out = Path(__file__).resolve().parent
src = out.parent / 'invanna2/photo_2026-11-12_19-19-33.jpg'
original = Image.open(src).convert('RGB')
a = np.asarray(original)
points = []
# Region inspected on this source; excludes the horizontal dimension line.
for y in range(211, 601):
    if 395 <= y <= 415:
        continue
    xs = np.flatnonzero(np.max(a[y, 150:345], axis=1) < 105)
    if not len(xs):
        continue
    run = [xs[0]]
    for x in xs[1:]:
        if x - run[-1] > 1:
            break
        run.append(x)
    if len(run) <= 10:
        points.append([150 + np.mean(run), y])
points = np.array(points)
def fit(p):
    result = least_squares(lambda q: np.linalg.norm(p-q[:2], axis=1)-q[2], [365,406,200], loss='soft_l1')
    residual = np.linalg.norm(p-result.x[:2], axis=1)-result.x[2]
    return result.x, float(np.sqrt(np.mean(residual**2)))
(cx,cy,r), rms = fit(points)
upper, upper_rms = fit(points[points[:,1] < 395])
lower, lower_rms = fit(points[points[:,1] > 415])
# For the circular model tangent to the two parallel straight edges,
# their stated separation 613 mm is the diameter; this is not a universal rule.
radius_mm = 613/2
stem = 'circle_on_original_exact'
n = 1
while any((out / (stem + ext)).exists() for ext in ['.png','.svg','.json']):
    n += 1
    stem = f'circle_on_original_exact{n}'

# Native-size source remains untouched. Draw only transparent annotations.
scale = 4
layer = Image.new('RGBA', (original.width*scale,original.height*scale))
d = ImageDraw.Draw(layer)
blue = (0,90,215,255)
box = tuple(v*scale for v in (cx-r,cy-r,cx+r,cy+r))
d.ellipse(box, outline=blue, width=2*scale)
def line(coords, width=2):
    d.line(tuple(v*scale for v in coords), fill=blue, width=width*scale)
line((cx-8,cy,cx+8,cy)); line((cx,cy-8,cx,cy+8))
angle = -math.pi/4
ex,ey = cx+r*math.cos(angle), cy+r*math.sin(angle)
line((cx,cy,ex,ey))
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22*scale)
for xy, txt in [((cx+10,cy+12),'O'),((cx-145,cy-105),'R ≈ 306,5 мм')]:
    d.text((xy[0]*scale,xy[1]*scale),txt,font=font,fill=blue)
layer = layer.resize(original.size,Image.Resampling.LANCZOS)
result = Image.alpha_composite(original.convert('RGBA'),layer).convert('RGB')
result.save(out / (stem+'.png'))
mask = np.asarray(layer)[:,:,3] == 0
assert np.array_equal(np.asarray(result)[mask], a[mask])
assert abs((box[2]-box[0])-(box[3]-box[1])) < 1e-9
embedded = base64.b64encode(src.read_bytes()).decode()
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="770" viewBox="0 0 1280 770">
<image width="1280" height="770" href="data:image/jpeg;base64,{embedded}"/>
<g fill="none" stroke="#005ad7" stroke-width="2">
<circle cx="{cx}" cy="{cy}" r="{r}"/>
<path d="M {cx-8} {cy} H {cx+8} M {cx} {cy-8} V {cy+8} M {cx} {cy} L {ex} {ey}"/>
</g><g fill="#005ad7" font-family="Arial" font-size="22">
<text x="{cx+10}" y="{cy+34}">O</text><text x="{cx-145}" y="{cy-83}">R ≈ 306,5 мм</text></g></svg>'''
(out/(stem+'.svg')).write_text(svg,encoding='utf-8')
data = dict(source=str(src),source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),
    pixel_center=[cx,cy],pixel_radius=r,pixel_rms=rms,point_count=len(points),
    upper_circle=upper.tolist(),lower_circle=lower.tolist(),
    center_separation_pixels=float(np.linalg.norm(upper[:2]-lower[:2])),
    radius_mm=radius_mm,metric_center_relative_to_leftmost_midpoint_mm=[radius_mm,0],
    basis='Circular end tangent to upper/lower parallel edges separated by 613 mm; approximate model, not manufacturer radius.',
    warning='Diagram dimensions do not share a uniform pixel scale. Overlay fits visual arc; physical circularity is an assumption.',
    equal_xy_diameter=True,unchanged_pixels_outside_annotation=True,output_png=stem+'.png')
(out/(stem+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(data,ensure_ascii=False,indent=2))

