"""PARAD-003: offline paths and explicitly non-cutting XY NC previews.
Run with the bundled Python; CAD and geometry dependencies are local to work.
This generator does not operate ArtCAM or a machine.
"""
from pathlib import Path
import sys, math, json, csv, hashlib, re, argparse
BASE=Path(__file__).resolve().parent
sys.path[:0]=[str(BASE/'cadlib'),str(BASE/'cnc_readable')]
import numpy as np
import ezdxf
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union

ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--output',type=Path)
ap.add_argument('--source-root',type=Path,default=Path(r'W:\obsidian\_parad\Prompts\Jenja\postprocessor'))
args=ap.parse_args()
ROOT=args.source_root
CAD=ROOT.parent/'stone_project/artifacts/09122026/out2'
OUT=args.output or BASE.parent
OUT.mkdir(parents=True,exist_ok=True)
for folder in ['nc_air_xy','geometry','data','postprocessors','scripts']:
    (OUT/folder).mkdir(exist_ok=True)
TAU=2*math.pi
def write(p,s): p.write_text(s,encoding='utf-8',newline='\n')
def js(p,d): write(p,json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def length(a,b):return math.dist(a,b)
def lerp(a,b,t):return tuple(x+(y-x)*t for x,y in zip(a,b))

def line(a,b):return dict(kind='line',start=list(a),end=list(b))
def arc(c,r,a,b):
    return dict(kind='arc',center=list(c),radius=r,a=a,b=b,
                start=[c[0]+r*math.cos(a),c[1]+r*math.sin(a)],
                end=[c[0]+r*math.cos(b),c[1]+r*math.sin(b)])
def seglen(s):return length(s['start'],s['end']) if s['kind']=='line' else s['radius']*abs(s['b']-s['a'])
def segpoint(s,t):
    if s['kind']=='line':return lerp(s['start'],s['end'],t)
    a=s['a']+(s['b']-s['a'])*t
    return (s['center'][0]+s['radius']*math.cos(a),s['center'][1]+s['radius']*math.sin(a))
def sample(segs,tol=.0002):
    pts=[]
    for s in segs:
        n=1 if s['kind']=='line' else max(2,math.ceil(abs(s['b']-s['a'])/(2*math.acos(1-tol/s['radius']))))
        pts.extend(segpoint(s,i/n) for i in range(n))
    return pts+[segs[-1]['end']]
def slice_path(segs,lo,hi):
    total=sum(seglen(s) for s in segs); result=[]
    for cycle in [0,1]:
        acc=cycle*total
        for s in segs:
            n=seglen(s);u=max(lo,acc);v=min(hi,acc+n)
            if v-u>1e-8:
                t0=(u-acc)/n;t1=(v-acc)/n
                result.append(line(segpoint(s,t0),segpoint(s,t1)) if s['kind']=='line' else arc(s['center'],s['radius'],s['a']+(s['b']-s['a'])*t0,s['a']+(s['b']-s['a'])*t1))
            acc+=n
    return result
def position_on_path(segs,p):
    acc=0
    for s in segs:
        if s['kind']=='line' and abs(length(s['start'],p)+length(p,s['end'])-seglen(s))<1e-6:
            return acc+length(s['start'],p)
        acc+=seglen(s)
    raise ValueError(p)

doc=ezdxf.readfile(CAD/'podoconnik_contour_mm.dxf')
poly=list(doc.modelspace().query('LWPOLYLINE'))
assert len(poly)==1 and poly[0].closed and doc.units==4
orig=[tuple(v[:2]) for v in poly[0].get_points()]
expected=[(0,0),(2100,0),(2100,50),(2050,50),(2050,270),(50,270),(50,50),(0,50)]
assert orig==expected,orig
transformed=[(y,2100-x) for x,y in orig]
stock=Polygon(transformed)
P=[(0,0),(50,0),(50,50),(270,50),(270,2050),(50,2050),(50,2100),(0,2100)]
assert stock.equals(Polygon(P)) and stock.area==545000

# Exact contour of the accepted DVP template, including two residual R2 corners.
dvp_final=[line((0,0),(50,0)),line((50,0),(50,48)),arc((52,48),2,math.pi,math.pi/2),
 line((52,50),(270,50)),line((270,50),(270,2050)),line((270,2050),(52,2050)),
 arc((52,2052),2,3*math.pi/2,math.pi),line((50,2052),(50,2100)),line((50,2100),(0,2100)),line((0,2100),(0,0))]
dvp_shape=Polygon(sample(dvp_final))
# Cutter-centre offset: round convex corners, intersect offset lines at concave corners.
dvp_loop=[line((0,-2),(50,-2)),arc((50,0),2,-math.pi/2,0),line((52,0),(52,48)),line((52,48),(270,48)),
 arc((270,50),2,-math.pi/2,0),line((272,50),(272,2050)),arc((270,2050),2,0,math.pi/2),
 line((270,2052),(52,2052)),line((52,2052),(52,2100)),arc((50,2100),2,0,math.pi/2),
 line((50,2102),(0,2102)),arc((0,2100),2,math.pi/2,math.pi),line((-2,2100),(-2,0)),arc((0,0),2,math.pi,3*math.pi/2)]
tabs=[dict(center=[25,0],axis=[1,0],normal=[0,-1]),
      dict(center=[270,2100/3],axis=[0,1],normal=[1,0]),
      dict(center=[270,4200/3],axis=[0,1],normal=[1,0]),
      dict(center=[25,2100],axis=[-1,0],normal=[0,1]),
      dict(center=[0,4200/3],axis=[0,-1],normal=[-1,0]),
      dict(center=[0,2100/3],axis=[0,-1],normal=[-1,0])]
for t in tabs:
    t['s']=position_on_path(dvp_loop,[t['center'][i]+2*t['normal'][i] for i in range(2)])
    t.update(width_min_mm=5,height_mm=5,centerline_skip_mm=9)
tabs.sort(key=lambda t:t['s'])
L=sum(map(seglen,dvp_loop)); holes=[]; dvp_sections=[]
for i,t in enumerate(tabs):
    nxt=tabs[(i+1)%6]['s']+(L if i==5 else 0)
    segs=slice_path(dvp_loop,t['s']+4.5,nxt-4.5)
    entry=segs[0]['start'];n=t['normal']
    hole=[entry[j]+6*n[j] for j in range(2)]
    holes.append(dict(id=i+1,x=hole[0],y=hole[1],sheet_x=hole[0]+50,sheet_y=hole[1]+50,diameter=8))
    dvp_sections.append([line(hole,entry)]+segs)

paths=[]
def path(op,name,segs,z,safe,feed,approach_z=None,feed_z=None,step=None,profile=None):
    paths.append(dict(operation=op,name=name,segments=segs,z=z,safe_z=safe,feed_xy=feed,
                      approach_z=approach_z,feed_z=feed_z,radial_step=step,profile=profile))
for depth in [2.5,.3]:
    for i,s in enumerate(dvp_sections):path('01_dvp',f'depth_{depth}_section_{i+1}',s,depth,45,800,7,100)

# All stone strokes follow the CCW outside-contour sense with CW spindle, conventional.
# Side end points X=63 keep a >=10 mm gap from a radius-3 cutter and the wing end X=50.
def pcd_u(d):
    k=d-3
    return [line((63,2100-k),(k,2100-k)),line((k,2100-k),(k,k)),line((k,k),(63,k))]
far=[line((283,2050),(273,2050)),arc((270,2050),3,0,math.pi/2),line((270,2053),(53,2053)),line((53,2053),(53,2113))]
near=[line((53,-13),(53,0)),line((53,0),(53,47)),line((53,47),(270,47)),arc((270,50),3,-math.pi/2,0),line((273,50),(283,50))]
pcd_widths=list(range(1,14))+[13.5]
for depth in [-1.5,-2.5]:
    path('02_pcd',f'depth_{depth}_far_nominal',far,depth,40,500,2,100,0,'nominal_edges')
    prev=0
    for d in pcd_widths:
        path('02_pcd',f'depth_{depth}_width_{d}',pcd_u(d),depth,40,500,2,100,d-prev,'HV_band');prev=d
    path('02_pcd',f'depth_{depth}_near_nominal',near,depth,40,500,2,100,0,'nominal_edges')

hv_steps=[1,3,5,7,9,11,13,13.5]
for i,q in enumerate(hv_steps):
    o=37-q
    segs=[line((97,2100+o),(-o,2100+o)),line((-o,2100+o),(-o,-o)),line((-o,-o),(97,-o))]
    path('03_hv_rough' if i<7 else '04_hv_finish',f'infeed_{q}',segs,0,70,292.5 if i<7 else 162.5,
         step=q-(hv_steps[i-1] if i else 0),profile='R13.5_D74')

def centerline(s):return LineString(sample(s))
def swept(s,r):return centerline(s).buffer(r,quad_segs=128)
def boundary_at(d):return Polygon([(d,d),(50,d),(50,50),(270,50),(270,2050),(50,2050),(50,2100-d),(d,2100-d)])
checks={}
# Shape changes caused by the accepted concave radii are explicit and limited to DVP.
checks['source']={'units':'mm','area_mm2':stock.area,'bbox_XY':[0,0,270,2100],
 'transform':'X=Y_CAD; Y=2100-X_CAD; Z=Z_CAD','rotation_determinant':1,
 'sha256':sha(CAD/'podoconnik_contour_mm.dxf')}
checks['dvp']={'accepted_inner_radius_mm':2,'max_corner_deviation_mm':2*(math.sqrt(2)-1),
 'area_added_by_R2_mm2_exact':2*(4-math.pi),'tabs':6,'tab_width_min_mm':5,
 'tab_width_at_nominal_wall_mm':9,'centerline_skip_mm':9,'holes':6,
 'final_bottom_z':.3,'tab_height':5}
tab_polys=[]
for t in tabs:
    c=np.array(t['center']);a=np.array(t['axis']);n=np.array(t['normal'])
    tab_polys.append(Polygon([c-2.5*a,c+2.5*a,c+2.5*a+4*n,c-2.5*a+4*n]))
cut_dvp=unary_union([swept(s,2) for s in dvp_sections]+[Point(h['x'],h['y']).buffer(4,quad_segs=128) for h in holes])
checks['dvp']['gouge_into_accepted_template_mm2']=cut_dvp.intersection(dvp_shape).area
checks['dvp']['bridge_intersection_mm2']=sum(cut_dvp.intersection(t).area for t in tab_polys)
assert checks['dvp']['gouge_into_accepted_template_mm2']<.02,checks['dvp']
assert checks['dvp']['bridge_intersection_mm2']<.001
sheet=box(-50,-50,1170,2660)
assert sheet.contains(cut_dvp)
checks['dvp']['holes_and_cut_inside_sheet']=True
checks['dvp']['slot_sweep_bounds']=list(cut_dvp.bounds)

target_band=stock.difference(boundary_at(13.5))
pcd_cut=unary_union([swept(p['segments'],3) for p in paths if p['operation']=='02_pcd' and p['z']==-2.5])
missing=target_band.difference(pcd_cut.buffer(.002))
over=pcd_cut.intersection(boundary_at(13.5).buffer(-.002))
checks['pcd']={'width_passes_per_depth':14,'depth_levels':2,'profile_strokes':28,'nominal_edge_strokes':4,
 'target_band_area_mm2':target_band.area,'unremoved_band_area_mm2_tolerance_002':missing.area,
 'overcut_final_top_mm2_tolerance_002':over.area,'tolerance_of_sweep_check_mm':.002,
 'PCD_bottom_above_stone_bottom_mm':27.5,'HV_top_mm':28,'vertical_overlap_mm':.5}
assert missing.area<.01 and over.area<.01,checks['pcd']
hvfinal=[p for p in paths if p['operation']=='04_hv_finish'][0]
errors=[]
for z in np.linspace(0,27,109):
    d=13.5-math.sqrt(max(0,13.5**2-(z-13.5)**2))
    rr=37-math.sqrt(max(0,13.5**2-(z-13.5)**2))
    remain=stock.difference(swept(hvfinal['segments'],rr))
    target=boundary_at(d)
    errors.append(remain.symmetric_difference(target).area)
checks['hv']={'profile_radius':13.5,'max_diameter':74,'groove_min_radius':23.5,'radial_total':13.5,
 'rough_passes':7,'finish_passes':1,'cumulative_infeeds':hv_steps,
 'offsets_from_nominal_edge':[37-q for q in hv_steps],'working_tool_bottom_Z':0,
 'cross_sections_checked':109,'max_symmetric_difference_area_mm2':max(errors),
 'sharp_miter_path':True,'terminal_center_X':97,'minimum_cutter_exit_clearance_mm':min(Point(p['segments'][-1]['end']).distance(stock)-37 for p in paths if p['operation'].startswith(('03','04')))}
assert max(errors)<.15,checks['hv']
assert checks['hv']['minimum_cutter_exit_clearance_mm']>=10
# Check every stone start and end at work height: full cutting disk is outside stock.
clearances=[]
for p in paths:
    if p['operation']=='01_dvp':continue
    r=3 if p['operation']=='02_pcd' else 37
    for pt in [p['segments'][0]['start'],p['segments'][-1]['end']]:
        clearances.append((p['name'],Point(pt).distance(stock)-r))
assert min(v for _,v in clearances)>=9.999,clearances
checks['stone_entry_exit_min_clearance_mm']=min(v for _,v in clearances)
checks['checks_not_performed']=['ArtCAM 2011/2018 actual export/import','actual A11S command and F/S settings',
 'tool holder and shank envelope','clamps/support locations and heights','machine travel in work coordinates',
    'physical dry run','actual cutting/tool wear/finish accuracy','permission to exceed tool max RPM']

stats={}
for op in ['01_dvp','02_pcd','03_hv_rough','04_hv_finish']:
    group=[p for p in paths if p['operation']==op]
    xy=sum(sum(map(seglen,p['segments'])) for p in group)
    zfeed=sum(abs(p['approach_z']-p['z'])/p['feed_z'] for p in group if p['feed_z'])
    fastdist=0; prev=(0,0,group[0]['safe_z'])
    for p in group:
        start=(*p['segments'][0]['start'],p['safe_z'])
        fastdist+=length(prev,start)
        approach=p['approach_z'] if p['approach_z'] is not None else p['z']
        fastdist+=p['safe_z']-approach
        fastdist+=p['safe_z']-p['z']
        prev=(*p['segments'][-1]['end'],p['safe_z'])
    if op in ['01_dvp','02_pcd']:fastdist+=length(prev,(0,0,group[0]['safe_z']))
    points=[pt for p in group for s in p['segments'] for pt in sample([s])]
    ar=np.array(points)
    stats[op]={'strokes':len(group),'XY_feed_path_mm':xy,'XY_feed_minutes':xy/group[0]['feed_xy'],
      'Z_feed_minutes':zfeed,'feed_motion_minutes':xy/group[0]['feed_xy']+zfeed,
      'rapid_path_mm':fastdist,'center_bounds_xy':[ar.min(axis=0).tolist(),ar.max(axis=0).tolist()],
      'safe_z':group[0]['safe_z'],'full_cycle_minutes':None,
      'time_note':'Ideal programmed feed time; no acceleration/corner slowdowns, setup, or machine rapid-time estimate.'}

# Four planar NC previews only. Deliberate flattening to safe height, not a production post.
def fmt(v):return f'{0 if abs(v)<.0000001 else v:.3f}'
for op,st in stats.items():
    group=[p for p in paths if p['operation']==op]
    rows=['%','(PARAD003 AIR XY ONLY - NO CUTTING - SPINDLE OFF)',
          '(WORK Z0: '+('TABLE' if op=='01_dvp' else 'STONE TOP' if op=='02_pcd' else 'STONE BOTTOM')+')',
          '(ALL Z MOVES FLATTENED TO SAFE HEIGHT; NOT A CUTTING PROGRAM)',
          '(VERIFY WORK OFFSET TRAVEL CLAMPS AND CONTROLLER BEFORE PHYSICAL USE)',
          'G90','G21','G17','M5','G0 Z'+fmt(st['safe_z'])]
    for p in group:
        rows+=['('+p['name'].upper()+')','G0 X'+fmt(p['segments'][0]['start'][0])+' Y'+fmt(p['segments'][0]['start'][1])]
        for s in p['segments']:
            code='G1' if s['kind']=='line' else 'G3' if s['b']>s['a'] else 'G2'
            row=code+' X'+fmt(s['end'][0])+' Y'+fmt(s['end'][1])
            if s['kind']=='arc':row+=' I'+fmt(s['center'][0]-s['start'][0])+' J'+fmt(s['center'][1]-s['start'][1])
            rows.append(row+' F'+str(p['feed_xy']))
    if op in ['01_dvp','02_pcd']:rows.append('G0 X0.000 Y0.000')
    rows+=['M5','M30','%']
    (OUT/'nc_air_xy'/f'{op}_AIR_XY.nc').write_bytes(('\r\n'.join(rows)+'\r\n').encode('ascii'))

def dxf_file(name,layers):
    d=ezdxf.new('R2000');d.units=4;d.header['$MEASUREMENT']=1
    m=d.modelspace()
    for i,(label,items) in enumerate(layers):
        d.layers.new(label,dxfattribs={'color':(i%6)+1})
        for segs,z in items:
            for s in segs:
                if s['kind']=='line':m.add_line((*s['start'],z),(*s['end'],z),dxfattribs={'layer':label})
                elif s['b']>=s['a']:m.add_arc((*s['center'],z),s['radius'],math.degrees(s['a'])%360,math.degrees(s['b'])%360,dxfattribs={'layer':label})
                else:m.add_arc((*s['center'],z),s['radius'],math.degrees(s['b'])%360,math.degrees(s['a'])%360,dxfattribs={'layer':label})
    d.saveas(OUT/'geometry'/name)
    chk=ezdxf.readfile(OUT/'geometry'/name).audit();assert not chk.errors and not chk.fixes
nominal=[line(P[i],P[(i+1)%len(P)]) for i in range(len(P))]
dxf_file('part_contours_Y2100.dxf',[('STONE_NOMINAL',[(nominal,0)]),('DVP_ACCEPTED_R2',[(dvp_final,0)])])
for filename,segs in [('stone_contour_Y2100.dxf',nominal),('dvp_contour_R2_Y2100.dxf',dvp_final)]:
    d=ezdxf.new('R2000');d.units=4
    verts=[(*s['start'],math.tan((s['b']-s['a'])/4) if s['kind']=='arc' else 0) for s in segs]
    d.modelspace().add_lwpolyline(verts,format='xyb',close=True)
    d.saveas(OUT/'geometry'/filename)
motion_plans={}
for op in stats:
    group=[p for p in paths if p['operation']==op]
    layers=[('NOMINAL_STOCK',[(nominal,0)])]+[(f'PATH_{i+1:02d}',[(p['segments'],p['z'])]) for i,p in enumerate(group)]
    dxf_file(op+'_center_paths.dxf',layers)
    # Explicit three-dimensional ideal motion plan, kept as data rather than cutting NC.
    planned=[];current=[0.,0.,group[0]['safe_z']]
    def move(code,end,role,feed=None,ij=None):
        global current
        planned.append(dict(code=code,start=current.copy(),end=list(end),role=role,feed=feed,ij=ij))
        current=list(end)
    for p in group:
        a=p['segments'][0]['start'];safe=p['safe_z']
        move('G0',[a[0],a[1],safe],'air_return')
        az=p['approach_z'] if p['approach_z'] is not None else p['z']
        move('G0',[a[0],a[1],az],'clear_vertical_approach')
        if p['feed_z']:move('G1',[a[0],a[1],p['z']],'controlled_descent',p['feed_z'])
        for s in p['segments']:
            code='G1' if s['kind']=='line' else 'G3' if s['b']>s['a'] else 'G2'
            ij=[s['center'][i]-s['start'][i] for i in range(2)] if s['kind']=='arc' else None
            move(code,[*s['end'],p['z']],'feed_path',p['feed_xy'],ij)
        move('G0',[current[0],current[1],safe],'retract_after_exit')
    if op in ['01_dvp','02_pcd']:move('G0',[0,0,group[0]['safe_z']],'return_work_XY0')
    motion_plans[op]=planned
    d=ezdxf.new('R2000');d.units=4;m=d.modelspace()
    for v in planned:
        layer='AIR' if v['code']=='G0' else 'FEED'
        if v['code'] in ['G0','G1']:m.add_line(v['start'],v['end'],dxfattribs={'layer':layer})
        else:
            c=[v['start'][i]+v['ij'][i] for i in range(2)];r=math.dist(c,v['start'][:2])
            a=math.degrees(math.atan2(v['start'][1]-c[1],v['start'][0]-c[0]))%360
            b=math.degrees(math.atan2(v['end'][1]-c[1],v['end'][0]-c[0]))%360
            m.add_arc((*c,v['start'][2]),r,a if v['code']=='G3' else b,b if v['code']=='G3' else a,dxfattribs={'layer':layer})
    d.saveas(OUT/'geometry'/f'{op}_planned_3d_motion.dxf')
d=ezdxf.new('R2000');d.units=4;m=d.modelspace()
m.add_lwpolyline(P,close=True,dxfattribs={'layer':'PART_NOMINAL'})
m.add_lwpolyline([(-50,-50),(1170,-50),(1170,2660),(-50,2660)],close=True,dxfattribs={'layer':'SHEET'})
for h in holes:
    m.add_circle((h['x'],h['y']),4,dxfattribs={'layer':'PRE_DRILL_D8'})
    m.add_text(str(h['id']),dxfattribs={'height':5,'insert':(h['x']+6,h['y']+6),'layer':'LABELS'})
for t,b in zip(tabs,tab_polys):m.add_lwpolyline(list(b.exterior.coords)[:-1],close=True,dxfattribs={'layer':'TABS_MIN5'})
d.saveas(OUT/'geometry/dvp_sheet_holes_tabs.dxf')
with (OUT/'data/dvp_holes.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(holes[0]));writer.writeheader();writer.writerows(holes)
with (OUT/'data/paths_working_coordinates.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.writer(f);writer.writerow(['operation','stroke','primitive','X_start','Y_start','X_end','Y_end','work_Z','safe_Z','I','J','feed_XY'])
    for p in paths:
        for s in p['segments']:
            ij=[s['center'][i]-s['start'][i] for i in range(2)] if s['kind']=='arc' else ['', '']
            writer.writerow([p['operation'],p['name'],s['kind'],*s['start'],*s['end'],p['z'],p['safe_z'],*ij,p['feed_xy']])
js(OUT/'data/toolpaths.json',paths);js(OUT/'data/tabs.json',tabs);js(OUT/'data/time_estimates.json',stats)
js(OUT/'data/planned_3d_motion.json',motion_plans)
js(OUT/'data/run_parameters.json',{
 'part':'PARAD-003','dimensions_mm':[2100,270,30],'work_axes':{'X':'depth 270, right','Y':'length 2100, away from operator','Z':'up'},
 'coordinate_origin':'front-left bounding corner of part, not sheet or machine home',
 'release_scope':'Four AIR_XY NC previews; no spindle start and no cutting depth in NC. Full working motions are offline JSON/DXF only.',
 'cutting_spindle_policy':'M3/M5 from eventual cutting NC; water and tool changes manual',
 'dvp':{'diameter_mm':4,'flutes':1,'rpm_selected':16000,'feed_xy':800,'feed_z':100,'source':'ArtCAM',
        'thickness_mm':5,'Z0':'table','depth_Z':[2.5,.3],'safe_Z':45,'rapid_to_Z':7,'pre_drill_mm':8,
        'tabs_width_min':5,'tabs_height':5,'tabs_count':6,'accepted_template_corners_R':2,
        'sheet_mm':[1220,2710],'sheet_to_part_origin_mm':[50,50]},
 'pcd':{'diameter_mm':6,'rpm_selected':8000,'feed_xy':500,'feed_z':100,'source_requested':'pendant, unverified settings',
        'Z0':'stone top','depth_Z':[-1.5,-2.5],'safe_Z':40,'rapid_to_Z':2,'width_steps':[1]*13+[.5]},
 'hv':{'diameter_mm':74,'profile_R_mm':13.5,'cutting_height_mm':28,'ideal_extra_top_cylinder_mm':1,
       'Z0':'stone bottom','tool_reference':'lowest cutting point','work_Z':0,'safe_Z':70,
       'source_requested':'pendant, unverified settings','rpm_requested':6000,'stated_tool_max_rpm':4000,
       'rpm_status':'User experimental request above stated tool limit; no S or M3 in AIR NC; not validated for cutting',
       'feed_rough':292.5,'feed_finish':162.5,'normal_infeed_steps':[1,2,2,2,2,2,2,.5]},
 'new_implementation_choices':{'approach_clearance_above_top_mm':2,'DVP_skip_width_including_round_end_compensation_mm':9,
   'HV_exit_center_X':97,'PCD_profile_exit_center_X':63,'machine_rapid_speed':None,'tool_holder_dimensions':None},
 'material':'Emperador Dark, nominal contour, no external allowance',
 'direction':'CCW around the outside with CW M3; conventional relative to the kept part',
 'physical_tests':'none','ArtCAM_export_tests':'none'})
js(OUT/'data/geometry_verification.json',checks)
js(OUT/'data/inputs_manifest.json',{str(p):sha(p) for p in [CAD/'podoconnik_contour_mm.dxf',CAD/'podoconnik_section_HV_mm.dxf',ROOT/'NC-Studio.con',ROOT/'NC-Studio-Arc.con',ROOT/'recomendation fres.txt',ROOT/'PCDfres.txt',ROOT/'nc/3.NC',ROOT/'nc/уп.NC']})

# Adapted drafts, not installed and not used to generate the four AIR NC files.
# Retain original authorship comments, ensure explicit G1 and F after arcs/feed changes.
original=(ROOT/'NC-Studio-Arc.con').read_text(encoding='cp1251')
for suffix,endhome in [('CAM_FS_HOME',True),('CAM_FS_STAY',False)]:
    text=original
    text=re.sub(r'DESCRIPTION = .*',f'DESCRIPTION = "PARAD A11 REVIEW {suffix} (*.nc)"',text)
    begin=text.index('START = "%"');end=text.index('; Program moves',begin)
    text=text[:begin]+'START = "%"\nSTART = "G90"\nSTART = "G21"\nSTART = "G17"\nSTART = "M5"\nSTART = "G0[ZH]"\nSTART = "G0[XH][YH]"\nSTART = "M3[S]"\n;\n'+text[end:]
    text=text.replace('FEED_RATE_MOVE         = "[X][Y][Z]"','FEED_RATE_MOVE         = "G1[X][Y][Z][F]"')
    text=text.replace('CW_ARC_MOVE            = "G2 [X] [Y] [I] [J]"','CW_ARC_MOVE            = "G2 [X] [Y] [I] [J] [F]"')
    text=text.replace('CCW_ARC_MOVE           = "G3 [X] [Y] [I] [J]"','CCW_ARC_MOVE           = "G3 [X] [Y] [I] [J] [F]"')
    ix=text.index('END = "G0[ZH]"')
    text=text[:ix]+'END = "G0[ZH]"\nEND = "M5"\n'+('END = "G0X0Y0"\n' if endhome else '')+'END = "M30"\n'
    intro='; REVIEW DRAFT - NOT MACHINE VALIDATED - CAM F/S ONLY\n; Both ArtCAM 2011 and 2018 exports must be checked.\n; STAY: CAM must fully clear HV laterally before ANY Z lift, including END.\n; This file cannot choose pendant F/S settings. No automatic tool changes.\n; Original attribution retained below.\n'
    (OUT/'postprocessors'/f'PARAD_A11_REVIEW_{suffix}.con').write_bytes((intro+text).replace('\r\n','\n').replace('\n','\r\n').encode('cp1251'))

print(json.dumps({'out':str(OUT),'paths':len(paths),'checks':checks,'time_estimates':stats},ensure_ascii=False,indent=2))
