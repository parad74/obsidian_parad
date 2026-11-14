"""Generate and independently parse the calculated Vanna NC. Never controls a machine."""
from pathlib import Path
import sys, json, math, re, csv, hashlib
OUT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(OUT/'work/python_packages'))
import numpy as np
import ezdxf
from shapely.geometry import Polygon, Point, LineString, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union, substring

P=json.loads((OUT/'cnc/data/parameters.json').read_text(encoding='utf-8'))
G=OUT/'cnc/geometry'; G.mkdir(parents=True,exist_ok=True)
N=OUT/'cnc/nc'; N.mkdir(exist_ok=True)
D=OUT/'cnc/data'
transform=lambda pts:[(float(y),float(1730-x)) for x,y in pts]
outer=Polygon(transform(P['outer_original']))
inner=Polygon(transform(P['inner_original']))
frame=outer.difference(inner)
assert outer.is_valid and inner.is_valid and outer.contains(inner)
assert outer.bounds==(0.,0.,810.,1730.)
assert np.allclose(inner.bounds,[90,62.5,720,1667.5],atol=1e-8)
sheet=box(-50,-50,1170,2660)
# Offset the tool center; external re-entrant corners necessarily retain R2 with D4.
external=orient(outer.buffer(2,quad_segs=64,join_style='round'),sign=1)
internal=orient(inner.buffer(-2,quad_segs=64,join_style='round'),sign=-1)
effective_outer=external.buffer(-2,quad_segs=64)
effective_frame=effective_outer.difference(inner)
tabs=[box(90,862.5,94,867.5),box(-4,862.5,0,867.5)]
holes=[]; plans=[]; motions=[]
pos=[0.,0.,45.]
def move(code,xyz,feed=None,role='',contour=''):
    global pos
    xyz=list(map(float,xyz))
    motions.append(dict(code=code,start=pos[:],end=xyz,feed=feed,role=role,contour=contour))
    pos=xyz

def ring_part(ring,s0,s1):
    length=ring.length
    while s0<0: s0+=length;s1+=length
    s0%=length
    span=s1-s0 if s1>=s0 else s1+length-s0
    # Caller supplies absolute positive span independently below.
    return substring(ring,s0,s1)

def span_points(ring,start,distance):
    length=ring.length; start%=length; stop=start+distance
    if stop<=length+1e-8:
        return list(substring(ring,start,min(stop,length)).coords)
    a=list(substring(ring,start,length).coords)
    b=list(substring(ring,0,stop-length).coords)
    return a+b[1:]

for index,(name,poly,axis_x,hole_dx) in enumerate([('INNER',internal,92,6),('OUTER',external,-2,-6)]):
    ring=LineString(poly.exterior.coords)
    s=ring.project(Point(axis_x,865))
    main=span_points(ring,s+4.5,ring.length-9)
    bridge=span_points(ring,s-4.5,9)
    assert math.dist(main[0],bridge[-1])<1e-6
    assert math.dist(main[-1],bridge[0])<1e-6
    hole=(main[0][0]+hole_dx,main[0][1]); holes.append(hole)
    assert Point(hole).buffer(4).intersection(frame).area<1e-7
    for z in (2.5,0):
        move('G0',[*pos[:2],45],role='retract',contour=name)
        move('G0',[*hole,45],role='travel',contour=name)
        move('G0',[*hole,7],role='approach_hole',contour=name)
        move('G1',[*hole,z],100,'plunge_hole',name)
        move('G1',[*main[0],z],800,'lead_in',name)
        for p in main[1:]: move('G1',[*p,z],800,'contour',name)
        tab_z=max(z,1)
        if tab_z!=z:move('G1',[*main[-1],tab_z],100,'tab_raise',name)
        for p in bridge[1:]:move('G1',[*p,tab_z],800,'tab_cross',name)
        move('G1',[*hole,tab_z],800,'lead_out',name)
        move('G0',[*hole,45],role='retract',contour=name)
    plans.append(dict(name=name,hole=hole,tab_center=[0 if name=='OUTER' else 90,865],
                      axis_tab_span_mm=9,path_length=ring.length,main=main,bridge=bridge))
move('G0',[0,0,45],role='home')

def f(v):return f'{0 if abs(v)<.0000001 else v:.3f}'
header=['%','(VANNA FRAME - CALCULATED CUT - Z0 TABLE - TOOL D4)',
        '(XY0 PART BOUNDING CORNER AT SHEET X50 Y50)',
        '(INNER THEN OUTER; ONE TAB 5MM MIN X 1MM EACH)',
        '(VERIFY HOLES CLAMPS Z0 DWELL AND AIR BEFORE CUT)',
        'G90','G21','G17','G40','G49','G80','M5','G0 Z45.000']
cut=header+['M3 S16000',f'G04 P{int(P["dwell_seconds"]*1000)}']
air=['%','(VANNA AIR XY ONLY - NO SPINDLE - ALL Z45)']+header[5:]
previous=''
for m in motions:
    if m['contour']!=previous and m['contour']:
        cut.append('('+m['contour']+')');air.append('('+m['contour']+')');previous=m['contour']
    if m['role']=='home':cut.append('M5')
    row=m['code']+' '+' '.join(k+f(v) for k,v in zip('XYZ',m['end']))
    if m['feed'] is not None:row+=' F'+f(m['feed'])
    cut.append(row)
    if math.dist(m['start'][:2],m['end'][:2])>1e-9:
        air.append(m['code']+' X'+f(m['end'][0])+' Y'+f(m['end'][1])+' Z45.000'+(' F800.000' if m['code']=='G1' else ''))
cut+=['M30','%'];air+=['M5','M30','%']
for name,rows in [('VANNA_DVP_D4_CUT.nc',cut),('VANNA_DVP_AIR_XY.nc',air)]:
    (N/name).write_bytes(('\r\n'.join(rows)+'\r\n').encode('ascii'))

# Read back written coordinates; geometric checks use this rounded NC, not source paths.
def parse(path,is_air=False):
    xyz=[0.,0.,45.]; moves=[]; modes=set(); spindle=False; dwell=False;rpm=None; ended=False
    for raw in path.read_text('ascii').splitlines():
        row=re.sub(r'\([^)]*\)','',raw).strip()
        if row in ('','%'):continue
        words=re.findall(r'([A-Z])([-+]?\d+(?:\.\d*)?)',row)
        assert ''.join(k+v for k,v in words)==re.sub(r'\s','',row),row
        w={k:float(v) for k,v in words}; g=int(w['G']) if 'G' in w else None
        assert set(w)<=set('GMSXYZFP')
        if g in (90,21,17,40,49,80):modes.add(g);continue
        if 'M' in w:
            if w['M']==3:
                assert not is_air;spindle=True;rpm=w['S'];assert rpm==16000
            elif w['M']==5:spindle=False
            elif w['M']==30:assert not spindle and xyz==[0.,0.,45.];ended=True
            else:raise AssertionError(row)
            continue
        if g==4:assert not is_air and spindle and w['P']==P['dwell_seconds']*1000;dwell=True;continue
        assert g in (0,1) and modes=={90,21,17,40,49,80},row
        end=[w.get(k,xyz[i]) for i,k in enumerate('XYZ')]
        assert min(end[2],xyz[2])>=0
        xy=math.dist(xyz[:2],end[:2]); dz=end[2]-xyz[2]
        if is_air:assert not spindle and 'S' not in w and end[2]==45
        elif g==0:
            if xy>1e-8:assert xyz[2]==end[2]==45
            if dz<0:assert xy<1e-8 and end[2]==7
        else:
            assert spindle and dwell and rpm==16000
            if dz<0:
                assert xy<1e-8 and xyz[2]==7 and end[2] in (2.5,0) and w['F']==100
                assert min(math.dist(end[:2],h) for h in holes)<.001
            elif dz>0:assert xy<1e-8 and xyz[2]==0 and end[2]==1 and w['F']==100
            else:assert w['F']==800 and end[2] in (0,1,2.5)
        moves.append(dict(code=g,start=xyz[:],end=end[:],feed=w.get('F')));xyz=end
    assert ended
    return moves
parsed=parse(N/'VANNA_DVP_D4_CUT.nc'); parsed_air=parse(N/'VANNA_DVP_AIR_XY.nc',True)
assert len(parsed)==len(motions)+1
for actual,expected in zip(parsed[1:],motions):
    assert actual['code']==int(expected['code'][1:])
    assert max(abs(a-b) for a,b in zip(actual['end'],expected['end']))<=.000501
cut_xy=[(m['code'],m['end'][:2]) for m in parsed if math.dist(m['start'][:2],m['end'][:2])>.00001]
air_xy=[(m['code'],m['end'][:2]) for m in parsed_air if math.dist(m['start'][:2],m['end'][:2])>.00001]
assert cut_xy==air_xy
sweeps=[]; through=[]; upper=[]; minutes=0; plunges=0
for m in parsed:
    if m['code']!=1:continue
    minutes+=math.dist(m['start'],m['end'])/m['feed']
    xy=math.dist(m['start'][:2],m['end'][:2])
    if m['start'][2]==7 and m['end'][2] in (0,2.5):plunges+=1
    if xy>.00001:
        sw=LineString([m['start'][:2],m['end'][:2]]).buffer(2,quad_segs=32)
        sweeps.append(sw)
        if m['end'][2]==0:through.append(sw)
        if m['end'][2]<=1:upper.append(sw)
all_cut=unary_union(sweeps); through_cut=unary_union(through); upper_cut=unary_union(upper)
gouge=all_cut.intersection(frame.buffer(-.003)).area
assert gouge<.01,(gouge,'frame gouge')
assert sheet.contains(all_cut) and all(sheet.contains(Point(h).buffer(4)) for h in holes)
assert plunges==4
for tab in tabs:
    assert through_cut.intersection(tab.buffer(-.003)).area<.001
    assert tab.difference(upper_cut.buffer(.003)).area<.001
# At mid-height below the tabs there must remain a connected sheet: opening/part not freed.
remaining=sheet.difference(through_cut)
assert remaining.geom_type=='Polygon',remaining.geom_type
# Every nominal toolpath interval is covered at full depth except the explicit 9 mm center span.
through_tolerance=through_cut.buffer(.003)
for plan in plans:
    sample=LineString(plan['main'])
    for t in np.linspace(0,sample.length,1001):assert through_tolerance.contains(sample.interpolate(t))

def dxf(path,layout=False,dimensioned=False):
    doc=ezdxf.new('R2010');doc.units=4;ms=doc.modelspace()
    for name,color in [('OUTER_NOMINAL',7),('INNER_RECONSTRUCTED',3),('TOOL_AXIS',1),('HOLES_D8',30),('TABS_5x1',6),('SHEET',8),('TEXT',7),('EFFECTIVE_OUTER_R2',4)]:doc.layers.new(name,dxfattribs={'color':color})
    ms.add_lwpolyline(list(outer.exterior.coords)[:-1],close=True,dxfattribs={'layer':'OUTER_NOMINAL'})
    ms.add_lwpolyline(list(inner.exterior.coords)[:-1],close=True,dxfattribs={'layer':'INNER_RECONSTRUCTED'})
    if layout:
        ms.add_lwpolyline(list(sheet.exterior.coords)[:-1],close=True,dxfattribs={'layer':'SHEET'})
        for poly in (external,internal):ms.add_lwpolyline(list(poly.exterior.coords)[:-1],close=True,dxfattribs={'layer':'TOOL_AXIS'})
        ms.add_lwpolyline(list(effective_outer.exterior.coords)[:-1],close=True,dxfattribs={'layer':'EFFECTIVE_OUTER_R2'})
        for i,h in enumerate(holes,1):
            ms.add_circle(h,4,dxfattribs={'layer':'HOLES_D8'})
            ms.add_text(f'H{i} D8',dxfattribs={'height':12,'layer':'TEXT'}).set_placement((h[0]+12,h[1]+12))
        for tab in tabs:ms.add_lwpolyline(list(tab.exterior.coords)[:-1],close=True,dxfattribs={'layer':'TABS_5x1'})
    if dimensioned:
        for a,b,base,ang in [((0,0),(810,0),(0,-90),0),((810,0),(810,1730),(900,0),90),((90,865),(720,865),(90,865),0),((405,62.5),(405,1667.5),(405,62.5),90)]:
            dim=ms.add_linear_dim(base=base,p1=a,p2=b,angle=ang,override={'dimtxt':16,'dimasz':10,'dimgap':5,'dimdec':1});dim.render()
        for i,line in enumerate(['VANNA 1730 x 810; OPENING 1605 x 630 CENTERED','BOTTOM CORNER NOTCHES 8 x 25; REMAINING 1714',
                                 'OPENING CURVE RECONSTRUCTED FROM SCHEMATIC','X = SOURCE Y; Y = 1730 - SOURCE X; MM',
                                 'NOMINAL CORNERS SHARP; D4 MACHINING LEAVES INTERNAL R2']):
            ms.add_text(line,dxfattribs={'height':12,'layer':'TEXT'}).set_placement((0,1830+25*i))
    doc.saveas(path)
    read=ezdxf.readfile(path);audit=read.audit();assert not audit.errors and not audit.fixes
    assert read.units==4
    return doc
dxf(OUT/'vanna_contours_mm.dxf');dxf(OUT/'vanna_dimensioned_mm.dxf',dimensioned=True)
dxf(G/'vanna_sheet_toolpaths_mm.dxf',layout=True)
doc=ezdxf.new('R2010');doc.units=4
for m in parsed:doc.modelspace().add_line(m['start'],m['end'],dxfattribs={'layer':'RAPID' if m['code']==0 else 'FEED'})
doc.saveas(G/'vanna_motion_XYZ.dxf');assert not ezdxf.readfile(G/'vanna_motion_XYZ.dxf').audit().errors
with (D/'holes_tabs.csv').open('w',encoding='utf-8-sig',newline='') as fp:
    wr=csv.writer(fp);wr.writerow(['type','contour','X_work_mm','Y_work_mm','X_sheet_mm','Y_sheet_mm','diameter_or_width_mm','residual_height_mm'])
    for i,p in enumerate(plans):
        x,y=p['hole'];wr.writerow(['hole',p['name'],round(x,3),round(y,3),round(x+50,3),round(y+50,3),8,''])
        x,y=p['tab_center'];wr.writerow(['tab',p['name'],x,y,x+50,y+50,5,1])
report=dict(status='PASS_STATIC_CHECKS',physical_test=False,actual_ArtCAM_export=False,
    outer_bounds=list(outer.bounds),inner_bounds=list(inner.bounds),notches=[8,25],
    source_sha256=P['source_sha256'],plunges=plunges,holes=holes,tabs=2,
    min_z=min(m['end'][2] for m in parsed),air_z=45,xy_air_matches_cut=True,
    frame_gouge_beyond_003mm_tolerance_mm2=gouge,
    remaining_sheet_components=1,tab_width_min=5,tab_axis_span=9,tab_height=1,
    external_concave_corner_radius=2,external_nominal_vs_effective_area_mm2=effective_outer.difference(outer).area,
    feed_minutes=minutes,dwell_seconds=P['dwell_seconds'],feed_plus_explicit_dwell_minutes=minutes+P['dwell_seconds']/60,
    total_cycle_minutes=None,move_count=len(parsed),
    limitations=['Schematic curve approximation, not certified bath fit','Clamps/holder/travel unmeasured',
                'Z0 table: no allowance below table; full release depends on flatness and zero accuracy',
                'One thin tab per contour is user choice; holding strength not validated',
                'A11S dwell and short-line handling require machine check'])
(D/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(D/'parsed_motion.json').write_text(json.dumps(parsed,indent=2),encoding='utf-8')
(D/'paths.json').write_text(json.dumps(plans,indent=2),encoding='utf-8')
hashes={str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [N/'VANNA_DVP_D4_CUT.nc',N/'VANNA_DVP_AIR_XY.nc',OUT/'vanna_contours_mm.dxf',OUT/'vanna_dimensioned_mm.dxf',G/'vanna_sheet_toolpaths_mm.dxf',G/'vanna_motion_XYZ.dxf']}
(D/'output_sha256.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
