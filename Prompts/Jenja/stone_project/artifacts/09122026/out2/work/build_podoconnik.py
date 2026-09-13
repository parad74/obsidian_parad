from pathlib import Path
import sys, math, json, hashlib
from collections import Counter
sys.path.insert(0, str(Path(__file__).parent / 'cadlib'))
import numpy as np
import ezdxf
from ezdxf import bbox
from ezdxf.math import bulge_to_arc
from ezdxf.addons.drawing import Frontend, RenderContext, layout, svg, config
from PIL import Image, ImageDraw, ImageFont

import argparse
parser=argparse.ArgumentParser()
parser.add_argument('--length',type=float,required=True)
parser.add_argument('--depth',type=float,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
L,D=args.length,args.depth
assert math.isfinite(L) and math.isfinite(D) and L>100 and D>50
A0=L*50+(L-100)*(D-50)
OUT=args.output
OUT.mkdir(parents=True,exist_ok=True)
R, N = 13.5, 96
def boundary(d):
    return [(d,d),(L-d,d),(L-d,50),((L-50),50),
            ((L-50),D),(50,D),(50,50),(d,50)]

def newdoc():
    doc = ezdxf.new('R2000')
    doc.units = 4
    doc.header['$MEASUREMENT'] = 1
    doc.header['$LUNITS'] = 2
    doc.header['$LUPREC'] = 3
    doc.header['$INSBASE'] = (0,0,0)
    for name,color in [('OUTLINE',7),('PROFILE',4),('DIMENSIONS',3),
                       ('NOTES',7),('FRONT_VIEW',7),('SECTION',7),('SOLID_MESH',7)]:
        doc.layers.new(name, dxfattribs={'color':color})
    return doc

def poly(msp, points, layer='OUTLINE', close=True):
    return msp.add_lwpolyline(points, close=close, dxfattribs={'layer':layer})

doc = newdoc()
poly(doc.modelspace(), boundary(0))
doc.saveas(OUT/'podoconnik_contour_mm.dxf')

# Coordinates are depth inward from frontmost envelope, and height from bottom.
# The exact 180-degree bulge bows towards the front (minimum depth = 0).
section = [(D,30,0),(R,30,0),(R,27,1),(R,0,0),(D,0,0)]
doc = newdoc()
doc.modelspace().add_lwpolyline(section, format='xyb', close=True,
                              dxfattribs={'layer':'SECTION'})
doc.saveas(OUT/'podoconnik_section_HV_mm.dxf')

doc = newdoc(); msp = doc.modelspace()
poly(msp, boundary(0))
poly(msp, [(R,50),(R,R),(L-R,R),(L-R,50)], 'PROFILE', False)
for a,b in [((0,0),(R,R)),((L,0),(L-R,R))]:
    msp.add_line(a,b,dxfattribs={'layer':'PROFILE'})

def text(s, p, h=18):
    msp.add_text(s, dxfattribs={'height':h,'insert':p,'layer':'NOTES'})

def dim(p1,p2,base,angle=0, factor=1, label='<>'):
    d = msp.add_linear_dim(base=base,p1=p1,p2=p2,angle=angle,text=label,
        override={'dimtxt':17,'dimasz':8,'dimgap':5,'dimexo':4,
                  'dimexe':7,'dimdec':1,'dimtad':1,'dimlfac':factor},
        dxfattribs={'layer':'DIMENSIONS'})
    d.render()

text('WINDOW SILL / STAGE 1 / mm', (0,D+195), 30)
text(f'Overall {L:g} x {D:g} x 30 | Rear {L-100:g} | HV R13.5', (0,D+150), 20)
text('TOP VIEW 1:1 / OUTERMOST ENVELOPE', (460,180), 20)
dim((0,0),(L,0),(0,-65))
dim((50,D),((L-50),D),(0,D+65))
dim((L,0),(L,D),((L+100),0),90)
dim((0,0),(0,50),(-70,0),90)
dim((0,50),(50,50),(0,115))
dim(((L-50),50),(L,50),(0,115))
text('HV: FRONT + BOTH 50 mm RETURNS', (370,-115), 18)
text('Sharp plan corners; diagonal profile joints.', (370,-147), 16)

# The front silhouette is L wide at mid-height, L-27 at top/bottom.
curve_z = [R+R*math.sin(-math.pi/2+math.pi*i/N) for i in range(N+1)]
curve_d = [R-R*math.cos(-math.pi/2+math.pi*i/N) for i in range(N+1)]
front = [(R,-285,-1),(R,-258,0),(R,-255,0),
         (L-R,-255,0),(L-R,-258,-1),(L-R,-285,0)]
msp.add_lwpolyline(front,format='xyb',close=True,dxfattribs={'layer':'FRONT_VIEW'})
msp.add_line((R,-258),(L-R,-258),dxfattribs={'layer':'PROFILE'})
text('FRONT VIEW 1:1', (550,-220), 19)
dim((L,-285),(L,-255),((L+100),0),90)

sx,sy,scale=120,-610,4
transformed=[(sx+scale*x,sy+scale*y,b) for x,y,b in section]
msp.add_lwpolyline(transformed,format='xyb',close=True,dxfattribs={'layer':'SECTION'})
text('CENTRE SECTION / HV EDGE / DISPLAY SCALE 4:1', (120,-420), 19)
text('Section dimensions show actual mm.', (120,-710), 16)
dim((sx,sy),(sx+D*scale,sy),(sx,sy-60),factor=1/scale)
dim((sx+D*scale,sy),(sx+D*scale,sy+30*scale),(sx+D*scale+80,sy),90,1/scale)
dim((sx+R*scale,sy),(sx+R*scale,sy+27*scale),(sx-85,sy),90,1/scale)
text('R13.5', (sx+135,sy+45), 20)
msp.add_line((sx+130,sy+52),(sx,sy+R*scale),dxfattribs={'layer':'DIMENSIONS'})
text('3 mm upper vertical segment', (sx+220,sy+155), 17)
msp.add_line((sx+225,sy+145),(sx+R*scale,sy+28.5*scale),dxfattribs={'layer':'DIMENSIONS'})
text('Parametric geometry from specified dimensions; no physical object measured.', (0,-760), 17)
text('0.1 mm: requested dimensional accuracy; physical object accuracy is unverified.', (0,-792), 17)
text('Use contour DXF for 2D import; use mesh DXF for 3D import. No toolpaths.', (0,-824), 17)
doc.saveas(OUT/'podoconnik_drawing_mm.dxf')

# Ear clipping triangulates the concave 8-vertex caps without crossing notches.
def triangulate(points):
    ids=list(range(len(points))); out=[]
    def cross(a,b,c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    while len(ids)>3:
        for j,b in enumerate(ids):
            a,c=ids[j-1],ids[(j+1)%len(ids)]
            if cross(points[a],points[b],points[c])<=1e-9: continue
            inside=False
            for k in ids:
                if k in (a,b,c): continue
                if min(cross(points[a],points[b],points[k]),
                       cross(points[b],points[c],points[k]),
                       cross(points[c],points[a],points[k]))>=-1e-9:
                    inside=True; break
            if inside: continue
            out.append((a,b,c)); ids.pop(j); break
        else: raise ValueError('Cannot triangulate cap')
    return out+[tuple(ids)]

rings=[[(x,y,z) for x,y in boundary(d)] for d,z in zip(curve_d,curve_z)]
rings.append([(x,y,30) for x,y in boundary(R)])
vertices=np.array([p for ring in rings for p in ring])
faces=[]
for k in range(len(rings)-1):
    for j in range(8):
        a=k*8+j; b=k*8+(j+1)%8; c=b+8; d=a+8
        faces.extend([(a,b,c),(a,c,d)])
caps=triangulate(boundary(R))
faces.extend([(c,b,a) for a,b,c in caps])
last=(len(rings)-1)*8
faces.extend([(a+last,b+last,c+last) for a,b,c in caps])
doc=newdoc(); msp=doc.modelspace()
for face in faces:
    msp.add_3dface([vertices[i] for i in face], dxfattribs={'layer':'SOLID_MESH'})
doc.saveas(OUT/'podoconnik_volume_3d_mm.dxf')

# Verify the saved files, including the serialized surface topology and dimensions.
checks={}
for p in OUT.glob('*.dxf'):
    reread=ezdxf.readfile(p); audit=reread.audit()
    assert not audit.errors and not audit.fixes, (p.name,audit.errors,audit.fixes)
    assert reread.units==4
    checks[p.name]={'audit_errors':0,'audit_fixes':0,'units':'mm',
                   'entities':len(reread.modelspace()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
contour=ezdxf.readfile(OUT/'podoconnik_contour_mm.dxf').modelspace()[0]
assert contour.closed and len(contour)==8
xy=np.array(list(contour.get_points('xy')))
assert np.allclose(xy,np.array(boundary(0)),rtol=0,atol=1e-10)
area=abs(sum(xy[i,0]*xy[(i+1)%8,1]-xy[(i+1)%8,0]*xy[i,1] for i in range(8)))/2
assert area==A0
section_read=ezdxf.readfile(OUT/'podoconnik_section_HV_mm.dxf').modelspace()[0]
assert section_read.closed
sp=list(section_read.get_points('xyb'))
centre,start,end,radius=bulge_to_arc(sp[2][:2],sp[3][:2],sp[2][2])
assert abs(radius-R)<1e-10 and np.allclose(centre,(R,R))
assert np.allclose(bbox.extents([section_read]).size,(D,30,0))
front_read=list(ezdxf.readfile(OUT/'podoconnik_drawing_mm.dxf').modelspace().query('LWPOLYLINE[layer=="FRONT_VIEW"]'))[0]
assert front_read.closed and np.allclose(bbox.extents([front_read]).size,(L,30,0))

mesh=ezdxf.readfile(OUT/'podoconnik_volume_3d_mm.dxf').modelspace()
edge_counts=Counter(); directed=Counter(); volume=0.0; mesh_points=[]
for face in mesh:
    ps=[tuple(round(v,9) for v in face.dxf.get('vtx'+str(i))) for i in range(3)]
    mesh_points.extend(ps)
    a,b,c=np.array(ps)
    assert np.linalg.norm(np.cross(b-a,c-a))>1e-9
    volume+=float(np.dot(a,np.cross(b,c)))/6
    for u,v in zip(ps,ps[1:]+ps[:1]):
        edge_counts[tuple(sorted([u,v]))]+=1; directed[(u,v)]+=1
assert set(edge_counts.values())=={2}
assert all(directed[(v,u)]==n for (u,v),n in directed.items())
V=len(set(mesh_points)); E=len(edge_counts); F=len(mesh)
assert V-E+F==2
assert np.allclose(np.ptp(np.array(mesh_points),axis=0),(L,D,30))
exact_volume=(A0*2*R-(L+100)*R**2*(2-math.pi/2)
              +2*R**3*(10/3-math.pi)+3*(A0-(L+100)*R+2*R**2))
assert volume>0 and abs(volume-exact_volume)/exact_volume<0.0001
max_chord_error=math.sqrt(2)*R*(1-math.cos(math.pi/(2*N)))
assert max_chord_error<0.1
checks['geometry']={'envelope_mm':[L,D,30],'rear_width_mm':(L-100),
    'wings_mm':[50,50],'wing_depth_mm':50,'contour_area_mm2':area,
    'radius_mm':radius,'arc_height_mm':27,'upper_vertical_mm':3,
    'mesh_vertices':V,'mesh_edges':E,'mesh_triangles':F,'euler_characteristic':V-E+F,
    'mesh_closed_manifold':True,'winding_consistent':True,
    'mesh_volume_mm3':volume,'analytic_volume_mm3':exact_volume,
    'mesh_volume_relative_error':abs(volume-exact_volume)/exact_volume,
    'max_mesh_surface_error_bound_mm':max_chord_error,
    'ArtCAM_import_tested':False,'physical_accuracy_verified':False}
(OUT/'verification.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf8')

# Export the actual annotated DXF through the ezdxf CAD drawing backend.
drawdoc=ezdxf.readfile(OUT/'podoconnik_drawing_mm.dxf')
backend=svg.SVGBackend()
Frontend(RenderContext(drawdoc),backend,
    config=config.Configuration(background_policy=config.BackgroundPolicy.WHITE,
                                color_policy=config.ColorPolicy.BLACK)).draw_layout(drawdoc.modelspace(),finalize=True)
(OUT/'podoconnik_drawing.svg').write_text(backend.get_string(
    layout.Page(420,310,margins=layout.Margins(10,10,10,10)),
    settings=layout.Settings(min_stroke_width=0.25)),encoding='utf8')
import resvg_py
(OUT/'podoconnik_drawing.png').write_bytes(resvg_py.svg_to_bytes(
    svg_path=str(OUT/'podoconnik_drawing.svg'),width=2200,dpi=96))


# Responsive preview of the checked parametric model.
W,H=2000,1500
im=Image.new('RGB',(W,H),'#f5f7fa'); dr=ImageDraw.Draw(im)
def font(n): return ImageFont.truetype('C:/Windows/Fonts/arial.ttf',n)
def label(pos,s,n=25,color='#243244'): dr.text(pos,s,font=font(n),fill=color)
def line(ps,fill='#233447',width=3): dr.line(ps,fill=fill,width=width)
label((70,35),'ПОДОКОННИК · DXF + STL',40)
label((70,94),f'{L:g} × {D:g} × 30 мм   |   задняя часть {L-100:g} мм   |   HV R13,5',28)
label((70,139),'Габариты до выпуклой точки. Выступы по 50 мм, глубина выступов 50 мм.',24)
plan_scale=min(1600/L,310/D)
x0,y0=180,555
def pp(p): return (x0+p[0]*plan_scale,y0-p[1]*plan_scale)
dr.polygon([pp(p) for p in xy],fill='#e0e9f0',outline='#243244',width=3)
line([pp(p) for p in [(R,50),(R,R),(L-R,R),(L-R,50)]], '#197995',2)
for a,b in [((0,0),(R,R)),((L,0),(L-R,R))]: line([pp(a),pp(b)],'#197995',2)
label((x0+L*plan_scale*.38,y0-D*plan_scale*.65),'ВИД СВЕРХУ',26)
def hdim(x1,x2,y,txt,e1,e2):
    for x,e in [(x1,e1),(x2,e2)]:
        line([(x,e),(x,y+10)],'#748292',1)
        line([(x-5,y+7),(x+5,y-7)],'#465a6d',2)
    line([(x1,y),(x2,y)],'#465a6d',2)
    tw=dr.textlength(txt,font=font(23)); label(((x1+x2-tw)/2,y-30),txt,23)
hdim(x0,x0+L*plan_scale,y0+50,f'{L:g}',y0,y0)
yt=y0-D*plan_scale
hdim(x0+50*plan_scale,x0+(L-50)*plan_scale,yt-45,f'{L-100:g}',yt,yt)
xd=x0+L*plan_scale+50
line([(xd,yt),(xd,y0)],'#465a6d',2)
line([(x0+(L-50)*plan_scale,yt),(xd+10,yt)],'#748292',1)
line([(x0+L*plan_scale,y0),(xd+10,y0)],'#748292',1)
label((xd+12,(yt+y0)/2-15),f'{D:g}',23)
label((x0-65,y0-50*plan_scale/2-15),'50',22)
label((x0-7,y0-50*plan_scale-40),'50',22)
label((x0+L*plan_scale-35,y0-50*plan_scale-40),'50',22)
label((70,655),'СЕЧЕНИЕ HV · точная дуга R13,5',29)
cx,cy,sc=220,990,7
def cp(u,z): return(cx+u*sc,cy-z*sc)
cut_depth=min(75,D)
profile=[(cut_depth,30),(R,30),(R,27)]
profile += [(R+R*math.cos(t),R+R*math.sin(t)) for t in np.linspace(math.pi/2,3*math.pi/2,97)]
profile += [(cut_depth,0)]
dr.polygon([cp(*p) for p in profile],fill='#d5e5ed',outline='#243244',width=3)
label((790,829),'30 мм - полная толщина',24)
label((790,870),'27 мм - диаметр закругления',24)
label((790,911),'3 мм - верхний прямой участок',24)
line([cp(0,R),cp(R,R)],'#1b7894',2); label((cx+115,cy-123),'R13,5',23)
label((70,1030),f'Фрагмент сечения увеличен. Полная глубина в DXF - {D:g} мм.',22)
proj=lambda p: np.array([p[0]+0.65*p[1],-0.22*p[0]+0.5*p[1]+1.3*p[2]])
projected=np.array([proj(p) for p in vertices]); lo=projected.min(axis=0); hi=projected.max(axis=0)
fac=min(1770/(hi[0]-lo[0]),245/(hi[1]-lo[1]))
q=np.column_stack([100+(projected[:,0]-lo[0])*fac,1370-(projected[:,1]-lo[1])*fac])
order=sorted(range(len(faces)),key=lambda i: np.mean(vertices[list(faces[i])],axis=0).dot(np.array([-.65,1,-.5])),reverse=True)
for i in order:
    ids=list(faces[i]); a,b,c=vertices[ids]; normal=np.cross(b-a,c-a); normal/=np.linalg.norm(normal)
    if normal.dot(np.array([.65,-1,.494]))<=1e-8: continue
    light=.68+.25*abs(normal.dot(np.array([.2,-.3,.93])))
    dr.polygon([tuple(v) for v in q[ids]],fill=tuple(int(v*light) for v in (141,177,194)))
label((70,1090),'ПОЛНЫЙ ОБЪЁМ · острые углы, диагональные стыки',27)
label((70,1410),f'Предел отклонения сетки: {max_chord_error:.5f} мм. Геометрия проверена.',24)
label((70,1450),'Точность изготовления и импорт в ArtCAM в этой проверке не подтверждаются.',22)
im.save(OUT/'podoconnik_preview.png')
print(json.dumps(checks['geometry'],indent=2))
