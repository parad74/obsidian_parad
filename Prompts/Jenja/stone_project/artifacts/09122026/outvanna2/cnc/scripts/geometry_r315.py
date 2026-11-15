"""Approved symmetric opening in drawing coordinates (X right, Y up, millimetres)."""
import hashlib
import json
import math
from pathlib import Path

out = Path(__file__).resolve().parents[2]
source = out.parent / 'invanna2/photo_2026-11-06_20-17-19.jpg'
overlay = out / 'symmetric_frame_r315_dimensioned.png'
width, height = 1730, 810
length, diameter = 1605, 630
radius = diameter / 2
margin = (width - length) / 2
centers = [[margin + radius, height/2], [width-margin-radius, height/2]]
assert centers == [[377.5,405],[1352.5,405]]
outer = [[8,0],[1722,0],[1722,25],[1730,25],[1730,810],[0,810],[0,25],[8,25]]
inner = []
segments = 512
for (cx,cy), start in [(centers[1],-90),(centers[0],90)]:
    for step in range(segments+1):
        angle = math.radians(start+180*step/segments)
        inner.append([round(cx+radius*math.cos(angle),10), round(cy+radius*math.sin(angle),10)])

params = dict(date='2026-11-15', catalog_id='PARAD-027', units='mm', quantity=1,
    outer_size=[width,height], opening_size=[length,diameter], radius_mm=radius, centered=True,
    centers_drawing=centers, tangent_length_mm=centers[1][0]-centers[0][0], corner_notches=[8,25],
    sheet=[1220,2710,5], origin_from_sheet=[50,50], transform='X=y, Y=1730-x',
    tool_diameter=4, spindle_rpm=16000, xy_feed=800, z_feed=100, safe_z=45, approach_z=7,
    cut_levels=[2.5,0], tab_width_min=5, tab_height=1, tabs_per_contour=1,
    entry_hole_diameter=8, dwell_seconds=5, source='../invanna2/'+source.name, overlay=overlay.name,
    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    overlay_sha256=hashlib.sha256(overlay.read_bytes()).hexdigest(),
    segments_per_semicircle_nc=segments, chord_sagitta_mm=radius*(1-math.cos(math.pi/(2*segments))),
    outer_original=outer, inner_original=inner)
(out/'cnc/data/parameters.json').write_text(json.dumps(params, indent=2),encoding='utf-8')
