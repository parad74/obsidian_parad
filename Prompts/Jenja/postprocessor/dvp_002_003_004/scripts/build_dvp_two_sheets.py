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
placements=[(1,'002',2,1600,50,50),(1,'003',3,2100,370,50),(1,'004',4,1280,690,50)]
placements += [(2,f'002-{i+1}',2,1600,40+290*i,50+100*(i%2)) for i in range(4)]
for sheet_id,ident,n,L,x,y in placements:
 zx,zy=(50,50) if sheet_id==1 else (40,50)
 src=root/f'stone_project/artifacts/09122026/out{n-1}/cnc'
 load=lambda f:json.loads((src/'data'/f).read_text(encoding='utf-8'))
 doc=ezdxf.readfile(src/f'geometry/dvp_contour_R2_Y{L}.dxf')
 e=list(doc.modelspace().query('LWPOLYLINE'))[0]
 pts=[(p.x+x,p.y+y) for p in make_path(e).flattening(.0002)]
 shape=Polygon(pts)
 hp=[]
 with (src/'data/dvp_holes.csv').open(encoding='utf-8-sig') as f:
  for h in csv.DictReader(f):
   u,v=float(h['x'])+x,float(h['y'])+y
   item={'id':f'{ident}-H{h["id"]}','sheet':sheet_id,'project':f'PARAD-{n:03d}','A_X':u,'A_Y':v,'B_X':u-zx,'B_Y':v-zy}
   holes.append(item);hp.append(Point(u,v).buffer(4,quad_segs=96))
 tp=[]
 for j,t in enumerate(load('tabs.json'),1):
  u,v=t['center'][0]+x,t['center'][1]+y
  tabs.append({'id':f'{ident}-T{j}','sheet':sheet_id,'project':f'PARAD-{n:03d}','A_X':u,'A_Y':v,'B_X':u-zx,'B_Y':v-zy})
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
  line=LineString([(u+x,v+y) for u,v in points]);lines.append(line);sweeps.append(line.buffer(2,quad_segs=96))
 cut=unary_union(sweeps+hp)
 assert sum(cut.intersection(t).area for t in tp)<.001
 assert cut.intersection(shape).area<.02
 parts.append({'n':n,'L':L,'x':x,'y':y,'sheet':sheet_id,'ident':ident,'shape':shape,'cut':cut,'lines':lines,'vertices':list(e.get_points('xyb'))})
 for p in [src/f'geometry/dvp_contour_R2_Y{L}.dxf',src/'data/toolpaths.json',src/'data/tabs.json',src/'data/dvp_holes.csv']:
  manifest[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
sheet=box(0,0,1220,2710)
checks={'sheet_mm':[1220,2710,5],'selected_origin':'B','NC_released':False,'sheets':{}}
for sid in (1,2):
 ps=[p for p in parts if p['sheet']==sid]
 for p in ps:
  assert sheet.contains(p['cut'])
  for q in ps:
   if p is not q:assert p['cut'].distance(q['shape'])>0 and p['cut'].distance(q['cut'])>0
 checks['sheets'][sid]={'placements':[{'id':p['ident'],'xy_from_sheet':[p['x'],p['y']]} for p in ps],
  'minimum_gap_between_cut_and_drill_zones_mm':min(p['cut'].distance(q['cut']) for i,p in enumerate(ps) for q in ps[i+1:]),
  'minimum_sheet_margin_cut_and_drill_mm':min(p['cut'].distance(sheet.boundary) for p in ps),'holes':6*len(ps),'tabs':6*len(ps)}
 for kind,allrows in [('holes',holes),('tabs',tabs)]:
  rows=[t for t in allrows if t['sheet']==sid]
  with (out/f'sheet{sid}_{kind}.csv').open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 zero=(50,50) if sid==1 else (40,50)
 d=ezdxf.new('R2000');d.units=4;m=d.modelspace()
 m.add_lwpolyline([(x-zero[0],y-zero[1]) for x,y in [(0,0),(1220,0),(1220,2710),(0,2710)]],close=True,dxfattribs={'layer':'SHEET'})
 for p in ps:m.add_lwpolyline([(u+p['x']-zero[0],v+p['y']-zero[1],b) for u,v,b in p['vertices']],format='xyb',close=True,dxfattribs={'layer':'PART_'+p['ident']})
 for h in holes:
  if h['sheet']==sid:m.add_circle((h['B_X'],h['B_Y']),4,dxfattribs={'layer':'PRE_DRILL_D8'})
 for t in tabs:
  if t['sheet']==sid:m.add_point((t['B_X'],t['B_Y']),dxfattribs={'layer':'TAB_CENTERS'})
 m.add_point((0,0),dxfattribs={'layer':'ORIGIN_B'});d.saveas(out/f'layout_sheet{sid}_B.dxf')
 chk=ezdxf.readfile(out/f'layout_sheet{sid}_B.dxf');assert not chk.audit().errors
(out/'verification.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
(out/'sources.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
steps=[
'Два листа ДВП 1220 × 2710 × 5 мм. Лист 1: по одному лекалу 002, 003, 004. Лист 2: четыре лекала 002 длиной 1600 мм. Каменные операции не входят в задание.',
'Выбран B: XY0 в габаритном углу первого PARAD-002. На листе 1 он расположен в (50;50) от листа, на листе 2 в (40;50). При смене листа заново проверить XY0; это две отдельные установки.',
'Лист 1 оставить прежним. На листе 2 четыре лекала шириной 270 мм, промежутки 20 мм, боковые поля по 40 мм. Экземпляры 2 и 4 сдвинуты от оператора на 100 мм. Смещение разносит соседние отверстия и зоны подхода фрезы.',
'До установки просверлить Ø8: 18 отверстий на листе 1 и 24 на листе 2. Для разметки от физических краёв использовать столбцы «От листа», для будущих УП — столбцы B. Не сверлить стол.',
'Поддержать свес листа 210 мм относительно указанного поля Y2500. Закрепить лист в свободных полях. Поле 40 мм и промежуток 20 мм не подтверждают, что конкретный прижим или держатель помещается: проверить их размеры и высоты отдельно.',
'Фреза Ø4; Z0 — стол, безопасный Z+45. В будущей AIR_XY все движения только на Z+45, без вращения шпинделя. Начальное положение, реальные ходы и настройки A11S проверить перед физической проверкой.',
'Предлагаемый порядок: лист 1 — 002 → 003 → 004; лист 2 — экземпляры 1 → 2 → 3 → 4. Каждый полностью на двух уровнях Z+2,5 и Z+0,3, затем следующий. По 6 участков между перемычками на каждом уровне, вход через подготовленные отверстия.',
'На каждом лекале 6 перемычек высотой 5 мм, шириной минимум 5 мм через паз; осевой пропуск 9 мм учитывает круглые концы фрезы. Недорез 0,3 мм. Внутренние R2 остаются: по два у 002/003 и один у 004.',
'Сохранённая расчётная основа для будущего резания: XY800, Z100 мм/мин, 16000 об/мин. Новая физическая проба не выполнялась. После проверки схемы отдельно подготовить общую AIR_XY для каждого листа с проверкой переходов. В этом обновлении NC не создавалась.'
]
md='# Общий раскрой ДВП — два листа, вариант B\n\n[Открыть обновлённый PDF](project_overview.pdf)\n\nВариант B выбран пользователем. Лист 1 оставлен без изменений. Лист 2: четыре PARAD-002; начала от листа (40;50), (330;150), (620;50), (910;150). B-ноль каждого листа — начало первого PARAD-002.\n\n'+ '\n\n'.join(f'{i}. {s}' for i,s in enumerate(steps,1))
md+='\n\nАктуальные схемы: layout_sheet1_B.dxf и layout_sheet2_B.dxf; координаты в sheet1/2_holes.csv и sheet1/2_tabs.csv. verification.json содержит проверки. Предыдущие варианты A/B сохранены в архиве и не являются текущей раскладкой двух листов.\n'
(out/'README.md').write_text(md,encoding='utf-8')
if not a.pdf:print(json.dumps(checks,ensure_ascii=False));sys.exit()
pdfmetrics.registerFont(TTFont('Arial',r'C:\Windows\Fonts\arial.ttf'));pdfmetrics.registerFont(TTFont('ArialB',r'C:\Windows\Fonts\arialbd.ttf'))
c=canvas.Canvas(str(out/'project_overview.pdf'),pagesize=(595.28,841.89));c.setTitle('Раскрой ДВП - два листа, вариант B');c.setAuthor('Parad')
style=ParagraphStyle('text',fontName='Arial',fontSize=10,leading=14,textColor=HexColor('#243b4b'))
small=ParagraphStyle('small',parent=style,fontSize=8,leading=10)
def para(t,x,y,w,st=style):
 p=Paragraph(t,st);_,h=p.wrap(w,750);p.drawOn(c,x,y-h);return y-h
def header(n,title,sub):
 c.setFillColor(HexColor('#24768a'));c.rect(0,828,596,14,fill=1,stroke=0)
 c.setFillColor(HexColor('#243b4b'));c.setFont('ArialB',19);c.drawString(35,788,title);para(sub,35,770,525,small)
 c.setFont('Arial',8);c.drawString(35,24,'Parad | ДВП | Выбран B | Две отдельные установки | Общих NC пока нет');c.drawRightString(560,24,str(n))
def table(rows,y,widths):
 t=Table([[Paragraph(str(v),small) for v in row] for row in rows],colWidths=widths)
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#e9f1f3')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,-1),.35,HexColor('#c6d6dc'))]));_,h=t.wrap(525,750);t.drawOn(c,35,y-h);return y-h
def layout(sid):
 sc=.17;ox=48;oy=205;c.setLineWidth(.7);c.setStrokeColor(HexColor('#69808b'));c.rect(ox,oy,1220*sc,2710*sc)
 colors=['#dcecf4','#e2efe8','#f4e9dc','#eadff0']
 for p,col in zip([p for p in parts if p['sheet']==sid],colors):
  path=c.beginPath();pts=list(p['shape'].exterior.coords);path.moveTo(ox+pts[0][0]*sc,oy+pts[0][1]*sc)
  for u,v in pts[1:]:path.lineTo(ox+u*sc,oy+v*sc)
  path.close();c.setFillColor(HexColor(col));c.setStrokeColor(HexColor('#27728a'));c.drawPath(path,fill=1,stroke=1)
  c.saveState();c.translate(ox+(p['x']+130)*sc,oy+(p['y']+180)*sc);c.rotate(90);c.setFont('ArialB',8);c.setFillColor(HexColor('#243b4b'));c.drawString(0,0,f'{p["ident"]} / {p["L"]}');c.restoreState()
 for h in holes:
  if h['sheet']==sid:c.setFillColor(HexColor('#c96828'));c.circle(ox+h['A_X']*sc,oy+h['A_Y']*sc,1.6,fill=1,stroke=0)
 for t in tabs:
  if t['sheet']==sid:c.setFillColor(HexColor('#247f57'));c.rect(ox+t['A_X']*sc-1.4,oy+t['A_Y']*sc-1.4,2.8,2.8,fill=1,stroke=0)
 zx,zy=ox+(50 if sid==1 else 40)*sc,oy+50*sc
 c.setStrokeColor(HexColor('#bb3545'));c.setLineWidth(1.3);c.line(zx-5,zy,zx+5,zy);c.line(zx,zy-5,zx,zy+5)
 c.setFont('ArialB',9);c.setFillColor(HexColor('#bb3545'));c.drawString(zx+10,zy-16,'XY0 B')
 c.setFillColor(HexColor('#243b4b'));c.setFont('Arial',9);c.drawString(110,680,'1220 мм');c.saveState();c.translate(34,360);c.rotate(90);c.drawString(0,0,'2710 мм / +Y от оператора');c.restoreState();c.drawString(85,170,'Оператор; +X вправо')
header(1,'Раскрой ДВП: два листа','Выбран B: ноль в углу первого PARAD-002. Листы 1220 × 2710 × 5 мм.')
y=para('<b>Лист 1 сохранён без изменений.</b> На листе 2 размещены четыре PARAD-002 со смещением второго и четвёртого экземпляров на 100 мм вдоль Y. Все лекала толщиной 5 мм.',35,728,525)
y=table([['Лист','Состав','Отверстия / перемычки'],[1,'002 × 1; 003 × 1; 004 × 1','18 / 18'],[2,'002 × 4, длина каждого 1600 мм','24 / 24']],y-20,[70,300,155])
y=para('<b>На обоих листах действует B, но ноль размечается отдельно:</b><br/>Лист 1: (50;50) от угла листа.<br/>Лист 2: (40;50) от угла листа.<br/>Это не перенос координат старой программы без перепривязки.',35,y-24,525)
y=table([['Проверка','Лист 1','Лист 2'],['Между габаритами','50 мм','20 мм'],['Минимум между зонами фрезы/отверстий',*[f'{checks["sheets"][i]["minimum_gap_between_cut_and_drill_zones_mm"]:.1f} мм' for i in (1,2)]],['Минимум от зоны фрезы/отверстий до края листа',*[f'{checks["sheets"][i]["minimum_sheet_margin_cut_and_drill_mm"]:.1f} мм' for i in (1,2)]]],y-24,[285,120,120])
para('Проверены контуры, диаметр фрезы Ø4, отверстия Ø8 и сохранность перемычек. Проверки прижимов, держателя и реальных ходов станка пока нет.<br/><br/>Боковые поля листа 2 по 40 мм. Ширина: 40 + 4 × 270 + 3 × 20 + 40 = 1220 мм. Общая высота габаритов при смещении - 1700 мм.<br/><br/><b>Документ для оценки раскладки. Общая NC не выпущена.</b> Каменные операции не изменялись.',35,y-24,525)
c.showPage()
for sid in (1,2):
 header(sid+1,f'Лист {sid}: '+('прежняя раскладка' if sid==1 else 'четыре PARAD-002'),'Зелёные маркеры - перемычки; оранжевые - отверстия. Маркеры увеличены.')
 layout(sid)
 zero=(50,50) if sid==1 else (40,50)
 ps=[p for p in parts if p['sheet']==sid]
 y=para('<b>Начала лекал в системе B:</b><br/>'+'<br/>'.join(f'{p["ident"]}: ({p["x"]-zero[0]}; {p["y"]-zero[1]})' for p in ps),288,655,270)
 y=para('<b>От физического угла листа:</b><br/>'+'<br/>'.join(f'{p["ident"]}: ({p["x"]}; {p["y"]})' for p in ps),288,y-24,270)
 y=para('Z0 - стол; безопасный Z+45. План будущих глубин +2,5 и +0,3. В AIR_XY только Z+45.<br/><br/>Порядок обработки - по номерам слева направо, оба уровня каждого лекала перед переходом к следующему.',288,y-24,270)
 if sid==2:para('Смещение по Y разносит отверстия соседних лекал. Между габаритами 20 мм; минимальный зазор между зонами реза/сверления '+f'{checks["sheets"][2]["minimum_gap_between_cut_and_drill_zones_mm"]:.1f} мм. Прижимы в эти узкие промежутки автоматически не назначены.',288,y-24,270)
 para('Ноль B находится на пересечении габаритных линий первого лекала. Для разметки отверстий от краёв листа применять столбцы «От листа» на следующих страницах; для будущей УП - B. Положения крепления требуется проверить отдельно.',35,119,525,small);c.showPage()
for page,sid,kind,allrows in [(4,1,'Отверстия Ø8',holes),(5,2,'Отверстия Ø8',holes),(6,1,'Перемычки',tabs),(7,2,'Перемычки',tabs)]:
 header(page,f'Лист {sid}: {kind}','H - отверстие; T - центр перемычки. 002-1…002-4 - экземпляры второго листа.')
 rows=[t for t in allrows if t['sheet']==sid]
 data=[['Номер','От листа X','От листа Y','B: X','B: Y']]+[[t['id'],*[f'{t[k]:.3f}' for k in ['A_X','A_Y','B_X','B_Y']]] for t in rows]
 y=table(data,732,[105]*5)
 para('Отверстия Ø8 сверлить до установки листа, только в отходе. На втором листе внимательно различать номер экземпляра.' if kind.startswith('Отверстия') else 'Перемычки: высота 5 мм; минимум ширины 5 мм через паз; осевой пропуск 9 мм для Ø4. По шесть на лекало. Общий недорез 0,3 мм сохраняется.',35,y-17,525,small)
 assert y>95,y;c.showPage()
header(8,'Действия по двум листам','Обработка ДВП. Ни выпуска режущей УП, ни физического запуска в этой работе нет.')
y=735
for i,t in enumerate(steps,1):y=para(f'<b>{i}.</b> '+t,35,y,525)-12
assert y>48,y;c.save();print(json.dumps(checks,ensure_ascii=False))
