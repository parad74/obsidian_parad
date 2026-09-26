"""Independent read-back of emitted NC, DXF and full 3D motion plans."""
from pathlib import Path
import json,sys,re,math,hashlib,argparse
BASE=Path(__file__).resolve().parent
sys.path[:0]=[str(BASE/'cadlib'),str(BASE/'cnc_readable')]
import ezdxf
from shapely.geometry import Polygon,Point,LineString
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path);args=ap.parse_args()
OUT=args.output or BASE.parent
data=lambda n:json.loads((OUT/'data'/n).read_text(encoding='utf-8'))
stats=data('time_estimates.json'); plans=data('planned_3d_motion.json')
stock=Polygon([(0,0),(50,0),(50,50),(270,50),(270,1280),(0,1280)])
report={'scope':'static NC parsing and ideal geometry only','nc':{},'dxf':{},'full_3d_plans':{}}
for p in sorted((OUT/'nc_air_xy').glob('*.nc')):
    op=p.name.removesuffix('_AIR_XY.nc');s=p.read_text('ascii');st=stats[op]
    coord={};ready=set();dist=0;arcerrors=[];nfeed=0;xs=[];ys=[]
    for no,raw in enumerate(s.splitlines(),1):
        row=re.sub(r'\([^)]*\)','',raw).strip()
        if row in ('','%'):continue
        words=re.findall(r'([A-Z])\s*([-+]?\d+(?:\.\d*)?)',row)
        assert re.sub(r'\s+','',row)==''.join(a+b for a,b in words),(no,row)
        codes=[(a,float(b)) for a,b in words if a in 'GM']
        assert not any(a in 'ST' for a,b in words)
        assert all((a=='M' and b in (5,30)) or (a=='G' and b in (0,1,2,3,17,21,90)) for a,b in codes)
        for a,b in codes:
            if a=='G' and b in (17,21,90):ready.add(b)
        moves=[int(b) for a,b in codes if a=='G' and b in (0,1,2,3)]
        if not moves:continue
        assert ready=={17,21,90}
        w={a:float(b) for a,b in words if a not in 'GM'};old=coord.copy()
        coord.update({k:v for k,v in w.items() if k in 'XYZ'})
        if 'Z' in w:assert w['Z']==st['safe_z']
        if 'X' in w or 'Y' in w:
            assert coord['Z']==st['safe_z'];xs.append(coord['X']);ys.append(coord['Y'])
        if moves[0] in (1,2,3):
            assert w.get('F',0)>0 and w['F']=={'01_dvp':800,'02_pcd':500,'03_hv_rough':292.5,'04_hv_finish':162.5}[op]
            a=(old['X'],old['Y']);b=(coord['X'],coord['Y']);nfeed+=1
            if moves[0]==1:dist+=math.dist(a,b)
            else:
                c=(a[0]+w['I'],a[1]+w['J']);r0=math.dist(a,c);r1=math.dist(b,c)
                arcerrors.append(abs(r0-r1));assert abs(r0-r1)<.002
                aa=math.atan2(a[1]-c[1],a[0]-c[0]);bb=math.atan2(b[1]-c[1],b[0]-c[0])
                sweep=(bb-aa)%(2*math.pi) if moves[0]==3 else (aa-bb)%(2*math.pi)
                assert 0<sweep<=math.pi/2+.001
                dist+=r0*sweep
    assert abs(dist-st['XY_feed_path_mm'])<.02,(op,dist,st['XY_feed_path_mm'])
    expected=(0,0) if op in ('01_dvp','02_pcd') else (97,-24) if op=='03_hv_rough' else (97,-23.5)
    assert math.dist((coord['X'],coord['Y']),expected)<.001
    assert s.rstrip().endswith('M5\nM30\n%')
    report['nc'][p.name]={'status':'pass','feed_blocks':nfeed,'XY_feed_length_mm':dist,'safe_Z_only':coord['Z'],
      'max_arc_radius_error_mm':max(arcerrors,default=0),'arcs':len(arcerrors),'end_XY':list(expected),
      'spindle_start_commands':0,'spindle_speed_words':0,'XYZ_endpoint_bounds':[min(xs),min(ys),max(xs),max(ys)]}
for p in (OUT/'geometry').glob('*.dxf'):
    d=ezdxf.readfile(p);a=d.audit();assert not a.errors and not a.fixes and d.units==4,p
    report['dxf'][p.name]={'audit_errors':0,'audit_fixes':0,'entities':len(d.modelspace())}
for name in ['stone_contour_Y1280.dxf','dvp_contour_R2_Y1280.dxf']:
    d=ezdxf.readfile(OUT/'geometry'/name);polys=list(d.modelspace().query('LWPOLYLINE'))
    assert len(polys)==1 and polys[0].closed
    bs=[v[4] for v in polys[0].get_points() if abs(v[4])>0]
    assert len(bs)==(0 if name.startswith('stone') else 1)
    assert all(abs(v+math.tan(math.pi/8))<1e-10 for v in bs)
for op,moves in plans.items():
    prev=moves[0]['start'];raises=0;fast_xy=0
    for m in moves:
        assert math.dist(prev,m['start'])<1e-8
        if m['code']=='G0' and math.dist(m['start'][:2],m['end'][:2])>1e-8:
            assert m['start'][2]==m['end'][2]==stats[op]['safe_z'];fast_xy+=1
        if op.startswith(('03','04')) and m['start'][2]!=m['end'][2]:
            assert m['start'][:2]==m['end'][:2]
            assert Point(m['start'][:2]).distance(stock)-37>=10
            if m['end'][2]>m['start'][2]:raises+=1
        if op=='02_pcd' and m['start'][2]!=m['end'][2]:assert Point(m['start'][:2]).distance(stock)-3>=9.999
        prev=m['end']
    report['full_3d_plans'][op]={'continuous':True,'rapid_XY_at_safe_Z':fast_xy,'HV_verified_lateral_exit_before_lift':raises}
manifest=data('inputs_manifest.json')
for name,digest in manifest.items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest
report['unchanged_input_files']=len(manifest)
report['physical_machine_validation']=False
(OUT/'data/nc_readback_verification.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'nc_files':len(report['nc']),'dxf_files':len(report['dxf']),'plans':len(plans),'status':'pass','physical_validation':False}))
