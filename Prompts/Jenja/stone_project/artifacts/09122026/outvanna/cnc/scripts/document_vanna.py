"""Document the verified frame; no toolpaths are changed here."""
from pathlib import Path
import sys,json,csv,math,html
OUT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(OUT/'work/python_packages'))
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
c.setTitle('PARAD-016 - Рамка ванны из ДВП');c.setAuthor('Parad')
page=0
def text(s,x,y,size=10,bold=False,color='#253746'):
    c.setFillColor(colors.HexColor(color));c.setFont('AB' if bold else 'AR',size);c.drawString(x,y,s)
def para(s,x,y,width=507,st=style):
    p=Paragraph(s,st);_,height=p.wrap(width,700);p.drawOn(c,x,y-height);return y-height
def begin(title,subtitle):
    global page
    page+=1
    c.setFillColor(colors.HexColor('#12647b'));c.rect(0,H-12,W,12,fill=1,stroke=0)
    text('PARAD-016  /  06.11.2026',44,794,10,True)
    text(title,44,761,21,True)
    para(subtitle,44,740,507,small)
    text('Parad / outvanna / Расчётный комплект, на станке не испытан',44,25,8)
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

begin('Рамка ванны из ДВП','Одна деталь. Размеры в миллиметрах. Цветная область - сохраняемая рамка. Вид как на схеме производителя.')
x,y,s=75,430,.255
poly(P['outer_original'],x,y,s,fill='#ede4b8')
poly(P['inner_original'],x,y,s,fill='#ffffff',stroke='#12647b')
hdim(x,x+1730*s,y+810*s+24,'1730')
vdim(x-24,y,y+810*s,'810')
hdim(x+62.5*s,x+1667.5*s,y+405*s,'1605')
vdim(x+865*s,y+90*s,y+720*s,'630')
hdim(x+8*s,x+1722*s,y-24,'1714 между нижними вырезами')
y0=para('<b>Нижние углы:</b> два выреза 8 × 25 мм. Внутренний вырез по центру: отступы 62,5 мм слева/справа и 90 мм сверху/снизу.',44,365)
y0=para('<b>Форма выреза:</b> восстановлена по схематичному JPG с разрешения Parad. Прямые участки соединены гладкими симметричными кривыми. Точные радиусы производителя в исходнике отсутствуют; соответствие реальной ванне не проверено.',44,y0-16)
y0=para('<b>Углы после фрезы:</b> номинальные угловые вырезы остаются 8 × 25 мм на чертеже; в двух внутренних углах после Ø4 останется R2. Это остаток материала, без расширения рамки резом или добавления dogbone.',44,y0-16)
para('Комплект: размерный DXF, чистые контуры DXF, раскладка с осями инструмента, XYZ DXF, CUT и AIR_XY, координаты отверстий/перемычек, протокол проверок. PDF не является шаблоном для печати 1:1.',44,y0-16,st=small)
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

begin('Отверстия и перемычки','Отверстия Ø8 заранее просверлить в отходе до установки листа. Не сверлить стол. Одно отверстие используется на обоих уровнях своего контура.')
rows=[['Элемент','Рабочие X; Y','От листа X; Y','Размер']]
for i,plan in enumerate(paths,1):
    x,y=plan['hole'];tx,ty=plan['tab_center']
    rows.append([f'H{i} '+('внутренний' if i==1 else 'наружный'),f'{x:.3f}; {y:.3f}',f'{x+50:.3f}; {y+50:.3f}','Ø8, сквозное'])
    rows.append([f'T{i} перемычка',f'{tx:.3f}; {ty:.3f}',f'{tx+50:.3f}; {ty+50:.3f}','5 мин. × 1 по Z'])
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
y=para('<b>Файлы:</b> cnc/nc/VANNA_DVP_AIR_XY.nc - проверка XY; cnc/nc/VANNA_DVP_D4_CUT.nc - резание. AIR_XY не проверяет рабочие спуски Z и поведение материала.',44,y-16)
para('Тесты текущего проекта: cnc/test_checks. Проверка длительности - CHECK_DWELL_5S_NO_MOTION.nc; тест вращения без движения осей - CHECK_SPINDLE_16000_5S_NO_MOTION.nc. Последний включает шпиндель. Пауза 5 с задана по просьбе оператора через Parad 06.11.2026; дополнительная задержка пульта может увеличить паузу.',44,y-16,st=small)
end()

begin('Результаты проверок','Проверено повторным чтением записанных NC и DXF. Расчёт не заменяет проверку установки и испытание на станке.')
y=table([['Проверка','Результат'],['Габариты и положение','1730 × 810; вырез 1605 × 630 по центру; нижние уступы 8 × 25'],['DXF','Миллиметры; замкнутые контуры; аудит без ошибок'],['CUT','4 спуска в отверстия, минимальный Z0, внутренний контур раньше наружного'],['AIR_XY','XY совпадает с CUT; постоянный Z45; без запуска шпинделя'],['Геометрия Ø4','Зона инструмента в листе, зареза рамки за вычислительным допуском 0,003 мм нет'],['Перемычки','Две 5 × 1 мм; на уровне ниже Z1 части остаются связаны'],['Время подачи + явная пауза',f"{V['feed_plus_explicit_dwell_minutes']:.2f} мин; без G0, ускорений, задержек пульта и установки"]],44,680,[170,337])
y=para('Ниже - наложение восстановленной кривой (синяя) на исходную схему. Расхождение подбора к растру около '+f"{P['reconstruction']['rms_raster_fit_mm']:.2f}"+' мм является характеристикой изображения и аппроксимации, а не точностью изготовления.',44,y-18,st=small)
c.drawImage(str(OUT/'cnc/data/profile_overlay.png'),78,y-267.3,width=440,height=255.3,preserveAspectRatio=True,anchor='sw')
para('Материалы от \\Jenja\\: stone_project\\artifacts\\09122026\\outvanna - DXF, PDF и README; cnc\\nc - программы; cnc\\geometry - раскладка и XYZ; cnc\\data - параметры и проверки; cnc\\scripts - воспроизводимые скрипты. Вход: соседняя invanna.',44,92,507,small)
end();c.save()

# Preview for catalog; deterministic drawing of actual model, not a generated illustration.
im=Image.new('RGB',(1400,760),'white');draw=ImageDraw.Draw(im)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',26)
draw.text((50,25),'PARAD-016 | Рамка ванны | ДВП 5 мм',fill='#12647b',font=font)
xy=lambda pts:[(80+x*.7,670-y*.7) for x,y in pts]
draw.polygon(xy(P['outer_original']),fill='#ede4b8',outline='#253746',width=3)
draw.polygon(xy(P['inner_original']),fill='white',outline='#12647b',width=3)
draw.text((80,700),'1730 × 810 | Вырез 1605 × 630 | Нижние углы 8 × 25 мм',fill='#253746',font=font)
im.save(OUT/'vanna_preview.png')

pdf=pymupdf.open(OUT/'project_overview.pdf');assert len(pdf)==5
render=OUT/'work/pdf_pages';render.mkdir(parents=True,exist_ok=True)
for i,p in enumerate(pdf):
    assert p.get_text().strip()
    p.get_pixmap(matrix=pymupdf.Matrix(1.4,1.4)).save(render/f'page_{i+1}.png')
print('PDF: 5 pages, rendered for visual review')
