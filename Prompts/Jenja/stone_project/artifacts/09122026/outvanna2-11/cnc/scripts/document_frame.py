"""Document the verified frame; no toolpaths are changed here."""
from pathlib import Path
import sys,json,csv,math,html
OUT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(OUT.parent/'outvanna/work/python_packages'))
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph,Table,TableStyle
from reportlab.lib.styles import ParagraphStyle
from PIL import Image,ImageDraw,ImageFont
import pymupdf

P=json.loads((OUT/'cnc/data/parameters.json').read_text(encoding='utf-8'))
V=json.loads((OUT/'cnc/data/verification.json').read_text(encoding='utf-8'))
paths=json.loads((OUT/'cnc/data/paths.json').read_text(encoding='utf-8'))
pdfmetrics.registerFont(TTFont('AR','C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('AB','C:/Windows/Fonts/arialbd.ttf'))
pdfmetrics.registerFontFamily('AR',normal='AR',bold='AB',italic='AR',boldItalic='AB')
style=ParagraphStyle('body',fontName='AR',fontSize=10,leading=14,textColor=colors.HexColor('#253746'))
small=ParagraphStyle('small',parent=style,fontSize=8.5,leading=11.5)
W,H=595.276,841.89
c=canvas.Canvas(str(OUT/'project_overview.pdf'),pagesize=(W,H))
c.setTitle('PARAD-028 - Рамка ванны с выносом внутрь на 11 мм');c.setAuthor('Parad')
page=0
def text(s,x,y,size=10,bold=False,color='#253746'):
    c.setFillColor(colors.HexColor(color));c.setFont('AB' if bold else 'AR',size);c.drawString(x,y,s)
def para(s,x,y,width=507,st=style):
    p=Paragraph(s,st);_,height=p.wrap(width,700);p.drawOn(c,x,y-height);return y-height
def begin(title,subtitle):
    global page
    page+=1
    c.setFillColor(colors.HexColor('#12647b'));c.rect(0,H-12,W,12,fill=1,stroke=0)
    text('PARAD-028  /  15.11.2026',44,794,10,True)
    text(title,44,761,21,True)
    para(subtitle,44,740,507,small)
    text('Parad / outvanna2-11 / Расчётный комплект, на станке не испытан',44,25,8)
    text(str(page),535,25,8)
def end():c.showPage()
def poly(points,x,y,scale,fill=None,stroke='#253746',width=1):
    p=c.beginPath();p.moveTo(x+points[0][0]*scale,y+points[0][1]*scale)
    for px,py in points[1:]:p.lineTo(x+px*scale,y+py*scale)
    p.close();c.setStrokeColor(colors.HexColor(stroke));c.setLineWidth(width)
    if fill:c.setFillColor(colors.HexColor(fill))
    c.drawPath(p,stroke=1,fill=bool(fill))
def hdim(x1,x2,y,label):
    c.setStrokeColor(colors.HexColor('#657988'));c.setLineWidth(.6);c.line(x1,y,x2,y)
    for x in (x1,x2):c.line(x,y-5,x,y+5)
    c.setFont('AB',10);c.setFillColor(colors.HexColor('#12647b'));c.drawCentredString((x1+x2)/2,y+7,label)
def vdim(x,y1,y2,label):
    c.setStrokeColor(colors.HexColor('#657988'));c.line(x,y1,x,y2)
    c.line(x-5,y1,x+5,y1);c.line(x-5,y2,x+5,y2)
    c.saveState();c.translate(x-8,(y1+y2)/2);c.rotate(90);c.setFillColor(colors.HexColor('#12647b'));c.setFont('AB',10);c.drawCentredString(0,0,label);c.restoreState()
def table(rows,x,y,widths):
    cells=[[Paragraph(html.escape(str(v)),small) for v in row] for row in rows]
    t=Table(cells,colWidths=widths)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7f0f3')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#b7c7ce')),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    _,height=t.wrap(510,700);t.drawOn(c,x,y-height);return y-height

begin('Исходный чертёж производителя', 'Одна рамка для ванны из ДВП 5 мм. Размеры указаны в миллиметрах.')
c.drawImage(str(OUT/P['source']),42,340,width=511,height=338,preserveAspectRatio=True)
para('На исходной схеме указан вырез 1605 × 630 мм. В выпуске PARAD-028 рамка расширена внутрь по всему контуру на 11 мм. Новый размер для изготовления — 1583 × 608 мм. Наружный габарит 1730 × 810 мм, нижние уступы 8 × 25 мм, между уступами 1714 мм.',44,265)
para('Входной файл: invanna2-11/photo_2026-11-06_20-17-19.jpg. Согласованное размерное построение приведено на следующей странице.',44,173)
end()

begin('Окружности и привязки центров','Новый контур построен на исходной схеме. На прямых отложено 11 мм по перпендикуляру, на дугах радиус уменьшен с 315 до 304 мм при тех же центрах.')
c.drawImage(str(OUT/P['overlay']),20,241,width=555,height=449,preserveAspectRatio=True)
para('Центры O1 и O2 находятся на общей средней линии, по 405 мм от верха и низа. От левого края их координаты равны 377,5 и 1352,5 мм. До ближайшего короткого края от каждого центра 377,5 мм. Центр рамки O находится на 865 мм от левого края.',44,193)
para('Вырез 1583 × 608 мм образуют две полуокружности R304 и две прямые по 975 мм. Прямые касаются дуг на высотах 101 и 709 мм. Крайние точки выреза по длине рамки: 73,5 и 1656,5 мм.',44,119)
end()

begin('Размещение на листе','Рабочий XY0 находится в габаритном углу рамки. От физического ближнего левого угла листа до XY0: X50, Y50.')
sx,sy,ss=60,180,.18
poly([(0,0),(1220,0),(1220,2710),(0,2710)],sx,sy,ss,fill='#f1f5f6',stroke='#657988')
rot=lambda pts:[(y+50,1730-x+50) for x,y in pts]
poly(rot(P['outer_original']),sx,sy,ss,fill='#ede4b8')
poly(rot(P['inner_original']),sx,sy,ss,fill='#ffffff',stroke='#12647b')
for i,plan in enumerate(paths,1):
    hx,hy=plan['hole'];tx,ty=plan['tab_center']
    c.setFillColor(colors.HexColor('#c75521'));c.circle(sx+(hx+50)*ss,sy+(hy+50)*ss,3,stroke=0,fill=1)
    text('H'+str(i),sx+(hx+50)*ss+5,sy+(hy+50)*ss+8,8,True)
    c.setStrokeColor(colors.HexColor('#a72c89'));c.setLineWidth(3)
    c.line(sx+(tx+50)*ss,sy+(ty+50)*ss-3, sx+(tx+50)*ss,sy+(ty+50)*ss+3)
text('XY0',sx+12,sy+16,9,True);c.setStrokeColor(colors.HexColor('#12647b'));c.line(sx+9,sy+9,sx+36,sy+9);c.line(sx+9,sy+9,sx+9,sy+36)
hdim(sx,sx+1220*ss,sy-25,'1220 / X вправо')
vdim(sx-20,sy,sy+2710*ss,'2710 / Y от оператора')
para('<b>Ориентация</b><br/>1730 вдоль Y.<br/>810 вдоль X.<br/>Поворот без отражения:<br/>X = y исходной схемы;<br/>Y = 1730 - x исходной схемы.',310,660,235)
para('<b>Порядок</b><br/>1. Внутренний контур, оба уровня.<br/>2. Наружный контур, оба уровня.<br/>3. Подъём Z45, M5, возврат XY0.',310,530,235)
para('<b>Установка</b><br/>Механические прижимы вне траекторий - по подтверждению Parad. Их координаты и высоты не измерены. Проверить проход держателя, включая возврат XY0.',310,410,235)
para('Лист 2710 мм длиннее указанного поля Y2500 на 210 мм. Поддержать свес в плоскости стола. Обрабатываемая деталь занимает Y50…1780 от края листа.',310,285,235,small)
para('Оранжевый - отверстия Ø8; пурпурный - перемычки (маркеры увеличены). Заготовка лежит на столе, подложки нет. Z0 - стол, отрицательных Z в программе нет.',44,115,507,small)
end()

begin('Нижние угловые вырезы','Два уступа 8 × 25 мм. Слева показан нижний левый угол рамки в ориентации исходного чертежа. Справа увеличена его вогнутая вершина.')
x,y,s=75,420,6
poly([(0,25),(8,25),(8,0),(32,0),(32,45),(0,45)],x,y,s,fill='#efe8c7')
hdim(x,x+8*s,y-15,'8');vdim(x-12,y,y+25*s,'25')
x,y,s=325,460,35
c.setStrokeColor(colors.HexColor('#526a76'));c.setDash(3,2);c.line(x,y+2*s,x+2*s,y+2*s);c.line(x+2*s,y+2*s,x+2*s,y);c.setDash()
c.setStrokeColor(colors.HexColor('#a55220'));c.setLineWidth(2)
c.arc(x-2*s,y-2*s,x+2*s,y+2*s,startAng=0,extent=90)
c.line(x-35,y+2*s,x,y+2*s);c.line(x+2*s,y,x+2*s,y-32)
text('R2',x+22,y+26,12,True,'#a55220')
para('Пунктир показывает номинальную острую вершину. Сплошная дуга показывает кромку после прохода фрезой Ø4. Размеры уступа на прямых участках сохраняются. Второй нижний угол зеркален первому.',44,335)
para('В DXF раскладки этим контурам соответствуют слои OUTER_NOMINAL и EFFECTIVE_OUTER_R2. Между нижними вырезами по прямой 1714 мм.',44,244)
end()

begin('Отверстия и перемычки','Отверстия Ø8 заранее просверлить в отходе до установки листа. Не сверлить стол. Одно отверстие используется на обоих уровнях своего контура.')
rows=[['Элемент','Рабочие X; Y','От листа X; Y','Размер']]
for i,plan in enumerate(paths,1):
    x,y=plan['hole'];tx,ty=plan['tab_center']
    rows.append([f'H{i} '+('внутренний' if i==1 else 'наружный'),f'{x:.3f}; {y:.3f}',f'{x+50:.3f}; {y+50:.3f}','Ø8, сквозное'])
    rows.append([f'T{i} перемычка',f'{tx:.3f}; {ty:.3f}',f'{tx+50:.3f}; {ty+50:.3f}','ширина ≥5 мм, высота 1 мм'])
y=table(rows,44,680,[122,130,130,125])
y=para('<b>Вход:</b> Z45 → XY отверстия → Z7 → рабочий Z на F100; затем боковой выход на ось контура на F800. Центр отверстия отстоит от номинальной границы на 8 мм, от оси реза на 6 мм.',44,y-20)
y=para('<b>Перемычка:</b> участок осевой траектории длиной 9 мм оставлен на Z+1 на последнем проходе. Ø4 закругляет концы реза, поэтому минимальная остающаяся ширина через паз - 5 мм. По одной перемычке на каждом контуре, на прямом участке возле начала/замыкания.',44,y-16)
y=para('Первый проход полностью на Z+2,5. Второй: основной контур на Z0, подъём до Z+1 перед перемычкой, проход по перемычке и отвод к отверстию. Остаток 1 мм снимается вручную после остановки и извлечения детали.',44,y-16)
y=para('Одна тонкая перемычка на контур - согласованный выбор. Статическая геометрия сохраняет связь детали и внутренней части с листом; прочность удержания и поведение при вибрации расчётом не подтверждены.',44,y-16)
para('Номинальное Z0 совпадает со столом. При неровности листа или погрешности привязки возможно неполное прорезание либо касание стола. В файле нет команды ниже Z0.',44,y-16)
end()

begin('Программы и проверка запуска','MORN1325 / RichAuto A11S. Расчётный G-код создан скриптом, не экспортом ArtCAM. CUT запускает шпиндель и входит в материал.')
y=table([['Параметр','Значение'],['Инструмент / материал','Однозубая Ø4 / ДВП 5 мм'],['Обороты / подача XY / подача Z','S16000 / F800 / F100'],['Рабочие уровни от стола','Z+2,5; Z0; на перемычках последнего прохода Z+1'],['Подвод / переходы','Z+7 в отверстии / Z+45'],['Выдержка после M3','G04 P5000 - 5 с по указанию оператора'],['Компенсация','Ось уже смещена на радиус 2 мм; G40, повторную компенсацию не добавлять'],['AIR_XY','Все движения на Z45; без M3/M4 и S'] ],44,680,[170,337])
y=para('<b>Перед CUT:</b> проверить диаметр фрезы, плоское прилегание, привязки XY/Z, заранее просверленные отверстия и свободный ход держателя; исходное положение выше материала. Проверить выдержку и разгон шпинделя сохранёнными отдельными тестами, затем AIR_XY новой рамки.',44,y-18)
y=para('<b>Файлы:</b> cnc/nc/VANNA11_R304_AIR_XY.nc - проверка XY; cnc/nc/VANNA11_R304_D4_CUT.nc - резание. AIR_XY не проверяет рабочие спуски Z и поведение материала.',44,y-16)
para('Тесты текущего проекта: cnc/test_checks. Проверка длительности - CHECK_DWELL_5S_NO_MOTION.nc; тест вращения без движения осей - CHECK_SPINDLE_16000_5S_NO_MOTION.nc. Последний включает шпиндель. Пауза 5 с задана общим правилом для ДВП; дополнительная задержка пульта может увеличить паузу.',44,y-16,st=small)
end()

begin('Результаты проверок','Проверено повторным чтением записанных NC и DXF. Расчёт не заменяет проверку установки и испытание на станке.')
y=table([['Проверка','Результат'],['Габариты и положение','1730 × 810; вырез 1583 × 608 по центру; нижние уступы 8 × 25'],['DXF','Миллиметры; замкнутые контуры; аудит без ошибок'],['Вынос внутрь','Оба прямых участка смещены на 11 мм. Обе дуги уменьшены на 11 мм при совпадающих центрах'],['CUT','4 спуска в отверстия, минимальный Z0, внутренний контур раньше наружного'],['AIR_XY','XY совпадает с CUT; постоянный Z45; без запуска шпинделя'],['Геометрия Ø4','Зона инструмента в листе, зареза рамки за вычислительным допуском 0,003 мм нет'],['Перемычки','Две 5 × 1 мм; на уровне ниже Z1 части остаются связаны'],['Время подачи + явная пауза',f"{V['feed_plus_explicit_dwell_minutes']:.2f} мин; без G0, ускорений, задержек пульта и установки"]],44,680,[170,337])
y=para('Номинальный DXF хранит две точные дуги R304 и две прямые 975 мм. В CUT ось фрезы проходит по торцам R302 последовательностью отрезков G1. На 2055 проверенных точках и серединах отрезков отклонение оси от расчётного профиля менее 0,002 мм. Это результат проверки файла.',44,y-18)
para('Файлы модели: frame11_contours_mm.dxf, frame11_dimensioned_mm.dxf. Для импорта в старые редакторы предусмотрен frame11_contours_R12_mm.dxf (мм, 1:1). Папки: cnc/geometry (лист и XYZ), cnc/nc (CUT и AIR_XY), cnc/data (CSV разметки, параметры, протоколы), cnc/test_checks и cnc/scripts. Время полного цикла зависит от быстрых ходов, ускорений и работы пульта. Физическая проверка установки и посадки предстоит.',44,y-108,st=small)
end();c.save()

# Preview for catalog; deterministic drawing of actual model, not a generated illustration.
im=Image.new('RGB',(1400,760),'white');draw=ImageDraw.Draw(im)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',26)
draw.text((50,25),'PARAD-028 | Рамка ванны с выносом внутрь 11 мм | ДВП 5 мм',fill='#12647b',font=font)
xy=lambda pts:[(80+x*.7,670-y*.7) for x,y in pts]
draw.polygon(xy(P['outer_original']),fill='#ede4b8',outline='#253746',width=3)
draw.polygon(xy(P['inner_original']),fill='white',outline='#12647b',width=3)
draw.text((80,700),'1730 × 810 | Вырез 1583 × 608 | Нижние углы 8 × 25 мм',fill='#253746',font=font)
im.save(OUT/'frame11_preview.png')

pdf=pymupdf.open(OUT/'project_overview.pdf');assert len(pdf)==page
render=OUT/'work/pdf_pages';render.mkdir(parents=True,exist_ok=True)
for i,p in enumerate(pdf):
    assert p.get_text().strip()
    p.get_pixmap(matrix=pymupdf.Matrix(1.4,1.4)).save(render/f'page_{i+1}.png')
print(f'PDF: {page} pages, rendered for visual review')
