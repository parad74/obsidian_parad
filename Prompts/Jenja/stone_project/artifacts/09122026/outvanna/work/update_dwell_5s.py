"""One-time documented change requested by Parad on 2026-11-06."""
from pathlib import Path
import json,hashlib,re
OUT=Path(__file__).resolve().parents[1]
ROOT=OUT.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
protected=[OUT/'vanna_contours_mm.dxf',OUT/'vanna_dimensioned_mm.dxf',OUT/'cnc/nc/VANNA_DVP_AIR_XY.nc',OUT/'cnc/geometry/vanna_sheet_toolpaths_mm.dxf',OUT/'cnc/geometry/vanna_motion_XYZ.dxf',OUT/'cnc/data/parsed_motion.json',OUT/'cnc/data/paths.json',OUT/'cnc/data/holes_tabs.csv']
before={str(p.relative_to(OUT)):sha(p) for p in protected}
cutpath=OUT/'cnc/nc/VANNA_DVP_D4_CUT.nc'
old=cutpath.read_bytes();assert old.count(b'G04 P21000')==1
new=old.replace(b'G04 P21000',b'G04 P5000')
cutpath.write_bytes(new)
assert new.replace(b'G04 P5000',b'G04 P21000')==old
lines=new.decode('ascii').splitlines();i=lines.index('M3 S16000');assert lines[i+1]=='G04 P5000'
def replace(path,a,b):
    s=path.read_text(encoding='utf-8');assert a in s,(path,a)
    path.write_text(s.replace(a,b),encoding='utf-8')
params=OUT/'cnc/data/parameters.json';p=json.loads(params.read_text(encoding='utf-8'));assert p['dwell_seconds']==21;p['dwell_seconds']=5
params.write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
scripts=OUT/'cnc/scripts'
replace(scripts/'reconstruct_profile.py','dwell_seconds=21','dwell_seconds=5')
replace(scripts/'build_vanna.py',"'G04 P21000'","f'G04 P{int(P[\"dwell_seconds\"]*1000)}'")
replace(scripts/'build_vanna.py',"w['P']==21000","w['P']==P['dwell_seconds']*1000")
replace(scripts/'build_vanna.py','feed_plus_explicit_dwell_minutes=minutes+.35','dwell_seconds=P[\'dwell_seconds\'],feed_plus_explicit_dwell_minutes=minutes+P[\'dwell_seconds\']/60')
vpath=OUT/'cnc/data/verification.json';v=json.loads(vpath.read_text(encoding='utf-8'))
old_time=v['feed_plus_explicit_dwell_minutes'];v['dwell_seconds']=5;v['feed_plus_explicit_dwell_minutes']=v['feed_minutes']+5/60
vpath.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
new_time=v['feed_plus_explicit_dwell_minutes'];assert abs(old_time-new_time-16/60)<1e-10
testdir=OUT/'cnc/test_checks';testdir.mkdir(exist_ok=True)
for filename in ['CHECK_DWELL_21S_NO_MOTION.nc','CHECK_SPINDLE_16000_21S_NO_MOTION.nc']:
    original=(ROOT/'postprocessor/dvp_002_003_004/test_checks'/filename).read_bytes()
    updated=original.replace(b'G04 P21000',b'G04 P5000').replace(b'21 SECOND',b'5 SECOND')
    target=testdir/filename.replace('_21S_','_5S_');target.write_bytes(updated)
    assert updated.count(b'G04 P5000')==1 and b'P21000' not in updated
doc=scripts/'document_vanna.py'
replace(doc,'G04 P21000 - выбранные 21 с','G04 P5000 - 5 с по указанию оператора')
s=doc.read_text(encoding='utf-8')
s='\n'.join("para('Тесты текущего проекта: cnc/test_checks. Проверка длительности - CHECK_DWELL_5S_NO_MOTION.nc; тест вращения без движения осей - CHECK_SPINDLE_16000_5S_NO_MOTION.nc. Последний включает шпиндель. Пауза 5 с задана по просьбе оператора через Parad 06.11.2026; дополнительная задержка пульта может увеличить паузу.',44,y-16,st=small)" if line.startswith("para('Сохранённые тесты:") else line for line in s.split('\n'))
doc.write_text(s,encoding='utf-8')
readme=OUT/'README.md'
replace(readme,'G04 P21000 (21 с)','G04 P5000 (5 с, изменение по просьбе оператора через Parad 06.11.2026)')
replace(readme,'../../../../postprocessor/dvp_002_003_004/test_checks/CHECK_DWELL_21S_NO_MOTION.nc','cnc/test_checks/CHECK_DWELL_5S_NO_MOTION.nc')
replace(readme,'../../../../postprocessor/dvp_002_003_004/test_checks/CHECK_SPINDLE_16000_21S_NO_MOTION.nc','cnc/test_checks/CHECK_SPINDLE_16000_5S_NO_MOTION.nc')
replace(readme,'Выполнить ранее сохранённые','Выполнить обновлённые для outvanna')
replace(readme,'Выдержка 21 с выбрана, не измерена на этой прошивке','Выдержка 5 с задана по просьбе оператора, измерение на этой прошивке не сообщено')
replace(readme,'**23,11 мин**','**22,85 мин**')
with readme.open('a',encoding='utf-8') as f:f.write('\n06.11.2026 — По просьбе оператора, переданной Parad, пауза outvanna после M3 изменена с 21 на 5 с (G04 P5000). Прежнее значение 21 с относится к исходному выпуску. Пересчитано время: 22,85 мин, на 16 с меньше; траектории, подачи, обороты, DXF и AIR_XY сохранены. Тесты 5 с находятся в cnc/test_checks; прежние тесты других проектов не изменены.\n')
hashfile=OUT/'cnc/data/output_sha256.json';h=json.loads(hashfile.read_text());h[str(cutpath.relative_to(OUT))]=sha(cutpath)
for q in testdir.glob('*.nc'):h[str(q.relative_to(OUT))]=sha(q)
hashfile.write_text(json.dumps(h,indent=2),encoding='utf-8')
assert before=={str(q.relative_to(OUT)):sha(q) for q in protected}
report=dict(date='2026-11-06',reason='Operator request relayed and authorized by Parad',old_seconds=21,new_seconds=5,
    cut_only_changed_line='G04 P21000 -> G04 P5000',cut_before_sha256=hashlib.sha256(old).hexdigest(),cut_after_sha256=sha(cutpath),
    unchanged_sha256=before,old_feed_plus_dwell_minutes=old_time,new_feed_plus_dwell_minutes=new_time,time_reduction_seconds=16,physical_test=False)
(OUT/'cnc/data/dwell_update_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
for q in scripts.glob('*.py'):compile(q.read_text(encoding='utf-8'),str(q),'exec')
print(json.dumps(report,ensure_ascii=False,indent=2))
