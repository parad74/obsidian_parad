"""Read the delivered DXF/NC independently of the generator's internal geometry."""
from pathlib import Path
import math, re, sys, json
out = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(out.parent/'outvanna/work/python_packages'))
import ezdxf
from shapely.geometry import Polygon

reports = {}
for path in [out/'vanna2_contours_mm.dxf',out/'vanna2_dimensioned_mm.dxf',
             out/'cnc/geometry/vanna2_sheet_toolpaths_mm.dxf']:
    doc = ezdxf.readfile(path)
    assert doc.units == 4
    outline, = doc.modelspace().query('LWPOLYLINE[layer=="OUTER_NOMINAL"]')
    assert outline.closed and set(outline.get_points('xy')) == {
        (0,1722),(0,8),(25,8),(25,0),(810,0),(810,1730),(25,1730),(25,1722)}
    contour, = doc.modelspace().query('LWPOLYLINE[layer=="INNER_R315"]')
    assert contour.closed and len(contour)==4
    arcs = []; lines = []
    for entity in contour.virtual_entities():
        if entity.dxftype() == 'ARC':
            arc=entity.dxf
            assert math.isclose(arc.radius,315,abs_tol=1e-8)
            assert math.isclose((arc.end_angle-arc.start_angle)%360,180,abs_tol=1e-8)
            arcs.append(tuple(round(t,6) for t in (arc.center.x,arc.center.y)))
        else:
            assert entity.dxftype()=='LINE'
            start,end=entity.dxf.start,entity.dxf.end
            assert start.x==end.x and math.isclose(start.distance(end),975,abs_tol=1e-7)
            lines.append(start.x)
    assert set(arcs)=={(405,377.5),(405,1352.5)} and set(lines)=={90,720}
    reports[path.name]='two R315 semicircles, two tangent lines 975 mm, two 8 x 25 notches'

nc=(out/'cnc/nc/VANNA2_R315_D4_CUT.nc').read_text('ascii')
assert nc.count('M3 S16000\nG04 P5000\n')==1
assert nc.strip().endswith('M5\nG0 X0.000 Y0.000 Z45.000\nM30\n%')
section=nc.split('(INNER)\n')[1].split('(OUTER)')[0]
def axis_error(x,y):
    center_y=max(377.5,min(y,1352.5))
    return abs(math.hypot(x-405,y-center_y)-313)
errors=[]
for line in section.splitlines():
    m=re.fullmatch(r'G1 X([-\d.]+) Y([-\d.]+) Z0\.000 F800\.000',line)
    if not m: continue
    x,y=map(float,m.groups())
    if y>=869 and x>92 and abs(y-869.5)<.001:continue
    errors.append(axis_error(x,y))
    if len(errors)>1 and 'prev' in locals():
        errors.append(axis_error((x+prev[0])/2,(y+prev[1])/2))
    prev=(x,y)
assert len(errors)>1000 and max(errors)<.004
for filename, spinning in [('CHECK_DWELL_5S_NO_MOTION.nc',False),('CHECK_SPINDLE_16000_5S_NO_MOTION.nc',True)]:
    program=(out/'cnc/test_checks'/filename).read_text('ascii')
    commands=[s for s in program.splitlines() if s and s!='%' and not s.startswith('(')]
    assert commands==(['M5','M3 S16000','G04 P5000','M5','M30'] if spinning else ['M5','G04 P5000','M30'])
reports.update(sampled_cut_axis_max_error_mm=max(errors),sample_count=len(errors),test_programs='verified')
(out/'cnc/data/r315_readback.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
print(reports)
