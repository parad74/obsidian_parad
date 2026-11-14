from pathlib import Path
import sys,json,math
import numpy as np
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(OUT.parent/'outvanna/work/python_packages'))
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
import pymupdf
r=json.loads((OUT/'fit_results.json').read_text(encoding='utf-8'))
f=r['pixel']['one'];cx,cy=f['center'];rp=f['radius'];R=306.5
chord_offset=0
angle=180
pdfmetrics.registerFont(TTFont('AR','C:/Windows/Fonts/arial.ttf'));pdfmetrics.registerFont(TTFont('AB','C:/Windows/Fonts/arialbd.ttf'))
pdfmetrics.registerFontFamily('AR',normal='AR',bold='AB')
sty=ParagraphStyle('p',fontName='AR',fontSize=11,leading=15,textColor=colors.HexColor('#253746'))
c=canvas.Canvas(str(OUT/'project_overview.pdf'),pagesize=(842,595));c.setTitle('PARAD-018 - Окружность зелёного сегмента');c.setAuthor('Parad')
def text(s,x,y,size=11,bold=False,color='#253746'):
    c.setFont('AB' if bold else 'AR',size);c.setFillColor(colors.HexColor(color));c.drawString(x,y,s)
def para(s,x,y,w):
    p=Paragraph(s,sty);_,h=p.wrap(w,500);p.drawOn(c,x,y-h);return y-h
def heading(sub):
    text('PARAD-018 / Геометрия по схеме производителя / 12.11.2026',35,566,10)
    text(sub,35,535,23,True)
def foot(n):text('Исследование изображения. Не является подтверждённым производственным чертежом.',35,20,9);text(str(n),800,20,9)
heading('По размерам: полукруглый торец R306,5 мм')
para('Основа - размер 613 мм. Выбран вариант полукруга, а не масштабирование фотографии.',35,510,770)
ox,oy,rad=460,290,170
q=0;a=math.acos(-q)
ts=np.linspace(a,2*math.pi-a,500)
path=c.beginPath();path.moveTo(ox+rad*math.cos(ts[0]),oy+rad*math.sin(ts[0]))
for t in ts[1:]:path.lineTo(ox+rad*math.cos(t),oy+rad*math.sin(t))
path.close();c.setFillColor(colors.HexColor('#b6e52b'));c.drawPath(path,fill=1,stroke=0)
c.setStrokeColor(colors.HexColor('#1266bc'));c.setLineWidth(2);c.circle(ox,oy,rad,fill=0)
c.setStrokeColor(colors.HexColor('#253746'));c.setLineWidth(2)
p=c.beginPath();p.moveTo(ox+rad*math.cos(ts[0]),oy+rad*math.sin(ts[0]))
for t in ts[1:]:p.lineTo(ox+rad*math.cos(t),oy+rad*math.sin(t))
c.drawPath(p,stroke=1)
gx=ox-q*rad;gy=rad*math.sqrt(1-q*q)
c.setStrokeColor(colors.HexColor('#2aa54c'));c.setLineWidth(2.5);c.line(gx,oy-gy,gx,oy+gy)
c.setStrokeColor(colors.HexColor('#879ca9'));c.setLineWidth(.6);c.setDash(4,3);c.line(ox-rad-20,oy,ox+rad+20,oy);c.line(ox,oy-rad-12,ox,oy+rad+12);c.setDash()
c.setStrokeColor(colors.HexColor('#b83a32'));c.setLineWidth(1.5);c.line(ox,oy,ox-rad,oy)
text('R = 306,5 мм',ox-rad+35,oy+10,13,True,color='#b83a32')
for x,y in [(ox,oy),(ox-rad,oy)]:
    c.setStrokeColor(colors.HexColor('#1266bc'));c.line(x-5,y,x+5,y);c.line(x,y-5,x,y+5);c.circle(x,y,2,fill=0)
text('O',ox+10,oy-19,15,True);text('A',ox-rad-16,oy-20,14,True)
c.setStrokeColor(colors.HexColor('#657988'));c.line(670,oy-rad,670,oy+rad)
for yy in [oy-rad,oy+rad]:c.line(662,yy,678,yy)
c.saveState();c.translate(686,oy);c.rotate(90);text('Диаметр 613 мм',-55,0,12,True);c.restoreState()
para('<b>Центр O</b><br/>На середине высоты.<br/>306,5 мм вправо от крайней левой точки A.',35,440,220)
para('<b>Отсчёт от A</b><br/>X вправо, Y вверх.<br/>A = (0; 0)<br/>O = (306,5; 0) мм.',35,340,205)
para('<b>Две четверти</b><br/>Верхняя и нижняя:<br/>R1 = R2 = 306,5 мм.<br/>O1 = O2 = O.<br/>Один общий центр.',35,235,205)
para('Зелёным показан расчётный полукруг: две четверти по 90° с общим центром. Вспомогательная зелёная вертикаль исходника исключена из геометрии по указанию Parad.',35,84,770)
foot(1);c.showPage()
heading('Что определяют числа на схеме')
para('<b>613 мм</b> - высота внутреннего выреза. Для выбранного полукруглого торца это диаметр: R = 613 / 2 = <b>306,5 мм</b>. Центр находится на середине высоты и на 306,5 мм вправо от крайней левой точки.',40,490,750)
para('<b>1583 мм</b> - общая длина внутреннего выреза. Если оба его торца полукруглые с R306,5, длина каждого прямого участка между ними: 1583 - 2 × 306,5 = <b>970 мм</b>. Это проверка согласованности выбранного варианта, не дополнительный размер с картинки.',40,407,750)
para('<b>1730 × 810 мм</b> - наружный габарит рамки. Он не задаёт радиус внутреннего выреза. При явно заданном центральном расположении выреза поля были бы 73,5 мм по длине и 98,5 мм по высоте; центровка на этой картинке отдельно размером не указана и в расчёт центра относительно рамки не принята.',40,309,750)
para('<b>Можно ли доказать два разных центра?</b> Нет. Размеры высоты и длины сами по себе не определяют произвольную кривую, радиусы двух разных дуг и точку их соединения. Показанный вариант использует один полукруг: две его четверти имеют общий центр. Для иного варианта нужны размеры точки стыка/касания или радиусы.',40,207,750)
para('<b>Уточнение Parad:</b> ориентироваться на цифры. Поэтому итоговая схема не использует масштаб изображения, пиксельный радиус или измеренное по растру положение зелёной вертикали. Это размерное построение выбранной круговой формы, а не доказательство формы производителя.',40,101,750)
foot(2);c.save()
doc=pymupdf.open(OUT/'project_overview.pdf')
for i,page in enumerate(doc):page.get_pixmap(matrix=pymupdf.Matrix(1.6,1.6)).save(OUT/('circle_diagram.png' if i==0 else 'dimension_constraints.png'))
for page in doc:
    for b in page.get_text('blocks'):assert b[0]>=0 and b[1]>=0 and b[2]<=842 and b[3]<=595,b[:4]
print('2 PDF pages rendered; center difference px:',0,'green angle:',angle,'chord offset conditional mm:',chord_offset)
