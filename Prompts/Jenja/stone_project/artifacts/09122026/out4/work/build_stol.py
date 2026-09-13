"""Build the confirmed island countertop from its six exact DXF curves.
Usage: python build_stol.py --source stol_source_extracted_mm.dxf --output NEW_DIR
"""
from pathlib import Path
import sys,math,json,hashlib,argparse,shutil
sys.path.insert(0,str(Path(__file__).parent/'cadlib'))
import numpy as np
import ezdxf
from ezdxf.math import Matrix44,bulge_to_arc
from scipy.integrate import quad
from scipy.optimize import minimize_scalar
from stol_source_geometry import load

ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
args=ap.parse_args();OUT=args.output;OUT.mkdir(exist_ok=True,parents=True);(OUT/'work').mkdir(exist_ok=True)
doc,cs=load(args.source)
R,H,N,TOL=10.,20.,64,.006
def ex(a):
 r=[c.extrema(a) for c in cs];return np.array([min(v[0] for v in r),max(v[1] for v in r)])
bmin=np.array([ex(0)[0],ex(math.pi/2)[0]]);bmax=np.array([ex(0)[1],ex(math.pi/2)[1]])
shift=bmin-R; size=bmax-bmin+2*R
p=np.concatenate([c.sample(TOL)[:-1] for c in cs])-shift
p=p[np.linalg.norm(p-np.roll(p,1,axis=0),axis=1)>1e-6]
K=len(p);v=np.roll(p,-1,axis=0)-p; lengths=np.linalg.norm(v,axis=1);unit=v/lengths[:,None]
norm=np.column_stack((unit[:,1],-unit[:,0]));prev=np.roll(norm,1,axis=0)
miter=(norm+prev)/(1+np.sum(norm*prev,axis=1))[:,None]
def ring(d):return p+d*miter
def area(q):return float(np.cross(q,np.roll(q,-1,axis=0)).sum()/2)
center=p.mean(0)
def validate_polygon(q):
 # Star-shaped certificate: increasing polar angles, positive fan areas, winding one.
 a=q-center;b=np.roll(a,-1,axis=0)
 cross=np.cross(a,b);assert cross.min()>0
 angles=np.arctan2(cross,np.sum(a*b,axis=1));assert abs(angles.sum()-2*math.pi)<1e-10
 assert np.sum((np.roll(q,-1,axis=0)-q)*unit,axis=1).min()>0
 return float(cross.min()/2)
for d in np.linspace(0,R,101):validate_polygon(ring(d))
theta=np.linspace(-math.pi/2,math.pi/2,N+1)
dist=R*np.cos(theta);dist[0]=dist[-1]=0
zs=R+R*np.sin(theta);zs[0]=0;zs[-1]=20
rings=np.array([np.column_stack((ring(d),np.full(K,z))) for d,z in zip(dist,zs)])
verts=rings.reshape(-1,3).tolist();bottom=len(verts);verts.append([*center,0]);top=len(verts);verts.append([*center,H])
faces=[]
for k in range(N):
 for j in range(K):
  a=k*K+j;b=k*K+(j+1)%K;c=b+K;d=a+K;faces.extend([(a,b,c),(a,c,d)])
for j in range(K):
 faces.append((bottom,(j+1)%K,j));faces.append((top,N*K+j,N*K+(j+1)%K))
verts=np.array(verts);faces=np.array(faces);tri=verts[faces]
volume=float(np.einsum('ij,ij->i',tri[:,0],np.cross(tri[:,1],tri[:,2])).sum()/6)
assert np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1).min()>1e-8
actual_size=np.ptp(verts,axis=0);assert np.max(np.abs(actual_size-np.r_[size,H]))<.025

def newdoc():
 d=ezdxf.new('R2000');d.units=4;d.header['$MEASUREMENT']=1
 for name,col in [('BASE_EXACT',8),('ENVELOPE',4),('SECTION',7),('DIMENSIONS',3),('NOTES',7),('SOLID_MESH',7),('STOCK',6)]:d.layers.new(name,dxfattribs={'color':col})
 return d
def add_base(m):
 for c in cs:
  e=c.e.copy();e.dxf.layer='BASE_EXACT';e.transform(Matrix44.translate(-shift[0],-shift[1],0));m.add_entity(e)
def pl(m,q,layer):return m.add_lwpolyline(q,close=True,dxfattribs={'layer':layer})
def txt(m,s,p,h=30):m.add_text(s,dxfattribs={'insert':p,'height':h,'layer':'NOTES'})
def dim(m,a,b,pos,angle=0):
 d=m.add_linear_dim(base=pos,p1=a,p2=b,angle=angle,dxfattribs={'layer':'DIMENSIONS'},override={'dimtxt':26,'dimasz':20,'dimexo':8,'dimexe':15,'dimdec':3,'dimtad':1});d.render()
def section(m,origin=(0,0),scale=1):
 # x=0 is original top perimeter, the semicircle protrudes outward to x=10.
 q=[(-100,0,0),(0,0,1),(0,20,0),(-100,20,0)]
 return m.add_lwpolyline([(origin[0]+x*scale,origin[1]+y*scale,b) for x,y,b in q],format='xyb',close=True,dxfattribs={'layer':'SECTION'})

shutil.copy2(args.source,OUT/'stol_source_extracted_mm.dxf')
d=newdoc();add_base(d.modelspace());d.saveas(OUT/'stol_base_exact_mm.dxf')
d=newdoc();pl(d.modelspace(),ring(R),'ENVELOPE');d.saveas(OUT/'stol_contour_mm.dxf')
d=newdoc();section(d.modelspace());d.saveas(OUT/'stol_sections_mm.dxf')
d=newdoc();m=d.modelspace()
for t in tri:m.add_3dface(t.tolist(),dxfattribs={'layer':'SOLID_MESH'})
d.saveas(OUT/'stol_volume_3d_mm.dxf');del d,m

# Minimum square from exact support extrema; a 10 mm parallel contour adds 20 mm to each width.
def square(a):return max(np.ptp(ex(a)),np.ptp(ex(a+math.pi/2)))+20
aa=np.linspace(0,math.pi/2,361);vv=[square(a) for a in aa];ix=int(np.argmin(vv))
opt=minimize_scalar(square,bounds=(aa[max(0,ix-1)],aa[min(360,ix+1)]),method='bounded',options={'xatol':1e-13})
ang=float(opt.x);rot=np.array([[math.cos(ang),math.sin(ang)],[-math.sin(ang),math.cos(ang)]])
rotq=ring(R)@rot.T;rot_size=np.ptp(rotq,axis=0)
stock_size=2200.;clearances=(stock_size-rot_size)/2
assert min(clearances)>24
stock=dict(exact_support_square_mm=square(ang),rotation_clockwise_degrees=math.degrees(ang),
           mesh_rotated_envelope_mm=rot_size.tolist(),recommended_square_mm=stock_size,
           centered_clearances_mm=clearances.tolist(),axis_aligned_minimum_mm=square(0),axis_aligned_square_mm=2500,
           margin_basis='2200 mm square gives >=24 mm free border at recommended rotation; allowance is geometric, not a verified machine setup')
(OUT/'work/stock_calculation.json').write_text(json.dumps(stock,ensure_ascii=False,indent=2),encoding='utf8')

d=newdoc();m=d.modelspace();add_base(m);pl(m,ring(R),'ENVELOPE')
txt(m,'ISLAND COUNTERTOP / mm / ORIGINAL DXF CONTOUR',(0,size[1]+280),43)
txt(m,'V EDGE R10 / H20 / OUTWARD OVERHANG 10 mm / FULL PERIMETER',(0,size[1]+210),28)
dim(m,(0,0),(size[0],0),(0,-120));dim(m,(size[0],0),(size[0],size[1]),(size[0]+140,0),90)
dim(m,(10,10),(size[0]-10,10),(0,-235));dim(m,(10,10),(10,size[1]-10),(-170,0),90)
txt(m,'Cyan: outer envelope. Grey: exact upper/lower surface contour.',(0,-340),26)
section(m,(150,-700),5);txt(m,'V PROFILE / DISPLAY 5:1 / ACTUAL H20, R10, OVERHANG 10',(0,-800),25)
txt(m,'Source dimension labels 1630 x 2420 were not used to scale the contour.',(0,-920),25)
txt(m,'No holes. No base cabinet. Full closed solid; no toolpaths.',(0,-970),25)
d.saveas(OUT/'stol_drawing_mm.dxf')

base_area=sum(quad(lambda t:(c.point(t)[0]*c.tangent(t)[1]-c.point(t)[1]*c.tangent(t)[0])/2,c.a,c.b,epsabs=1e-5)[0] for c in cs)
perimeter=sum(quad(lambda t:np.linalg.norm(c.tangent(t)),c.a,c.b,epsabs=1e-7)[0] for c in cs)
# Independent polygon-offset area polynomial integrates the exact semicircular vertical profile.
A=area(p);A5=area(ring(5));A10=area(ring(10));coef2=(A10-2*A5+A)/50;coef1=(A5-A-25*coef2)/5
integrated_volume=20*A+coef1*math.pi*R**2/2+coef2*4*R**3/3
assert abs(volume-integrated_volume)/integrated_volume<3e-5
profile_bound=float(R*(1-math.cos(math.pi/(2*N)))*np.linalg.norm(miter,axis=1).max())
miter_extra=float(R*(np.linalg.norm(miter,axis=1).max()-1))
# A ruled patch mixed derivative bound: quad-to-triangle deviation <= |delta d|*|delta miter|/4.
mixed_bound=float(np.max(np.abs(np.diff(dist)))*np.linalg.norm(np.roll(miter,-1,axis=0)-miter,axis=1).max()/4)
total_bound=TOL+profile_bound+miter_extra+mixed_bound
assert total_bound<.1
verification={}
for path in OUT.glob('*.dxf'):
 r=ezdxf.readfile(path);audit=r.audit();assert not audit.errors and not audit.fixes
 verification[path.name]=dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),entities=len(r.modelspace()),audit_errors=0,audit_fixes=0,units='mm')
 if path.name=='stol_sections_mm.dxf':
  s=list(r.modelspace())[0];qp=list(s.get_points('xyb'));_,_,_,radius=bulge_to_arc(qp[1][:2],qp[2][:2],qp[1][2]);assert abs(radius-R)<1e-9
 if path.name=='stol_volume_3d_mm.dxf':
  actual=np.array([[tuple(e.dxf.get('vtx'+str(j))) for j in range(3)] for e in r.modelspace()]);assert np.max(np.abs(actual-tri))<1e-9
 del r
verification['geometry']=dict(base_exact_size_mm=(bmax-bmin).tolist(),envelope_target_mm=[*size,H],envelope_mesh_mm=actual_size.tolist(),
 base_exact_area_mm2=base_area,base_polygon_area_mm2=A,base_perimeter_mm=perimeter,source_translation_mm=(-shift).tolist(),
 perimeter_samples=K,profile_intervals=N,vertices=len(verts),triangles=len(faces),mesh_volume_mm3=volume,
 independent_integrated_offset_volume_mm3=integrated_volume,volume_relative_error=abs(volume-integrated_volume)/integrated_volume,
 base_curve_chord_bound_mm=TOL,profile_chord_bound_mm=profile_bound,join_miter_excess_bound_mm=miter_extra,
 ruled_patch_triangle_bound_mm=mixed_bound,combined_model_bound_mm=total_bound,
 polygon_star_certificate=True,profile_radius_mm=R,overhang_mm=R,height_mm=H,
 ArtCAM_import_tested=False,physical_accuracy_verified=False)
(OUT/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2),encoding='utf8')
np.savez(OUT/'work/model_arrays.npz',vertices=verts,faces=faces,base=p,envelope=ring(R),shift=shift,stock_rotation=rot)
print(json.dumps(verification['geometry'],indent=2));print(json.dumps(stock,indent=2))
