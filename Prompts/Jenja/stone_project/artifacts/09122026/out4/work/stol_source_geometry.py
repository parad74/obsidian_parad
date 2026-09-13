from pathlib import Path
import sys,math,json,hashlib
sys.path.insert(0,str(Path(__file__).parent/'cadlib'))
import ezdxf,numpy as np
from scipy.interpolate import BSpline, PPoly
from scipy.optimize import minimize_scalar
from scipy.integrate import quad
from ezdxf.math import Matrix44
HANDLES=['A4DB','A4DC','A4DD','A4DE','A4DF','A4E0']
SOURCE=None

class Curve:
 def __init__(self,e):
  self.e=e;self.arc=e.dxftype()=='ARC'
  if self.arc:
   self.c=np.array(e.dxf.center)[:2];self.r=e.dxf.radius
   self.a=math.radians(e.dxf.start_angle);self.b=self.a+math.radians((e.dxf.end_angle-e.dxf.start_angle)%360)
  else:
   self.s=BSpline(e.knots,np.array(e.control_points)[:,:2],e.dxf.degree)
   self.a=self.s.t[self.s.k];self.b=self.s.t[-self.s.k-1]
 def point(self,t):
  if self.arc:return self.c+self.r*np.array([np.cos(t),np.sin(t)]).T
  return self.s(t)
 def tangent(self,t):
  if self.arc:return self.r*np.array([-np.sin(t),np.cos(t)]).T
  return self.s(t,nu=1)
 def extrema(self,angle=0):
  v=np.array([math.cos(angle),math.sin(angle)]); ts=[self.a,self.b]
  if self.arc:
   for k in range(-5,6):
    t=angle+k*math.pi
    if self.a<t<self.b:ts.append(t)
  else:
   scalar=BSpline(self.s.t,self.s.c@v,self.s.k)
   ts += [float(t) for t in PPoly.from_spline(scalar.derivative()).roots(extrapolate=False) if self.a<t<self.b]
  p=self.point(np.array(ts))@v
  return float(p.min()),float(p.max())
 def sample(self,tol=.006):
  # Cubic Bezier convex-hull distance bounds; arcs use exact sagitta.
  if self.arc:
   n=math.ceil((self.b-self.a)/(2*math.acos(1-tol/self.r)))
   ts=sorted(set(np.linspace(self.a,self.b,n+1).tolist()+[a for a in [math.pi*k/2 for k in range(10)] if self.a<a<self.b]))
   return self.point(np.array(ts))
  pts=[]
  def split(a,b,depth=0):
   p0,p3=self.point(a),self.point(b);dt=b-a
   p1=p0+self.tangent(a)*dt/3;p2=p3-self.tangent(b)*dt/3
   v=p3-p0
   dist=[np.linalg.norm(p-p0-np.clip(np.dot(p-p0,v)/np.dot(v,v),0,1)*v) for p in [p1,p2]]
   if max(dist)<=tol:pts.append(p0)
   else:
    assert depth<30
    split(a,(a+b)/2,depth+1);split((a+b)/2,b,depth+1)
  knots=sorted(set([self.a,self.b]+[float(t) for t in self.s.t if self.a<t<self.b]))
  for a,b in zip(knots,knots[1:]):split(a,b)
  pts.append(self.point(self.b));return np.array(pts)

def load(source=None):
 source=source or SOURCE
 if source is None:raise ValueError('Provide a source DXF path')
 d=ezdxf.readfile(source)
 entities=[d.entitydb[h] for h in HANDLES] if all(h in d.entitydb for h in HANDLES) else list(d.modelspace())
 assert len(entities)==6 and all(e.dxftype() in ('ARC','SPLINE') for e in entities)
 return d,[Curve(e) for e in entities]

if __name__=='__main__':
 SOURCE=Path(sys.argv[1])
 d,cs=load(); mins=[];maxs=[]
 for ang in [0,math.pi/2]:
  ex=[c.extrema(ang) for c in cs];mins.append(min(e[0] for e in ex));maxs.append(max(e[1] for e in ex))
 dims=np.array(maxs)-mins
 p=np.concatenate([c.sample()[:-1] for c in cs]);vectors=np.roll(p,-1,axis=0)-p
 turns=np.degrees(np.arctan2(np.cross(vectors,np.roll(vectors,-1,axis=0)),np.sum(vectors*np.roll(vectors,-1,axis=0),axis=1)))
 gaps=[];joins=[]
 for c,n in zip(cs,cs[1:]+cs[:1]):
  gaps.append(float(np.linalg.norm(c.point(c.b)-n.point(n.a))))
  a=c.tangent(c.b);b=n.tangent(n.a);joins.append(float(np.degrees(np.arctan2(np.cross(a,b),np.dot(a,b)))))
 print('exact bounds',mins,maxs,'size',dims,'points',len(p),'turns min/max',turns.min(),turns.max(),'joins',joins,'gaps',gaps)
 area=sum(quad(lambda t:(c.point(t)[0]*c.tangent(t)[1]-c.point(t)[1]*c.tangent(t)[0])/2,c.a,c.b,epsabs=1e-5)[0] for c in cs)
 perimeter=sum(quad(lambda t:np.linalg.norm(c.tangent(t)),c.a,c.b,epsabs=1e-7)[0] for c in cs)
 report=dict(source_name=SOURCE.name,source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),handles=HANDLES,
             exact_min=mins,exact_max=maxs,size=dims.tolist(),area_mm2=area,perimeter_mm=perimeter,
             joint_gaps_mm=gaps,joint_tangent_angles_degrees=joins,sample_vertices=len(p),min_turn_degrees=float(turns.min()))
 Path('work/stol_analysis/source_geometry.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
 out=ezdxf.new('R2000');out.units=4
 for h in HANDLES:
  e=d.entitydb[h].copy();e.dxf.layer='0';out.modelspace().add_entity(e)
 out.saveas('work/stol_analysis/stol_source_extracted_mm.dxf')
 print('area',area,'perimeter',perimeter)
