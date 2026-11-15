"""Draw an engineering plate over the registered manufacturer sketch, in true millimetre proportions."""
from pathlib import Path
from io import BytesIO
import json
import math
import sys

from reportlab.lib.colors import HexColor, Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

out = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(out.parent/'outvanna/work/python_packages'))
import pymupdf

source = out.parent/'invanna2-11/photo_2026-11-06_20-17-19.jpg'
width, height = 1200, 825
buffer = BytesIO()
c = canvas.Canvas(buffer, pagesize=(width,height))
for name, filename in [('A','arial.ttf'),('B','arialbd.ttf')]:
    pdfmetrics.registerFont(TTFont(name, 'C:/Windows/Fonts/'+filename))
blue, green, rust = '#245d82', '#086758', '#a23e17'
ink, muted = '#233541', '#566b75'
left, top, scale = 133, 164, .54
right, bottom = left + 1730*scale, top + 810*scale
cx1, cx2 = left + 377.5*scale, left + 1352.5*scale
cy, radius = top + 405*scale, 304*scale

def label(x,y,txt,size=17,color=ink,align='center',bold=False,background=False):
    font = 'B' if bold else 'A'
    w = pdfmetrics.stringWidth(txt,font,size)
    x0 = x-w/2 if align=='center' else x
    if background:
        c.setFillColor(HexColor('#ffffff'))
        c.roundRect(x0-3,height-y-4,w+6,size+7,3,fill=1,stroke=0)
    c.setFillColor(HexColor(color)); c.setFont(font,size)
    c.drawString(x0,height-y,txt)

def line(x1,y1,x2,y2,color,lw=1):
    c.setStrokeColor(HexColor(color)); c.setLineWidth(lw)
    c.line(x1,height-y1,x2,height-y2)

def tip(x,y,dx,dy,color,size=7):
    a=math.atan2(dy,dx)
    for b in (a+.48,a-.48):
        line(x,y,x-size*math.cos(b),y-size*math.sin(b),color,1.2)

def circle(x,y,r,color,lw):
    c.setStrokeColor(HexColor(color)); c.setLineWidth(lw)
    c.circle(x,height-y,r,stroke=1,fill=0)

label(55,54,'Рамка ванны с выносом внутрь на 11 мм',34,ink,'left',True)
label(56,88,'Построение на схеме производителя. Все размеры в мм.',18,muted,'left')
label(600,138,'1730',18,ink,bold=True)
line(left,145,right,145,muted); tip(left,145,-1,0,muted); tip(right,145,1,0,muted)
# Register the four outer edges of the 855 x 496 source to the 1730 x 810 frame.
# The source has independent horizontal and vertical pixel scales.
sx, sy = 1730*scale/(796-82), 810*scale/(419-102)
ix, iy = left-82*sx, top-102*sy
c.saveState()
clip=c.beginPath(); clip.rect(left-3,height-bottom-3,right-left+6,bottom-top+6)
c.clipPath(clip,stroke=0,fill=0)
c.drawImage(str(source),ix,height-iy-496*sy,855*sx,496*sy)
c.setFillColor(Color(1,1,1,alpha=.84))
c.rect(left-3,height-bottom-3,right-left+6,bottom-top+6,stroke=0,fill=1)
c.restoreState()
outline=[(8,810),(1722,810),(1722,785),(1730,785),(1730,0),(0,0),(0,785),(8,785)]
for (x0,y0),(x1,y1) in zip(outline,outline[1:]+outline[:1]):
    line(left+x0*scale,top+y0*scale,left+x1*scale,top+y1*scale,ink,1.6)
line(left-28,top,left-28,bottom,muted)
tip(left-28,top,0,-1,muted); tip(left-28,bottom,0,1,muted)
label(left-55,cy,'810',16,ink,bold=True)
# Show the previous dimensioned contour as a reference distinct from the pixel sketch.
previous_radius = 315*scale
old_color = '#6e668c'
c.setDash(7,3)
for x,angle in ((cx1,90),(cx2,-90)):
    c.setStrokeColor(HexColor(old_color)); c.setLineWidth(1.1)
    c.arc(x-previous_radius,height-cy-previous_radius,x+previous_radius,height-cy+previous_radius,
          startAng=angle,extent=180)
for y in (cy-previous_radius,cy+previous_radius):
    line(cx1,y,cx2,y,old_color,1.1)
c.setDash()
mark_x = (cx1+cx2)/2 - 75
line(mark_x,cy-previous_radius-10,mark_x,cy-radius+12,ink,.8)
for y in (cy-previous_radius,cy-radius):
    line(mark_x-4,y,mark_x+4,y,ink,.8)
line(mark_x,cy-radius+12,mark_x+14,cy-radius+24,ink,.8)
label(mark_x+20,cy-radius+29,'11 мм внутрь',15,ink,'left',background=True)
# Dashed full construction circles. Solid outer halves and straight lines form the cut.
c.setDash(4,4)
for x in (cx1,cx2):
    circle(x,cy,radius,rust,1.3)
c.setDash()
for x,angle in ((cx1,90),(cx2,-90)):
    c.setStrokeColor(HexColor(green)); c.setLineWidth(2.8)
    c.arc(x-radius,height-cy-radius,x+radius,height-cy+radius,startAng=angle,extent=180)
for y in (cy-radius,cy+radius):
    line(cx1,y,cx2,y,green,2.8)

line(left,cy,right,cy,blue)
tip(left,cy,-1,0,blue);tip(right,cy,1,0,blue)
for x, name, sign in ((cx1,'O1',-1),(cx2,'O2',1)):
    line(x,top,x,bottom,blue)
    tip(x,top,0,-1,blue);tip(x,bottom,0,1,blue)
    label(x+8,(top+cy)/2,'405',16,blue,'left',background=True)
    label(x+8,(bottom+cy)/2+8,'405',16,blue,'left',background=True)
    c.setFillColor(HexColor(blue)); c.circle(x,height-cy,3.4,stroke=0,fill=1)
    label(x+10,cy+23,name,17,blue,'left',True,True)
    dx,dy=sign*radius*math.cos(.75),-radius*math.sin(.75)
    line(x,cy,x+dx,cy+dy,rust,1.4);tip(x+dx,cy+dy,dx,dy,rust)
    label(x+.6*dx,cy+.60*dy-8,'R304',18,rust,bold=True,background=True)
for x,y,msg in [((left+cx1)/2,cy-8,'377,5'),((cx1+right)/2,cy-8,'1352,5'),
                ((left+cx2)/2,cy+22,'1352,5'),((cx2+right)/2,cy+22,'377,5')]:
    label(x,y,msg,16,blue,background=True)
label(600,638,'Вырез 1583 × 608     •     Две прямые по 975     •     Нижние уступы 8 × 25',20,green,bold=True)
line(56,665,1144,665,'#cbd5d9')
label(56,698,'Поля рамки',20,ink,'left',True)
label(56,729,'73,5 мм слева и справа',17,ink,'left')
label(56,757,'101 мм сверху и снизу',17,ink,'left')
label(440,698,'Привязки центров',20,ink,'left',True)
label(440,729,'Над горизонталью — от O1',17,blue,'left')
label(440,757,'Под горизонталью — от O2',17,blue,'left')
label(825,698,'Линии на схеме',20,ink,'left',True)
label(825,729,'Зелёная — кромка выреза',17,green,'left')
label(825,757,'Коричневая — окружность R304',17,rust,'left')
label(825,783,'Сиреневая — исходный R315',16,old_color,'left')
label(56,802,'PARAD-028  /  15.11.2026',14,muted,'left')
c.showPage();c.save()
with pymupdf.open(stream=buffer.getvalue(),filetype='pdf') as doc:
    doc[0].get_pixmap(matrix=pymupdf.Matrix(2,2),alpha=False).save(out/'inset_11_r304_dimensioned.png')
