"""Two DVP sheets: cutting NC, air check and static read-back. Never operates a machine."""
from pathlib import Path
import argparse,json,csv,math,re,hashlib,shutil
import ezdxf
from ezdxf.path import make_path
from shapely.geometry import Polygon,Point,LineString,box
from shapely.ops import unary_union

ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
out=args.output;out.mkdir(parents=True,exist_ok=True)
root=Path(r'W:\obsidian\_parad\Prompts\Jenja');common=root/'postprocessor/dvp_002_003_004'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest={}
def read(p):manifest[str(p)]=sha(p);return json.loads(p.read_text(encoding='utf-8'))
def fmt(x):return f'{0 if abs(x)<.0000001 else x:.3f}'
def ncwrite(p,rows):p.write_bytes(('\r\n'.join(rows)+'\r\n').encode('ascii'))
placements={1:[(2,'002',0,0),(3,'003',320,0),(4,'004',640,0)],2:[(2,f'002-{i+1}',290*i,100*(i%2)) for i in range(4)]}
summary={}
for sid,specs in placements.items():
 d=out/f'sheet_{sid}';d.mkdir(exist_ok=True);(d/'data').mkdir(exist_ok=True)
 zero=(50,50) if sid==1 else (40,50)
 sheet=box(-zero[0],-zero[1],1220-zero[0],2710-zero[1])
 holes=[];tabpolys=[];shapes=[];nominal=[];expected=[];partinfo=[]
 for n,ident,dx,dy in specs:
  src=root/f'stone_project/artifacts/09122026/out{n-1}/cnc'
  L={2:1600,3:2100,4:1280}[n]
  cp=src/f'geometry/dvp_contour_R2_Y{L}.dxf';manifest[str(cp)]=sha(cp)
  e=list(ezdxf.readfile(cp).modelspace().query('LWPOLYLINE'))[0]
  shape=Polygon([(p.x+dx,p.y+dy) for p in make_path(e).flattening(.0001)]);shapes.append(shape)
  hp=src/'data/dvp_holes.csv';manifest[str(hp)]=sha(hp)
  with hp.open(encoding='utf-8-sig') as f:
   for h in csv.DictReader(f):holes.append((float(h['x'])+dx,float(h['y'])+dy))
  for t in read(src/'data/tabs.json'):
   u,v=t['center'][0]+dx,t['center'][1]+dy;ax=t['axis'];no=t['normal']
   tabpolys.append(Polygon([(u+k*ax[0]+z*no[0],v+k*ax[1]+z*no[1]) for k,z in [(-2.5,0),(2.5,0),(2.5,4),(-2.5,4)]]))
  motions=read(src/'data/planned_3d_motion.json')['01_dvp']
  for m in motions:
   if m['role']=='return_work_XY0':continue
   expected.append({**m,'end':[m['end'][0]+dx,m['end'][1]+dy,m['end'][2]],'part':ident})
  partinfo.append({'id':ident,'length_mm':L,'origin_B':[dx,dy],'origin_sheet':[dx+zero[0],dy+zero[1]]})
 rows=['%',f'(SHEET {sid} DVP 5MM - CUTTING PROGRAM - NOT AIR)',
  '(B ORIGIN FIRST PARAD002; Z0 TABLE; TOOL D4)',
  '(VERIFY CLAMPS FLATNESS PRE-DRILLED D8 HOLES AND TRAVEL)',
  '(START ABOVE STOCK; SPINDLE CHECK AND AIR CHECK REQUIRED)',
  'G90','G21','G17','G40','G49','G80','M5','G0 Z45.000','M3 S16000','G04 P21000']
 air=['%',f'(SHEET {sid} AIR XY ONLY - NO SPINDLE - Z45)', 'G90','G21','G17','G40','G49','G80','M5','G0 Z45.000']
 previous_part=None
 for m in expected:
  if m['part']!=previous_part:
   rows.append('(PART '+m['part']+')');air.append('(PART '+m['part']+')');previous_part=m['part']
  xyz=' '.join(k+fmt(v) for k,v in zip('XYZ',m['end']))
  row=m['code']+' '+xyz
  if m['ij'] is not None:row+=' I'+fmt(m['ij'][0])+' J'+fmt(m['ij'][1])
  if m['feed'] is not None:row+=' F'+fmt(m['feed'])
  rows.append(row)
  if m['role'] in ('air_return','feed_path'):
   arow=m['code']+' X'+fmt(m['end'][0])+' Y'+fmt(m['end'][1])
   if m['ij'] is not None:arow+=' I'+fmt(m['ij'][0])+' J'+fmt(m['ij'][1])
   if m['feed'] is not None:arow+=' F'+fmt(m['feed'])
   air.append(arow)
 rows+=['G0 Z45.000','M5','G0 X0.000 Y0.000','M30','%']
 air+=['M5','G0 X0.000 Y0.000','M30','%']
 cutfile=d/f'SHEET_{sid}_DVP_D4_CUT.nc';airfile=d/f'SHEET_{sid}_DVP_AIR_XY.nc'
 ncwrite(cutfile,rows);ncwrite(airfile,air)
 # Independent interpretation of emitted rounded coordinates, not just source plans.
 coord=[0.,0.,45.];spindle=False;rpm=None;dwell=False;mode=set();moves=[];sweeps=[];plunges=0;feed_minutes=0.;rapid_mm=0.;arc_error=0.;dwell_count=0
 for raw in cutfile.read_text('ascii').splitlines():
  row=re.sub(r'\([^)]*\)','',raw).strip()
  if row in ('','%'):continue
  words=re.findall(r'([A-Z])([-+]?\d+(?:\.\d*)?)',row)
  assert ''.join(k+v for k,v in words)==re.sub(r'\s','',row),row
  w={k:float(v) for k,v in words};g=int(w['G']) if 'G' in w else None
  assert set(w)<=set('GMSXYZIJFP')
  if g in (90,21,17,40,49,80):mode.add(g);continue
  if 'M' in w:
   assert w['M'] in (3,5,30)
   if w['M']==3:spindle=True;rpm=w['S'];dwell=False;assert rpm==16000
   if w['M']==5:spindle=False
   if w['M']==30:assert not spindle and coord==[0.,0.,45.]
   continue
  if g==4:
   assert set(w)=={'G','P'} and w['P']==21000 and spindle
   dwell=True;dwell_count+=1;continue
  assert g in (0,1,2,3) and mode=={90,21,17,40,49,80}
  end=[w.get(k,coord[i]) for i,k in enumerate('XYZ')];xy=math.dist(coord[:2],end[:2]);dz=end[2]-coord[2]
  if g==0:
   if xy>1e-8:assert coord[2]==end[2]==45
   if dz<0:assert xy<1e-8 and end[2]==7
   rapid_mm+=math.dist(coord,end)
  else:
   assert spindle and rpm==16000 and dwell
   if abs(dz)>1e-8:
    assert g==1 and xy<1e-8 and coord[2]==7 and end[2] in (2.5,.3) and w['F']==100
    assert min(math.dist(end[:2],h) for h in holes)<.001
    plunges+=1;feed_minutes+=abs(dz)/100
   else:
    assert end[2] in (2.5,.3) and w['F']==800
    if g==1:points=[coord[:2],end[:2]];dist=xy
    else:
     center=(coord[0]+w['I'],coord[1]+w['J']);r0=math.dist(coord[:2],center);r1=math.dist(end[:2],center)
     arc_error=max(arc_error,abs(r0-r1));assert abs(r0-r1)<.002
     aa=math.atan2(coord[1]-center[1],coord[0]-center[0]);bb=math.atan2(end[1]-center[1],end[0]-center[0]);sign=1 if g==3 else -1
     sweep=((bb-aa)*sign)%(2*math.pi);assert 0<sweep<=math.pi/2+.001
     points=[(center[0]+r0*math.cos(aa+sign*sweep*i/256),center[1]+r0*math.sin(aa+sign*sweep*i/256)) for i in range(257)];dist=r0*sweep
    sweeps.append(LineString(points).buffer(2,quad_segs=128));feed_minutes+=dist/800
  moves.append({'code':g,'start':coord[:],'end':end[:],'feed':w.get('F'),'ij':[w.get('I'),w.get('J')] if g in (2,3) else None});coord=end
 assert plunges==12*len(specs) and dwell_count==1
 # The parsed working moves must agree with the assembled source segments to rounding precision.
 actual=moves[1:1+len(expected)]
 assert len(actual)==len(expected)
 for got,want in zip(actual,expected):
  assert got['code']==int(want['code'][1:]) and max(abs(a-b) for a,b in zip(got['end'],want['end']))<=.000501
  assert got['feed']==want['feed']
  if got['ij']:assert max(abs(a-b) for a,b in zip(got['ij'],want['ij']))<=.000501
 cut=unary_union(sweeps);kept=unary_union(shapes);tabsbody=unary_union(tabpolys)
 gouge=cut.intersection(kept.buffer(-.002)).area;bridge=cut.intersection(tabsbody.buffer(-.002)).area
 assert gouge<.01 and bridge<.01 and sheet.contains(cut),(gouge,bridge)
 # Verify AIR file contains identical XY moves and no cutting heights or spindle speed.
 airtext=airfile.read_text('ascii');a_plain=re.sub(r'\([^)]*\)','',airtext)
 assert not re.search(r'\bM0?[34]\b|\bS\d',a_plain)
 assert all(float(z)==45 for z in re.findall(r'\bZ([-+\d.]+)',a_plain))
 expected_air=[(int(m['code'][1:]),*[round(v,3) for v in m['end'][:2]]) for m in expected if m['role'] in ('air_return','feed_path')]+[(0,0.,0.)]
 parsed_air=[]
 for line in a_plain.splitlines():
  words=dict((k,float(v)) for k,v in re.findall(r'([A-Z])([-+]?\d+(?:\.\d*)?)',line))
  if 'X' in words:parsed_air.append((int(words['G']),words['X'],words['Y']))
 assert parsed_air==expected_air
 # DXF showing complete motion, including vertical entry and inter-part transfers.
 doc=ezdxf.new('R2000');doc.units=4;ms=doc.modelspace()
 for m in moves:
  layer='RAPID' if m['code']==0 else 'FEED'
  if m['code'] in (0,1):ms.add_line(m['start'],m['end'],dxfattribs={'layer':layer})
  else:
   c=[m['start'][i]+m['ij'][i] for i in range(2)];rr=math.dist(c,m['start'][:2]);aa=math.degrees(math.atan2(m['start'][1]-c[1],m['start'][0]-c[0]))%360;bb=math.degrees(math.atan2(m['end'][1]-c[1],m['end'][0]-c[0]))%360
   ms.add_arc((*c,m['start'][2]),rr,aa if m['code']==3 else bb,bb if m['code']==3 else aa,dxfattribs={'layer':layer})
 doc.saveas(d/f'SHEET_{sid}_DVP_XYZ.dxf');audit=ezdxf.readfile(d/f'SHEET_{sid}_DVP_XYZ.dxf').audit();assert not audit.errors and not audit.fixes
 for kind in ('holes','tabs'):shutil.copy2(common/f'sheet{sid}_{kind}.csv',d/f'{kind}_coordinates.csv')
 check={'status':'pass_static_checks','sheet':sid,'origin_B_from_sheet_mm':zero,'parts':partinfo,'holes':len(holes),'tabs':len(tabpolys),'depths_Z_mm':[2.5,.3],'safe_Z':45,'spindle_RPM':16000,'G04_P':21000,'plunges':plunges,'arc_radius_error_mm':arc_error,'gouge_beyond_002mm_tolerance_mm2':gouge,'tab_intersection_beyond_002mm_tolerance_mm2':bridge,'feed_motion_minutes':feed_minutes,'feed_plus_explicit_dwell_minutes':feed_minutes+.35,'rapid_distance_mm':rapid_mm,'full_cycle_minutes':None,'physical_test':False,'actual_ArtCAM_export':False,'limits':'No measured fixtures/holder/travel; setup and dry checks by operator required; dwell not tested on this firmware.'}
 (d/'data/verification.json').write_text(json.dumps(check,ensure_ascii=False,indent=2),encoding='utf-8')
 (d/'data/parsed_motion.json').write_text(json.dumps(moves,indent=2),encoding='utf-8')
 (d/'data/input_hashes.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
 md=f'''# Лист {sid}: режущая УП ДВП

**SHEET_{sid}_DVP_D4_CUT.nc — РЕЖУЩАЯ программа: шпиндель включается, инструмент опускается в материал.** Статические проверки пройдены; станок этой программой не запускался. Это расчётный NC, не фактический экспорт ArtCAM.

[Открыть PDF листа](project_overview.pdf) · [Принятая раскладка двух листов](../project_overview.pdf)

## Файлы

- [Режущая УП](SHEET_{sid}_DVP_D4_CUT.nc).
- [Проверка XY без шпинделя](SHEET_{sid}_DVP_AIR_XY.nc): весь путь на Z+45.
- SHEET_{sid}_DVP_XYZ.dxf — полные движения; повторную компенсацию инструмента не добавлять.
- holes_coordinates.csv, tabs_coordinates.csv — отверстия и центры перемычек в B и от листа.
- data/verification.json, parsed_motion.json, input_hashes.json — проверки, движения и источники.

## Установка

ДВП 1220 × 2710 × 5 мм. **XY0 B — угол первого PARAD-002, от физического угла листа ({zero[0]}; {zero[1]}) мм.** X вправо, Y от оператора. Z0 — поверхность стола под листом; инструмент Ø4, один зуб. При смене листа проверить привязку заново. Лист плоско прижат, поддержка свеса 210 мм; прижимы вне зон реза/сверления, держатель свободно проходит на Z+45. Эти условия оператор подтвердил как проверку при установке, их геометрия не измерена.

Заранее просверлить {len(holes)} отверстий Ø8 в отходе ДО установки листа на станок. Проверить соответствие центров таблице. По шесть перемычек на лекало: высота 5 мм, минимум ширины 5 мм через паз; осевой пропуск 9 мм учитывает круглые концы Ø4. Недорез 0,3 мм сохраняется. R2 остаются без доводки.

## Перед первым резанием

1. Проверить чтение G04 P21000: в test_checks/CHECK_DWELL_21S_NO_MOTION.nc нет движения и запуска шпинделя. Должна получиться выдержка 21 с, а не 21 мс. Папка test_checks находится уровнем выше.
2. При свободном инструменте на безопасной высоте выполнить отдельную проверку test_checks/CHECK_SPINDLE_16000_21S_NO_MOTION.nc: она включает шпиндель, не перемещает оси, ждёт 21 с после M3 и останавливает его. Проверить направление, набор оборотов и останов. Встроенная задержка пульта может увеличить общее время.
3. Проверить нули, исходное безопасное положение и весь свободный объём, затем выполнить AIR_XY без вращения и резания. Оно проверяет XY, но не рабочие спуски.
4. Только после этих проверок применять CUT с правильным инструментом и установкой. При расхождении не продолжать резание, уточнить привязку/команды. Программы запускаются с начала; восстановление с середины не подготовлено.

## Логика CUT

G90/G21/G17, отмена радиусной/длиновой компенсации и циклов G40/G49/G80; M5, безопасный Z+45, M3 S16000, отдельная G04 P21000. Затем по порядку лекал, оба уровня каждого перед следующим. Из безопасного Z переход к отверстию, G0 до Z+7, G1 F100 до Z+2,5 или Z+0,3; XY F800. Между участками подъём Z+45; междетальные переходы только на Z+45. Шпиндель работает непрерывно в пределах листа. Конец: Z+45, M5, возврат в рабочий XY0, M30. Никаких G28 и автоматической смены инструмента.

Время на подаче {feed_minutes:.2f} мин; с явной паузой 21 с — {feed_minutes+.35:.2f} мин. Это не полное время: G0, ускорения, собственная задержка пульта и установка неизвестны.

## Проверки и границы

Повторно разобран записанный NC с округлением 0,001 мм: проверены порядок M3/G4, обороты/подачи, {plunges} спусков в существующие отверстия, уровни Z, дуги, переходы на Z+45, конечная точка. Проверена зона Ø4 по фактическим координатам NC: отсутствие зареза принятого лекала и перемычек с вычислительным допуском 0,002 мм, попадание в лист. DXF перечитан. Это не проверка реального станка, прижимов или прогиба ДВП.

Источник G4: руководство производителя RichAuto–AutoNow A1X для A11/A12/A15/A18, приложение 3, стр. 59, [копия](https://www.scribd.com/document/578134836/): P — миллисекунды. Реализация конкретной прошивки проверяется перед резанием. Настройки и история: [база общего раскроя](../README.md).
'''
 (d/'README.md').write_text(md,encoding='utf-8');summary[sid]=check
tests=out/'test_checks';tests.mkdir(exist_ok=True)
ncwrite(tests/'CHECK_DWELL_21S_NO_MOTION.nc',['%','(CHECK 21 SECOND DWELL - NO AXIS MOTION - NO SPINDLE START)','M5','G04 P21000','M30','%'])
ncwrite(tests/'CHECK_SPINDLE_16000_21S_NO_MOTION.nc',['%','(SPINDLE TEST - AXES DO NOT MOVE - TOOL MUST ALREADY BE CLEAR)','M5','M3 S16000','G04 P21000','M5','M30','%'])
(out/'cutting_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({sid:{k:v[k] for k in ['status','plunges','feed_plus_explicit_dwell_minutes']} for sid,v in summary.items()},ensure_ascii=False))
