from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont

p=Path(__file__).resolve().parent;root=p.parent
sys.path.insert(0,str((root/'work/python_packages').resolve()))
import ezdxf
files=[root/'vanna_contours_mm.dxf',root/'vanna_dimensioned_mm.dxf',root/'cnc/nc/VANNA_DVP_D4_CUT.nc',root/'cnc/nc/VANNA_DVP_AIR_XY.nc']
hashes={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
e=ezdxf.readfile(files[0]).modelspace().query('LWPOLYLINE[layer=="INNER_RECONSTRUCTED"]')[0]
a=np.array(list(e.get_points('xy')))
actual=np.column_stack((1730-a[:,1],810-a[:,0]))
params=json.loads((root/'cnc/data/parameters.json').read_text())
new=json.loads((p/'tangent_r315.json').read_text())
oldcx=62.5+params['reconstruction']['cap_horizontal_semiaxis'];newcx=new['center_mm'][0]
W,H=1240,1450;scale=.65;left=55
im=Image.new('RGB',(W,H),'white');d=ImageDraw.Draw(im)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
bold=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',25)
green='#087b66';brown='#b94d00'
def panel(y0,cx,color,title,sub,old):
    d.text((left,y0),title,font=bold,fill=color)
    d.text((left,y0+36),sub,font=font,fill='black')
    ytop=y0+89
    def pt(x,y):return (left+x*scale,ytop+y*scale)
    d.rectangle((*pt(0,0),*pt(1730,810)),outline='#555555',width=2)
    if old:
        pts=[pt(x,y) for x,y in actual]
        d.line(pts+[pts[0]],fill=color,width=3)
    else:
        d.ellipse((*pt(cx-315,90),*pt(cx+315,720)),outline=color,width=3)
        for y in [90,720]:d.line([pt(cx,y),pt(1050,y)],fill=color,width=3)
    d.line([pt(0,405),pt(1730,405)],fill=color,width=1)
    d.line([pt(cx,0),pt(cx,810)],fill=color,width=1)
    def label(x,y,text):
        xy=pt(x,y);box=d.textbbox(xy,text,font=font,anchor='mm')
        d.rectangle((box[0]-4,box[1]-2,box[2]+4,box[3]+2),fill='white')
        d.text(xy,text,font=font,fill=color,anchor='mm')
    label(cx/2,375,f'{cx:.1f} мм')
    label((cx+1730)/2,375,f'{1730-cx:.1f} мм')
    label(cx+90,42,'405 мм');label(cx+90,768,'405 мм')
    label(cx+26,432,'C' if old else 'O')
    if old:
        label(870,535,'Полуоси торца: 326,66 × 315 мм')
        label(870,585,'Единого радиуса окружности нет')
    else:
        d.line([pt(cx,405),pt(cx+315,405)],fill=color,width=2)
        label(cx+160,470,'R = 315 мм')
        label(1130,585,'Рассчитан только левый торец')
    d.text((left,ytop+810*scale+14),'Внешний прямоугольник: 1730 × 810 мм. Координаты от верхнего левого угла.',font=font,fill='#444444')
panel(15,oldcx,green,'1. КАК В СОХРАНЁННОМ DXF И CUT','C — центр модели суперэллиптического торца, НЕ центр окружности.',True)
panel(710,newcx,brown,'2. НЫНЕШНЯЯ МОДЕЛЬ С КАСАНИЯМИ R315','O подобран по маркеру на условно выровненном фото; положение приблизительное.',False)
d.text((left,1408),'Программы резки не изменены. Разница привязок C и O: 17,3 мм; это центры разных моделей.',font=font,fill='black')
dest=p/'cut_vs_r315.png';assert not dest.exists();im.save(dest)
assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in hashes.items())
(p/'cut_vs_r315_file_hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
print('Saved comparison; four DXF/NC hashes unchanged.')
