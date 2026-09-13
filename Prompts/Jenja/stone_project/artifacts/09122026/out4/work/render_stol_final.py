from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).parent/'cadlib'))
import numpy as np,ezdxf,resvg_py
from PIL import Image,ImageDraw,ImageFont
from ezdxf.addons.drawing import Frontend,RenderContext,layout,svg,config
ROOT=Path(sys.argv[1]);data=np.load(ROOT/'work/model_arrays.npz');p=data['base'];q=data['envelope'];verts=data['vertices'];faces=data['faces']
def label(d,pos,s,n=25,fill='#243244'):d.text(pos,s,font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',n),fill=fill)
d=ezdxf.readfile(ROOT/'stol_drawing_mm.dxf');backend=svg.SVGBackend()
Frontend(RenderContext(d),backend,config=config.Configuration(background_policy=config.BackgroundPolicy.WHITE,color_policy=config.ColorPolicy.BLACK)).draw_layout(d.modelspace(),finalize=True)
(ROOT/'stol_drawing.svg').write_text(backend.get_string(layout.Page(297,420,margins=layout.Margins(12,12,12,12)),settings=layout.Settings(min_stroke_width=.2)),encoding='utf8')
(ROOT/'stol_drawing.png').write_bytes(resvg_py.svg_to_bytes(svg_path=str(ROOT/'stol_drawing.svg'),width=2000,dpi=96))

im=Image.new('RGB',(1800,1500),'#f5f7fa');dr=ImageDraw.Draw(im)
label(dr,(60,35),'СТОЛЕШНИЦА ОСТРОВА · ИТОГОВАЯ ОРИЕНТАЦИЯ',38)
label(dr,(60,95),'Поворот 5° против часовой стрелки. Профиль V R10, толщина 20 мм.',27)
label(dr,(75,175),'ВИД СВЕРХУ',28)
lo=q.min(0);sc=.42
def proj(v):return (100+(v[0]-lo[0])*sc,1290-(v[1]-lo[1])*sc)
dr.polygon([proj(v) for v in q],fill='#77b9c9',outline='#19798d',width=3)
dr.polygon([proj(v) for v in p],fill='#dce3e9',outline='#657b8d',width=2)
label(dr,(95,1320),'Серый: верхняя плоскость; голубой: вылет 10 мм.',22)
label(dr,(95,1360),'Габарит в ориентации листа:',25)
label(dr,(95,1400),'1596,721 × 2505,423 × 20 мм.',26)
label(dr,(950,185),'ПРОФИЛЬ V · РАЗРЕЗ',28)
angles=np.linspace(-np.pi/2,np.pi/2,100)
prof=[(-90,0),(0,0)]+[(10*np.cos(t),10+10*np.sin(t)) for t in angles]+[(-90,20)]
def pp(v):return (1540+v[0]*5,425-v[1]*5)
dr.polygon([pp(v) for v in prof],fill='#dce3e9',outline='#34475b',width=3)
dr.line([pp((0,0)),pp((0,20))],fill='#8095a4',width=2)
label(dr,(985,465),'Полукруг R10, высота 20 мм.',25)
label(dr,(985,505),'Вылет наружу от исходного края: 10 мм.',23)
label(dr,(950,620),'ПОЛНЫЙ ОБЪЁМ',28)
cam=np.array([[-.81,-.58,0],[.24,-.33,1.7]])
uv=verts@cam.T;uv[:,1]*=-1;span=np.ptp(uv,axis=0);uv=(uv-uv.min(0))*min(740/span[0],520/span[1])+[945,730]
normal=np.cross(verts[faces[:,1]]-verts[faces[:,0]],verts[faces[:,2]]-verts[faces[:,0]])
view=np.cross(cam[0],cam[1]);depth=verts@view;light=np.array([-.3,-.4,1]);light/=np.linalg.norm(light)
for idx in np.argsort(depth[faces].mean(1)):
 n=normal[idx]/np.linalg.norm(normal[idx])
 if n@view<=0:continue
 brightness=.72+.25*max(0,n@light)
 dr.polygon([tuple(v) for v in uv[faces[idx]]],fill=tuple(int(v*brightness) for v in (212,222,231)))
label(dr,(945,1320),'Одна замкнутая деталь, 135 330 треугольников.',22)
label(dr,(945,1360),'Форма и сетка сохранены при повороте.',24)
label(dr,(945,1400),'Импорт в ArtCAM не проверен.',24)
im.save(ROOT/'stol_preview.png')

im=Image.new('RGB',(1150,1780),'white');dr=ImageDraw.Draw(im)
label(dr,(55,25),'ЛИСТ 1645 × 3200 ММ · РАСКЛАДКА СТОЛЕШНИЦЫ',32)
label(dr,(55,82),'Поворот 5° против часовой стрелки. Контур и V R10 сохраняются.',25)
sc=.43;left=180;bottom=1560
def sp(v):return (left+v[0]*sc,bottom-v[1]*sc)
dr.polygon([sp(v) for v in [(0,0),(1645,0),(1645,3200),(0,3200)]],fill='#edf1f5',outline='#526b7f',width=3)
dr.polygon([sp(v) for v in q],fill='#75bbcb',outline='#26798b',width=3);dr.polygon([sp(v) for v in p],fill='#d3dce4',outline='#60798b',width=2)
label(dr,(430,140),'1645 мм',30);label(dr,(915,840),'3200 мм',26)
top=q[np.argmax(q[:,1])];tx,ty=sp(top);sy=sp((0,3200))[1]
dr.line([(tx,sy),(tx,ty)],fill='#b13b33',width=3)
for yy in [sy,ty]:dr.line([(tx-6,yy),(tx+6,yy)],fill='#b13b33',width=2)
dr.line([(tx,(sy+ty)/2),(910,220)],fill='#b13b33',width=2);label(dr,(925,209),'25 мм',24,'#b13b33')
label(dr,(285,1440),'Остаток снизу ≈ 669,6 мм',26)
label(dr,(55,1600),'Занимаемый габарит сетки: 1596,721 × 2505,423 мм.',27)
label(dr,(55,1645),'Запас по ширине: ≈ 24,14 мм с каждой стороны.',26)
label(dr,(55,1690),'Сверху: 25 мм от крайней точки кромки. Толщина 20 мм, вылет 10 мм.',25)
label(dr,(55,1730),'Геометрическая раскладка; припуск на конкретную обработку ещё не назначен.',21)
im.save(ROOT/'stock_1645x3200_rotation5.png')
print('Rendered actual DXF, transformed mesh and final placement.')
