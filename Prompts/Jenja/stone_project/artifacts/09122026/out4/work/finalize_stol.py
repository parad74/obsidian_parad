"""Place the archived input DXF/STL on the confirmed stone sheet without remeshing."""
from pathlib import Path
import sys,json,math,hashlib,argparse
sys.path.insert(0,str(Path(__file__).parent/'cadlib'))
import numpy as np,ezdxf
from ezdxf.math import Matrix44

ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--support',type=Path,required=True)
args=ap.parse_args();OUT=args.output;OUT.mkdir(exist_ok=True,parents=True);(OUT/'work').mkdir(exist_ok=True)
source=args.input/'stol_volume_3d_mm.dxf';stl=args.input/'stol_volume_mm.stl'
input_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [source,stl]}
old=json.loads((args.support/'work/stl_verification.json').read_text(encoding='utf8'))
assert input_hashes[source.name]==old['source_sha256'] and input_hashes[stl.name]==old['output_sha256']
src=ezdxf.readfile(source);audit=src.audit();assert not audit.errors and not audit.fixes and src.units==4
tri=np.array([[tuple(e.dxf.get('vtx'+str(i))) for i in range(3)] for e in src.modelspace()])
assert all(e.dxftype()=='3DFACE' and e.dxf.vtx2.isclose(e.dxf.vtx3) for e in src.modelspace())
arrays=np.load(args.support/'work/model_arrays.npz');verts=arrays['vertices'];faces=arrays['faces'];base=arrays['base'];envelope=arrays['envelope']
assert np.max(np.abs(tri-verts[faces]))<1e-9
# Verify that the saved input STL is the archived DXF mesh, within float32 precision.
dtype=np.dtype([('normal','<f4',(3,)),('v','<f4',(3,3)),('attr','<u2')])
raw=stl.read_bytes();stl_tri=np.frombuffer(raw,dtype=dtype,offset=84)['v'].astype(float)
assert stl_tri.shape==tri.shape and np.max(np.linalg.norm(stl_tri-tri,axis=2))<.001
a=math.radians(5);rot=np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]])
turned=envelope@rot.T;span=np.ptp(turned,axis=0)
offset=np.array([(1645-turned[:,0].min()-turned[:,0].max())/2,3200-25-turned[:,1].max()])
def transform(x):
 y=x.copy();y[...,:2]=x[...,:2]@rot.T+offset;return y
outtri=transform(tri);vout=transform(verts);p=base@rot.T+offset;q=envelope@rot.T+offset
assert np.max(np.abs(outtri-vout[faces]))<1e-9
before_volume=float(np.einsum('ij,ij->i',tri[:,0],np.cross(tri[:,1],tri[:,2])).sum()/6)
after_volume=float(np.einsum('ij,ij->i',outtri[:,0],np.cross(outtri[:,1],outtri[:,2])).sum()/6)
assert abs(before_volume-after_volume)<.001
inverse=outtri.copy();inverse[...,:2]=(outtri[...,:2]-offset)@rot
inverse_error=float(np.max(np.linalg.norm(inverse-tri,axis=2)));assert inverse_error<1e-8

def newdoc():
 d=ezdxf.new('R2000');d.units=4;d.header['$MEASUREMENT']=1;d.header['$INSBASE']=(0,0,0)
 for name,col in [('BASE_EXACT',8),('ENVELOPE',4),('SECTION',7),('DIMENSIONS',3),('NOTES',7),('SOLID_MESH',7),('STOCK',6)]:d.layers.new(name,dxfattribs={'color':col})
 return d
def pl(m,pts,layer):return m.add_lwpolyline(pts,close=True,dxfattribs={'layer':layer})
def text(m,s,pt,h=30):m.add_text(s,dxfattribs={'insert':pt,'height':h,'layer':'NOTES'})
def dim(m,x,y,pos,angle=0):
 b=m.add_linear_dim(base=pos,p1=x,p2=y,angle=angle,dxfattribs={'layer':'DIMENSIONS'},override={'dimtxt':28,'dimasz':20,'dimexo':8,'dimexe':12,'dimdec':3,'dimtad':1});b.render()
base_doc=ezdxf.readfile(args.support/'stol_base_exact_mm.dxf')
matrix=Matrix44.z_rotate(a)@Matrix44.translate(*offset,0)
def addbase(m):
 for e in base_doc.modelspace():
  c=e.copy();c.dxf.layer='BASE_EXACT';c.transform(matrix);m.add_entity(c)
def section(m,origin=(0,0),scale=1):
 s=[(-100,0,0),(0,0,1),(0,20,0),(-100,20,0)]
 return m.add_lwpolyline([(origin[0]+x*scale,origin[1]+y*scale,b) for x,y,b in s],format='xyb',close=True,dxfattribs={'layer':'SECTION'})
d=newdoc();addbase(d.modelspace());d.saveas(OUT/'stol_base_exact_mm.dxf');d.saveas(OUT/'stol_source_extracted_mm.dxf')
d=newdoc();pl(d.modelspace(),q,'ENVELOPE');d.saveas(OUT/'stol_contour_mm.dxf')
d=newdoc();section(d.modelspace());d.saveas(OUT/'stol_sections_mm.dxf')
d=newdoc()
for t in outtri:d.modelspace().add_3dface(t.tolist(),dxfattribs={'layer':'SOLID_MESH'})
d.saveas(OUT/'stol_volume_3d_mm.dxf');del d

lo=outtri.min(axis=(0,1));hi=outtri.max(axis=(0,1));clear=dict(left_mm=float(lo[0]),right_mm=float(1645-hi[0]),top_mm=float(3200-hi[1]),bottom_mm=float(lo[1]))
assert min(clear.values())>24 and abs(clear['top_mm']-25)<1e-8
d=newdoc();m=d.modelspace();pl(m,[(0,0),(1645,0),(1645,3200),(0,3200)],'STOCK');pl(m,q,'ENVELOPE');addbase(m)
text(m,'ISLAND COUNTERTOP / SHEET COORDINATES / mm',(0,3470),45)
text(m,'SHEET 1645 x 3200 / ROTATION 5 deg CCW / TOP CLEARANCE 25',(0,3380),27)
dim(m,(0,0),(1645,0),(0,-130));dim(m,(1645,0),(1645,3200),(1830,0),90)
dim(m,(lo[0],lo[1]),(hi[0],lo[1]),(0,lo[1]-140));dim(m,(lo[0],lo[1]),(lo[0],hi[1]),(-210,0),90)
text(m,'Upper/lower face: exact source shape, not rescaled.',(0,-240),27)
text(m,'V R10 / HEIGHT 20 / OUTWARD OVERHANG 10 / FULL PERIMETER',(0,-310),27)
text(m,'Left/right gap 24.139 / Top gap 25 / Bottom remainder 669.577',(0,-380),27)
section(m,(800,-650),5);text(m,'LOCAL NORMAL SECTION / DISPLAY 5:1 / ACTUAL H20 R10',(0,-780),27)
text(m,'O=(0,0,0): sheet lower left, lower face. X right, Y up, Z thickness.',(0,-890),25)
text(m,'Exact base 1627.612 x 2423.897. Source labels 1630 x 2420 not used.',(0,-950),25)
d.saveas(OUT/'stol_drawing_mm.dxf')
# Stock layout DXF is separate from the clean working outline.
d=newdoc();m=d.modelspace();pl(m,[(0,0),(1645,0),(1645,3200),(0,3200)],'STOCK');pl(m,q,'ENVELOPE');addbase(m);d.saveas(OUT/'stol_stock_layout_mm.dxf')

checks={}
for path in OUT.glob('*.dxf'):
 r=ezdxf.readfile(path);audit=r.audit();assert not audit.errors and not audit.fixes and r.units==4
 checks[path.name]=dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),entities=len(r.modelspace()),audit_errors=0,audit_fixes=0,units='mm')
 if path.name=='stol_volume_3d_mm.dxf':
  saved=np.array([[tuple(e.dxf.get('vtx'+str(j))) for j in range(3)] for e in r.modelspace()]);assert np.max(np.abs(saved-outtri))<1e-9
 if path.name=='stol_contour_mm.dxf':
  line=r.modelspace()[0];assert line.closed and np.max(np.abs(np.array(list(line.get_points('xy')))-q))<1e-9
 del r
original=json.loads((args.support/'verification.json').read_text(encoding='utf8'))['geometry']
original.update(envelope_mm=(hi-lo).tolist(),bounds_mm=[lo.tolist(),hi.tolist()],rotation_ccw_degrees=5,translation_after_rotation_mm=offset.tolist(),
               clearances_mm=clear,inverse_transform_error_mm=inverse_error,volume_before_transform_mm3=before_volume,mesh_volume_mm3=after_volume)
checks['geometry']=original
(OUT/'verification.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf8')
params=dict(sheet_mm=[1645,3200],rotation_ccw_degrees=5,height_mm=20,edge_radius_mm=10,edge_overhang_mm=10,
            coordinate_origin='Sheet lower left at lower face, x right y up',translation_after_rotation_mm=offset.tolist(),clearances_mm=clear,
            no_scaling=True,input_files=input_hashes,date='2026-09-13',ArtCAM_import_tested=False)
(OUT/'work/run_parameters.json').write_text(json.dumps(params,ensure_ascii=False,indent=2),encoding='utf8')
np.savez(OUT/'work/model_arrays.npz',vertices=vout,faces=faces,base=p,envelope=q)
for path in [source,stl]:assert hashlib.sha256(path.read_bytes()).hexdigest()==input_hashes[path.name]
print(json.dumps(params,indent=2));print('FINAL SIZE',hi-lo,'VOLUME',after_volume,'INVERSE ERROR',inverse_error)
