from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
from scipy.optimize import least_squares
OUT=Path(__file__).resolve().parent
SOURCE=OUT.parent/'invanna2/33.jpg'
im=np.asarray(Image.open(SOURCE).convert('RGB'))
pts=[]
for y in range(211,601):
    if 395<=y<=415:continue
    row=im[y,150:345]
    dark=np.max(row,axis=1)<105
    indices=np.flatnonzero(dark)
    if len(indices):
        first=indices[0];run=[first]
        for k in indices[1:]:
            if k-run[-1]>1:break
            run.append(k)
        if len(run)<=10:pts.append([150+float(np.mean(run)),float(y)])
pts=np.array(pts)
def fit(points):
    def residual(p):return np.linalg.norm(points-p[:2],axis=1)-p[2]
    sol=least_squares(residual,[365,406,200],loss='soft_l1',f_scale=1)
    e=residual(sol.x)
    return dict(center=sol.x[:2].tolist(),radius=float(sol.x[2]),rms=float(np.sqrt(np.mean(e**2))),max_error=float(np.max(np.abs(e))),n=len(points))
pixel={k:fit(q) for k,q in [('one',pts),('upper',pts[pts[:,1]<395]),('lower',pts[pts[:,1]>415])]}
# Pixel extents measured at the black boundary center; do not assume all dimensions share a scale.
sx=1583/(1155-166.5);sy=613/(605.5-206.5)
metric_pts=np.column_stack(((pts[:,0]-166.5)*sx,(405.999999-pts[:,1])*sy))
metric={k:fit(q) for k,q in [('one',metric_pts),('upper',metric_pts[pts[:,1]<395]),('lower',metric_pts[pts[:,1]>415])]}
result=dict(source=str(SOURCE),sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    pixel_origin='top-left image; x right, y down',metric_origin='leftmost opening point at mid-height; x right, y up',
    scales_mm_per_pixel=dict(inner_x=sx,inner_y=sy,outer_x=1730/(1191-130),outer_y=810/(642-170)),
    pixel=pixel,metric_from_inner_dimensions=metric,semicircle_if_height_is_diameter=dict(radius_mm=613/2,center_mm=[613/2,0]),
    green_chord_x_pixel=350,warning='No single consistent image scale; metric fitted circles are approximate, not manufacturing dimensions.')
(OUT/'fit_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
np.savetxt(OUT/'boundary_points_pixel.csv',pts,delimiter=',',header='x_pixel,y_pixel',comments='')
print(json.dumps(result,ensure_ascii=False,indent=2))
