from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont

p=Path(__file__).resolve().parent
j=json.loads((p/'tangent_r315.json').read_text(encoding='utf-8'))
cx,cy=j['center_mm']; r=j['radius_mm']
W,H=1730,810
margin,top=55,115
im=Image.new('RGB',(W+2*margin,H+top+50),'white')
photo=Image.open(p/'rectified_assumption_v2.png')
im.paste(photo,(margin,top))
d=ImageDraw.Draw(im)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',25)
small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
blue='#b94d00'
def pt(x,y): return (margin+x,top+y)
def label(x,y,text):
    xy=pt(x,y);box=d.textbbox(xy,text,font=font,anchor='mm')
    d.rectangle((box[0]-6,box[1]-4,box[2]+6,box[3]+4),fill='white')
    d.text(xy,text,font=font,fill=blue,anchor='mm')
d.text((margin,12),'Расстояния от центра O до внешних сторон рамки 1730 × 810 мм',font=font,fill='black')
d.text((margin,49),'Приближённо: условная реконструкция по 630 мм. Справа пунктир — расчётная граница, вне фото.',font=small,fill='black')
d.text((margin,80),'Коричневая окружность R315; центр подбора маркера. Четыре перпендикуляра к сторонам.',font=small,fill='black')
d.line([pt(0,H),pt(0,0),pt(W,0)],fill=blue,width=2)
d.line([pt(0,H),pt(W,H)],fill=blue,width=2)
for y in range(0,H,16):d.line([pt(W,y),pt(W,min(H,y+8))],fill=blue,width=2)
d.ellipse((margin+cx-r,top+cy-r,margin+cx+r,top+cy+r),outline='#b94d00',width=2)
d.line([pt(0,cy),pt(W,cy)],fill=blue,width=2)
d.line([pt(cx,0),pt(cx,H)],fill=blue,width=2)
# Endpoint arrows point at the corresponding outer side.
for x,y,dx,dy in [(0,cy,1,0),(W,cy,-1,0),(cx,0,0,1),(cx,H,0,-1)]:
    tip=pt(x,y)
    d.polygon([tip,pt(x+12*dx-4*dy,y+12*dy+4*dx),pt(x+12*dx+4*dy,y+12*dy-4*dx)],fill=blue)
label(cx/2,cy-23,f'≈ {cx:.0f} мм')
label((cx+W)/2,cy-23,f'≈ {W-cx:.0f} мм')
label(cx+82,cy/2,f'≈ {cy:.0f} мм')
label(cx+82,(cy+H)/2,f'≈ {H-cy:.0f} мм')
d.ellipse((margin+cx-4,top+cy-4,margin+cx+4,top+cy+4),fill=blue)
label(cx+23,cy+24,'O')
label(cx+160,cy+65,'R = 315 мм')
dest=p/'center_to_outer_sides_r315.png'
assert not dest.exists(),'Preserve existing output'
im.save(dest)
distances=dict(left_mm=cx,right_mm=W-cx,top_mm=cy,bottom_mm=H-cy,
    basis='Conditional affine reconstruction. Outer 1730x810 from drawing; right edge outside photo, inferred.',
    horizontal_sum_mm=W,vertical_sum_mm=H)
(p/'center_to_outer_sides_r315.json').write_text(json.dumps(distances,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(distances,ensure_ascii=False))
