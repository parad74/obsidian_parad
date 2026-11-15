"""Read the delivered DXF/NC independently of the generator's internal geometry."""
from pathlib import Path
import math, re, sys, json
out = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(out.parent/'outvanna/work/python_packages'))
import ezdxf


# Compare the two nominal DXFs in work coordinates. With the same center
# segment, subtracting 11 from the capsule radius is a uniform normal inset.
previous = ezdxf.readfile(out.parent/'outvanna2/vanna2_contours_mm.dxf')
previous_inner, = previous.modelspace().query('LWPOLYLINE[layer=="INNER_R315"]')
def primitives(contour):
    arcs, lines = [], []
    for e in contour.virtual_entities():
        if e.dxftype() == 'ARC':
            arcs.append((tuple(e.dxf.center), e.dxf.start_angle, e.dxf.end_angle, e.dxf.radius))
        else:
            lines.append((tuple(e.dxf.start), tuple(e.dxf.end)))
    return arcs, lines
old_arcs, old_lines = primitives(previous_inner)
reports = {}
for path in [out/'frame11_contours_mm.dxf',out/'frame11_dimensioned_mm.dxf',
             out/'cnc/geometry/frame11_sheet_toolpaths_mm.dxf']:
    doc = ezdxf.readfile(path)
    assert doc.units == 4
    outline, = doc.modelspace().query('LWPOLYLINE[layer=="OUTER_NOMINAL"]')
    assert outline.closed and set(outline.get_points('xy')) == {
        (0,1722),(0,8),(25,8),(25,0),(810,0),(810,1730),(25,1730),(25,1722)}
    contour, = doc.modelspace().query('LWPOLYLINE[layer=="INNER_R304"]')
    assert contour.closed and len(contour)==4
    arcs = []; lines = []
    for entity in contour.virtual_entities():
        if entity.dxftype() == 'ARC':
            arc=entity.dxf
            assert math.isclose(arc.radius,304,abs_tol=1e-8)
            assert math.isclose((arc.end_angle-arc.start_angle)%360,180,abs_tol=1e-8)
            arcs.append(tuple(round(t,6) for t in (arc.center.x,arc.center.y)))
        else:
            assert entity.dxftype()=='LINE'
            start,end=entity.dxf.start,entity.dxf.end
            assert start.x==end.x and math.isclose(start.distance(end),975,abs_tol=1e-7)
            lines.append(start.x)
    assert set(arcs)=={(405,377.5),(405,1352.5)} and set(lines)=={101,709}
    new_arcs, new_lines = primitives(contour)
    assert len(old_arcs) == len(new_arcs) == len(old_lines) == len(new_lines) == 2
    for old_arc, new_arc in zip(old_arcs, new_arcs):
        assert old_arc[:3] == new_arc[:3] and math.isclose(old_arc[3] - new_arc[3], 11)
    for old_line, new_line in zip(old_lines, new_lines):
        for p0, p1 in zip(old_line, new_line):
            assert p0[1:] == p1[1:] and math.isclose(abs(p1[0]-405), abs(p0[0]-405)-11)
    outer_old, = previous.modelspace().query('LWPOLYLINE[layer=="OUTER_NOMINAL"]')
    assert list(outline.get_points('xyb')) == list(outer_old.get_points('xyb'))
    reports[path.name]='two R304 semicircles, two tangent lines 975 mm, two 8 x 25 notches'

nc=(out/'cnc/nc/VANNA11_R304_D4_CUT.nc').read_text('ascii')
assert nc.count('M3 S16000\nG04 P5000\n')==1
assert nc.strip().endswith('M5\nG0 X0.000 Y0.000 Z45.000\nM30\n%')
section=nc.split('(INNER)\n')[1].split('(OUTER)')[0]
def axis_error(x,y):
    center_y=max(377.5,min(y,1352.5))
    return abs(math.hypot(x-405,y-center_y)-302)
errors=[]
for line in section.splitlines():
    m=re.fullmatch(r'G1 X([-\d.]+) Y([-\d.]+) Z0\.000 F800\.000',line)
    if not m: continue
    x,y=map(float,m.groups())
    if y>=869 and x>103 and abs(y-869.5)<.001:continue
    errors.append(axis_error(x,y))
    if len(errors)>1 and 'prev' in locals():
        errors.append(axis_error((x+prev[0])/2,(y+prev[1])/2))
    prev=(x,y)
assert len(errors)>1000 and max(errors)<.004
for filename, spinning in [('CHECK_DWELL_5S_NO_MOTION.nc',False),('CHECK_SPINDLE_16000_5S_NO_MOTION.nc',True)]:
    program=(out/'cnc/test_checks'/filename).read_text('ascii')
    commands=[s for s in program.splitlines() if s and s!='%' and not s.startswith('(')]
    assert commands==(['M5','M3 S16000','G04 P5000','M5','M30'] if spinning else ['M5','G04 P5000','M30'])
reports.update(inward_offset_vs_PARAD_027_mm=11, outer_matches_PARAD_027=True, sampled_cut_axis_max_error_mm=max(errors),sample_count=len(errors),test_programs='verified')
(out/'cnc/data/r304_readback.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
print(reports)
