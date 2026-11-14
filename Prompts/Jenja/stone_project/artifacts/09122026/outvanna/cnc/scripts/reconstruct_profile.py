"""Reconstruct a symmetric opening from the supplied schematic, not a certified radius."""
from pathlib import Path
import json, hashlib
import numpy as np
from PIL import Image, ImageDraw
from scipy.optimize import least_squares

OUT = Path(__file__).resolve().parents[2]
SOURCE = OUT.parent / 'invanna/photo_2026-11-06_20-20-39.jpg'

def reconstruct():
    im = np.asarray(Image.open(SOURCE).convert('RGB'))
    # Inner black boundary in the supplied 855 x 496 image; ignore red dimension text.
    assert im.shape[:2] == (496, 855)
    observations = []
    for y in range(132, 390):
        if 257 <= y <= 271:  # horizontal red dimension arrow
            continue
        row = im[y]
        white = np.all(row > 242, axis=1)
        left = next((x for x in range(109, 275) if white[x:x+4].all()), None)
        right = next((x for x in range(769, 600, -1) if white[x-3:x+1].all()), None)
        if left is not None and right is not None:
            # Symmetrize top/bottom and left/right; enforce dimensions independently of raster scale.
            v = abs((y - 260.5) / 134.5)
            if .08 < v < .94:
                inset = ((left - 107) + (771 - right)) / 2 * 1605 / 664
                observations.append((v, inset))
    data = np.array(observations)
    def residual(p):
        rx, n = p
        return rx * (1 - np.maximum(0, 1-data[:,0]**n)**(1/n)) - data[:,1]
    fit = least_squares(residual, [325, 2], bounds=([220, 1.6], [470, 3]), loss='soft_l1', f_scale=2)
    rx, n = map(float, fit.x)
    # Superellipse caps joined to straight top/bottom edges, preserving horizontal and vertical tangency.
    points = []
    for side in (1, -1):
        cx = 1730-62.5-rx if side == 1 else 62.5+rx
        for a in np.linspace(-np.pi/2, np.pi/2, 513) if side == 1 else np.linspace(np.pi/2, 3*np.pi/2, 513):
            co, si = np.cos(a), np.sin(a)
            points.append([cx+rx*np.sign(co)*abs(co)**(2/n), 405+315*np.sign(si)*abs(si)**(2/n)])
    # Exact cardinal dimensions remove floating-point noise.
    outer = [[8,0],[1722,0],[1722,25],[1730,25],[1730,810],[0,810],[0,25],[8,25]]
    params = dict(date='2026-11-06', units='mm', quantity=1,
        outer_size=[1730,810], opening_size=[1605,630], centered=True,
        corner_notches=[8,25], sheet=[1220,2710,5], origin_from_sheet=[50,50],
        transform='X=y, Y=1730-x (rotation, no reflection)',
        tool_diameter=4, spindle_rpm=16000, xy_feed=800, z_feed=100,
        safe_z=45, approach_z=7, cut_levels=[2.5,0], tab_width_min=5, tab_height=1,
        tabs_per_contour=1, entry_hole_diameter=8, dwell_seconds=5,
        reconstruction=dict(type='symmetric superellipse end caps with straight sides',
            cap_horizontal_semiaxis=rx, cap_vertical_semiaxis=315, exponent=n,
            rms_raster_fit_mm=float(np.sqrt(np.mean(residual(fit.x)**2))),
            sample_count=len(data), manufacturing_accuracy=None,
            limitation='Shape reconstructed from schematic with user approval; not manufacturer radius data.'),
        source=str(SOURCE), source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        outer_original=outer, inner_original=points)
    (OUT/'cnc/data').mkdir(parents=True, exist_ok=True)
    (OUT/'cnc/data/parameters.json').write_text(json.dumps(params,ensure_ascii=False,indent=2),encoding='utf-8')
    # Overlay on a separate copy; the supplied image is unchanged.
    overlay=Image.open(SOURCE).convert('RGB')
    draw=ImageDraw.Draw(overlay)
    pix=[(107+(x-62.5)*664/1605, 395-(y-90)*269/630) for x,y in points]
    draw.line(pix+[pix[0]],fill=(0,100,230),width=2)
    overlay.save(OUT/'cnc/data/profile_overlay.png')
    print(json.dumps(params['reconstruction'],ensure_ascii=False))
    return params

if __name__=='__main__': reconstruct()
