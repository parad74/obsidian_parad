from pathlib import Path
import json,csv,math,hashlib,sys,argparse
import ezdxf
from ezdxf.path import make_path
from shapely.geometry import Polygon,LineString,Point,box
from shapely.ops import unary_union
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph,Table,TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor,white

ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--pdf',action='store_true');a=ap.parse_args()
out=a.output;out.mkdir(parents=True,exist_ok=True)
root=Path(r'W:\obsidian\_parad\Prompts\Jenja')
parts=[];holes=[];tabs=[];manifest={}
for n,L,x in [(2,1600,50),(3,2100,370),(4,1280,690)]:
 src=root/f'stone_project/artifacts/09122026/out{n-1}/cnc'
 load=lambda f:json.loads((src/'data'/f).read_text(encoding='utf-8'))
 doc=ezdxf.readfile(src/f'geometry/dvp_contour_R2_Y{L}.dxf')
 e=list(doc.modelspace().query('LWPOLYLINE'))[0]
 pts=[(p.x+x,p.y+50) for p in make_path(e).flattening(.0002)]
 shape=Polygon(pts)
 hp=[]
 with (src/'data/dvp_holes.csv').open(encoding='utf-8-sig') as f:
  for h in csv.DictReader(f):
   u,v=float(h['x'])+x,float(h['y'])+50
   item={'id':f'{n:03d}-H{h["id"]}','project':f'PARAD-{n:03d}','A_X':u,'A_Y':v,'B_X':u-50,'B_Y':v-50}
   holes.append(item);hp.append(Point(u,v).buffer(4,quad_segs=96))
 tp=[]
 for j,t in enumerate(load('tabs.json'),1):
  u,v=t['center'][0]+x,t['center'][1]+50
  tabs.append({'id':f'{n:03d}-T{j}','project':f'PARAD-{n:03d}','A_X':u,'A_Y':v,'B_X':u-50,'B_Y':v-50})
  axis=t['axis'];normal=t['normal']
  tp.append(Polygon([(u+k*axis[0]+z*normal[0],v+k*axis[1]+z*normal[1]) for k,z in [(-2.5,0),(2.5,0),(2.5,4),(-2.5,4)]]))
 sweeps=[];lines=[]
 for path in load('toolpaths.json'):
  if path['operation']!='01_dvp' or path['z']!=.3:continue
  points=[]
  for seg in path['segments']:
   if seg['kind']=='line':points.extend([seg['start'],seg['end']])
   else:
    count=256
    points.extend([(seg['center'][0]+seg['radius']*math.cos(seg['a']+(seg['b']-seg['a'])*i/count),seg['center'][1]+seg['radius']*math.sin(seg['a']+(seg['b']-seg['a'])*i/count)) for i in range(count+1)])
  line=LineString([(u+x,v+50) for u,v in points]);lines.append(line);sweeps.append(line.buffer(2,quad_segs=96))
 cut=unary_union(sweeps+hp)
 assert sum(cut.intersection(t).area for t in tp)<.001
 assert cut.intersection(shape).area<.02
 parts.append({'n':n,'L':L,'x':x,'y':50,'shape':shape,'cut':cut,'lines':lines,'vertices':list(e.get_points('xyb'))})
 for p in [src/f'geometry/dvp_contour_R2_Y{L}.dxf',src/'data/toolpaths.json',src/'data/tabs.json',src/'data/dvp_holes.csv']:
  manifest[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
sheet=box(0,0,1220,2710)
checks={'sheet_mm':[1220,2710,5],'quantities':{f'PARAD-{p["n"]:03d}':1 for p in parts},'NC_released':False,'physical_setup_checked':False,'geometry_checks':[]}
for p in parts:
 assert sheet.contains(p['cut'])
 for q in parts:
  if p is not q:assert p['cut'].distance(q['shape'])>0 and p['cut'].distance(q['cut'])>0
 checks['geometry_checks'].append({'project':p['n'],'sheet_origin':[p['x'],50],'cut_and_hole_bounds':list(p['cut'].bounds),'sheet_margin_min':p['cut'].distance(sheet.boundary)})
checks['inter_cut_min_mm']=min(p['cut'].distance(q['cut']) for p in parts for q in parts if p['n']<q['n'])
checks['holes']=len(holes);checks['tabs']=len(tabs)
for name,rows in [('holes',holes),('tabs',tabs)]:
 with (out/f'{name}_both_origins.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(out/'verification.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
(out/'sources.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
for label,zero in [('A_sheet',(0,0)),('B_part002',(50,50))]:
 d=ezdxf.new('R2000');d.units=4;m=d.modelspace()
 m.add_lwpolyline([(x-zero[0],y-zero[1]) for x,y in [(0,0),(1220,0),(1220,2710),(0,2710)]],close=True,dxfattribs={'layer':'SHEET'})
 for p in parts:
  m.add_lwpolyline([(u+p['x']-zero[0],v+50-zero[1],b) for u,v,b in p['vertices']],format='xyb',close=True,dxfattribs={'layer':f'PARAD_{p["n"]:03d}'})
 for h in holes:m.add_circle((h['A_X']-zero[0],h['A_Y']-zero[1]),4,dxfattribs={'layer':'PRE_DRILL_D8'})
 for t in tabs:m.add_point((t['A_X']-zero[0],t['A_Y']-zero[1]),dxfattribs={'layer':'TAB_CENTERS'})
 m.add_point((0,0),dxfattribs={'layer':'XY_ZERO'})
 d.saveas(out/f'layout_{label}.dxf')
 chk=ezdxf.readfile(out/f'layout_{label}.dxf');assert not chk.audit().errors and chk.units==4

steps=[
'Сверить лист ДВП 1220 × 2710 × 5 мм и три лекала: 1600, 2100 и 1280 мм, по одному. Толщина лекал 5 мм; 30 мм относится только к исходным каменным изделиям.',
'Выбрать один вариант XY0 из этого документа. Оба варианта дают одну и ту же раскладку; смешивать координаты A и B нельзя. Сейчас общая NC не выпускается.',
'До установки листа на станок разметить и просверлить 18 отверстий Ø8 в отходе по таблице. Для ручной разметки от угла листа использовать столбцы A, даже если позже выбран вариант B.',
'Установить лист: 1220 вдоль X, 2710 вдоль Y. Предусмотреть поддержку свеса 210 мм относительно указанного поля Y2500. Реальные ходы и положение листа проверить на станке.',
'Закрепить лист в свободных полях. Места и высоты прижимов ещё не измерены: проверить их относительно всего инструмента и будущих холостых переходов. Поля на схеме не являются проверкой крепления.',
'Установить торцевую фрезу Ø4. Z0 — поверхность стола; безопасный Z+45, то есть 40 мм над ДВП. XY0 задать по выбранной версии. Начальное положение должно уже обеспечивать безопасный подъём и движение.',
'После выбора версии подготовить и проверить одну общую AIR_XY NC: все движения на Z+45, без M3/M4/S. Не склеивать старые NC. Проверить координаты и переходы между тремя деталями, затем настройки A11S и установку перед физической проверкой.',
'План будущего резания (не выполняется этим документом): PARAD-002 → PARAD-003 → PARAD-004; каждое лекало полностью на двух уровнях Z+2,5 и Z+0,3, шесть участков между перемычками на каждом уровне. Вход через подготовленные отверстия. Недорез 0,3 мм, перемычки не прорезать.',
'Расчётная основа будущих режимов: XY800, Z100 мм/мин, 16000 об/мин; эти значения перенесены из согласованных ответов, не подтверждены новой пробой. Будущая AIR_XY не включает вращение. После резания отделить перемычки/недорез вручную и проверить лекала; один R2 у PARAD-004, по два R2 у остальных остаются без доводки.'
]
md='# Общий раскрой ДВП: два варианта XY0\n\nОдин лист 1220 × 2710 × 5 мм, по одному PARAD-002/003/004. Только схема для выбора; общей NC нет.\n\n[Открыть PDF: две версии](project_overview.pdf)\n\nРасположение в обеих версиях одинаково: начала габаритов от угла листа (50;50), (370;50), (690;50). Между габаритами 50 мм. Длины вдоль +Y. Вариант A: ноль листа. Вариант B: ноль PARAD-002, координаты A минус (50;50). Z не меняется.\n\n'
md+='\n\n'.join(f'{i}. {t}' for i,t in enumerate(steps,1))
md+='\n\nФайлы: layout_A_sheet.dxf, layout_B_part002.dxf — точные контуры с принятыми R2 и отверстиями; holes_both_origins.csv, tabs_both_origins.csv — координаты; verification.json — геометрические проверки; sources.json — контрольные суммы исходников. Поля/зазоры — предложение для сравнения, окончательную установку согласовать перед общей NC. Каменные файлы не изменены.\n'
(out/'README.md').write_text(md,encoding='utf-8')
if not a.pdf:print(json.dumps(checks,ensure_ascii=False));sys.exit()
pdfmetrics.registerFont(TTFont('Arial',r'C:\Windows\Fonts\arial.ttf'));pdfmetrics.registerFont(TTFont('ArialB',r'C:\Windows\Fonts\arialbd.ttf'))
c=canvas.Canvas(str(out/'project_overview.pdf'),pagesize=(595.28,841.89));c.setTitle('Раскрой ДВП - два варианта XY0');c.setAuthor('Parad')
style=ParagraphStyle('text',fontName='Arial',fontSize=10,leading=14,textColor=HexColor('#243b4b'))
small=ParagraphStyle('small',parent=style,fontSize=8,leading=10)
def para(t,x,y,w,st=style):
 p=Paragraph(t,st);_,h=p.wrap(w,750);p.drawOn(c,x,y-h);return y-h
def header(num,title,sub):
 c.setFillColor(HexColor('#24768a'));c.rect(0,828,596,14,fill=1,stroke=0)
 c.setFillColor(HexColor('#243b4b'));c.setFont('ArialB',19);c.drawString(35,788,title);para(sub,35,770,525,small)
 c.setFont('Arial',8);c.drawString(35,24,'Parad | ДВП | Сравнение вариантов, без выпуска общей NC');c.drawRightString(560,24,str(num))
def table(rows,y,widths):
 data=[[Paragraph(str(v),small) for v in row] for row in rows]
 t=Table(data,colWidths=widths);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#e9f1f3')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,-1),.35,HexColor('#c6d6dc'))]));_,h=t.wrap(525,750);t.drawOn(c,35,y-h);return y-h
def layout(version):
 sc=.17;ox=48;oy=205
 c.setStrokeColor(HexColor('#69808b'));c.rect(ox,oy,1220*sc,2710*sc)
 colors=['#dcecf4','#e2efe8','#f4e9dc']
 for p,col in zip(parts,colors):
  path=c.beginPath();pts=list(p['shape'].exterior.coords);path.moveTo(ox+pts[0][0]*sc,oy+pts[0][1]*sc)
  for u,v in pts[1:]:path.lineTo(ox+u*sc,oy+v*sc)
  path.close();c.setFillColor(HexColor(col));c.setStrokeColor(HexColor('#27728a'));c.drawPath(path,fill=1,stroke=1)
  c.saveState();c.translate(ox+(p['x']+130)*sc,oy+230*sc);c.rotate(90);c.setFont('ArialB',9);c.setFillColor(HexColor('#243b4b'));c.drawString(0,0,f'PARAD-{p["n"]:03d} / {p["L"]}');c.restoreState()
 for h in holes:c.setFillColor(HexColor('#c96828'));c.circle(ox+h['A_X']*sc,oy+h['A_Y']*sc,1.8,fill=1,stroke=0)
 for t in tabs:c.setFillColor(HexColor('#247f57'));c.rect(ox+t['A_X']*sc-1.5,oy+t['A_Y']*sc-1.5,3,3,fill=1,stroke=0)
 zero=(0,0) if version=='A' else (50,50);zx,zy=ox+zero[0]*sc,oy+zero[1]*sc
 c.setStrokeColor(HexColor('#bb3545'));c.setLineWidth(1.5);c.line(zx-5,zy,zx+5,zy);c.line(zx,zy-5,zx,zy+5);c.setFont('ArialB',9);c.setFillColor(HexColor('#bb3545'));c.drawString(zx+12,zy-15,'XY0 '+version)
 c.setFillColor(HexColor('#243b4b'));c.setFont('Arial',9);c.drawString(110,680,'1220 мм');c.saveState();c.translate(34,360);c.rotate(90);c.drawString(0,0,'2710 мм / +Y от оператора');c.restoreState();c.drawString(85,170,'Оператор; +X вправо')

header(1,'Три лекала на одном листе','ДВП 1220 × 2710 × 5 мм | два варианта нуля для выбора')
y=para('Обе версии имеют <b>одинаковое размещение</b>, одинаковые отверстия и перемычки. Меняется только ноль XY. Экономия материала и длина траекторий от смены нуля не меняются.',35,724,525)
y=table([['Лекало','Длина × глубина','Количество'],['PARAD-002','1600 × 270 мм',1],['PARAD-003','2100 × 270 мм',1],['PARAD-004','1280 × 270 мм',1]],y-20,[170,240,115])
y=para('Толщина всех лекал <b>5 мм</b>. PARAD-004: прямой левый торец, один правый выступ. Остальные: по два выступа. Длинная сторона вдоль Y; зеркального отражения и поворота деталей относительно отдельных расчётов нет.',35,y-20,525)
y=table([['Сравнение','A: угол листа','B: угол PARAD-002'],['XY0 от угла листа','(0; 0)','(50; 50)'],['Граница листа','X 0…1220; Y 0…2710','X -50…1170; Y -50…2660'],['Удобство','Прямой отсчёт разметки от листа','Совпадает с локальным нулём первого лекала'],['Проверка','Найти фактический угол листа','Точно отложить по 50 мм от двух краёв'] ],y-22,[125,200,200])
para('Предлагаю вариант A для общего листа: таблица разметки и рабочие координаты совпадают. Вариант B также пригоден при точной привязке. Выбор остаётся за вами.<br/><br/>Отступы от ближнего/левого края 50 мм, промежутки 50 мм. Справа от габарита крайнего лекала остаётся 260 мм, за самым длинным - 560 мм. Это не проверка реальных прижимов.',35,y-20,525)
c.showPage()
for page,v in [(2,'A'),(3,'B')]:
 header(page,f'Версия {v}: '+('ноль в углу листа' if v=='A' else 'ноль первого лекала'),'Одинаковая физическая раскладка; все размеры и координаты в миллиметрах')
 layout(v)
 shift=0 if v=='A' else 50
 y=para('<b>Начала габаритов:</b><br/>'+ '<br/>'.join(f'PARAD-{p["n"]:03d}: ({p["x"]-shift}; {50-shift})' for p in parts),288,655,270)
 y=para('<b>Разметка:</b> 18 отверстий Ø8 (оранжевые), 18 перемычек (зелёные). Маркеры увеличены. Координаты на следующих страницах.<br/><br/><b>Порядок:</b> 002 → 003 → 004. Два уровня каждого лекала, затем переход к следующему. Предложение до выпуска общей NC.',288,y-24,270)
 y=para('<b>Z одинаков в обеих версиях:</b><br/>Ноль - стол.<br/>Безопасная высота Z+45.<br/>План резания Z+2,5 и Z+0,3.<br/>В будущей AIR_XY только Z+45.<br/><br/>Смена XY0 не меняет привязку Z.',288,y-24,270)
 para('Проверено расчётом: контуры и отверстия внутри листа, фреза не задевает соседние лекала, перемычки сохраняются. Минимальный промежуток между зонами фрезерования/сверления соседних деталей: '+f'{checks["inter_cut_min_mm"]:.1f} мм.<br/>Прижимы, держатель и реальные ходы станка ещё не проверены.',35,124,525,small)
 c.showPage()
for page,title,rows in [(4,'Отверстия Ø8: обе версии',holes),(5,'Центры перемычек: обе версии',tabs)]:
 header(page,title,'Первые три цифры номера обозначают проект. X/Y заданы в выбранной системе координат.')
 data=[['Номер','A: X','A: Y','B: X','B: Y']]+[[t['id'],*[f'{t[k]:.3f}' for k in ['A_X','A_Y','B_X','B_Y']]] for t in rows]
 y=table(data,730,[105]*5)
 text='Отверстия сверлить до установки листа, чтобы не сверлить стол. Для разметки от угла листа брать A. Диаметр 8 мм, фреза 4 мм; отверстия полностью в отходе.' if page==4 else 'По 6 перемычек на лекало: две на каждой длинной стороне, одна на каждом торце. Высота 5 мм; минимальная ширина 5 мм через паз. Ось фрезы пропускает 9 мм с учётом круглых концов Ø4; у стенки изделия ширина 9 мм. Общий недорез 0,3 мм.'
 para(text,35,y-17,525,small);c.showPage()
header(6,'Порядок действий','Сейчас: схема для выбора. Общая NC будет отдельным результатом после выбора версии.')
y=735
for i,t in enumerate(steps,1):y=para(f'<b>{i}.</b> '+t,35,y,525)-13
assert y>48,y
c.save()
print('Created comparison PDF, 6 pages; no NC emitted.')

