from pathlib import Path
import json,argparse
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph,Table,TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();out=args.output
pdfmetrics.registerFont(TTFont('Arial',r'C:\Windows\Fonts\arial.ttf'));pdfmetrics.registerFont(TTFont('ArialB',r'C:\Windows\Fonts\arialbd.ttf'))
body=ParagraphStyle('body',fontName='Arial',fontSize=10,leading=14,textColor=HexColor('#243b4b'))
small=ParagraphStyle('small',parent=body,fontSize=8.5,leading=11)
for sid in (1,2):
 d=out/f'sheet_{sid}';v=json.loads((d/'data/verification.json').read_text(encoding='utf-8'))
 c=canvas.Canvas(str(d/'project_overview.pdf'),pagesize=(595.28,841.89));c.setTitle(f'Лист {sid}: режущая УП ДВП');c.setAuthor('Parad')
 def para(t,y,style=body):
  p=Paragraph(t,style);_,h=p.wrap(525,750);p.drawOn(c,35,y-h);return y-h
 def heading(page,title):
  c.setFillColor(HexColor('#24768a'));c.rect(0,828,596,14,fill=1,stroke=0);c.setFillColor(HexColor('#243b4b'));c.setFont('ArialB',19);c.drawString(35,788,title)
  c.setFont('Arial',8);c.drawString(35,24,f'Parad | Лист {sid} | ДВП | Проверено расчётом; физический запуск не выполнен');c.drawRightString(560,24,str(page))
 def table(rows,y,widths):
  t=Table([[Paragraph(str(x),small) for x in row] for row in rows],colWidths=widths);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#e9f1f3')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,0),(-1,-1),.35,HexColor('#c6d6dc'))]));_,h=t.wrap(525,750);t.drawOn(c,35,y-h);return y-h
 heading(1,f'Лист {sid}: режущая УП ДВП')
 y=para(f'<b>SHEET_{sid}_DVP_D4_CUT.nc включает шпиндель и опускает фрезу в материал.</b> Применять после проверки установки, паузы, разгона и AIR_XY. Не путать с файлом проверки без резания.',747)
 y=table([['Параметр','Значение'],['Лист / инструмент','ДВП 1220 × 2710 × 5 мм; фреза Ø4, один зуб'],['Ноль XY B',f'Угол первого PARAD-002; от угла листа ({v["origin_B_from_sheet_mm"][0]}; {v["origin_B_from_sheet_mm"][1]}) мм'],['Оси / Z0','X вправо; Y от оператора; Z0 по столу'],['Уровни Z','Безопасный +45; подвод +7; рабочие +2,5 и +0,3'],['Режим','S16000; XY F800; вертикальное опускание F100'],['Пауза','G04 P21000 после M3: 21 секунда'],['Отверстия / перемычки',f'{v["holes"]} × Ø8 заранее; {v["tabs"]} перемычек высотой 5 мм'],['Недорез / перемычка','Недорез 0,3 мм; минимум ширины перемычки 5 мм, осевой пропуск 9 мм']],y-18,[165,360])
 y=para('<b>Порядок лекал и их начала в системе B:</b>',y-20)
 y=table([['Лекало','X','Y']]+[[p['id'],p['origin_B'][0],p['origin_B'][1]] for p in v['parts']],y-10,[265,130,130])
 y=para('Оба уровня каждого лекала выполняются перед переходом к следующему. Между участками Z+45. Шпиндель работает непрерывно до конца листа. Завершение: Z+45, M5, рабочий XY0, M30.',y-18)
 y=para(f'На подаче с явной выдержкой: <b>{v["feed_plus_explicit_dwell_minutes"]:.2f} мин</b>. Это не полное время: не учтены G0, ускорения, задержка пульта и установка.',y-12,small)
 assert y>45,y;c.showPage()
 heading(2,'Проверка и запуск')
 steps=[
 'Сверить номер листа и файл. Проверить фрезу Ø4, разметку B и Z0 по столу. При замене листа привязку проверить заново. Не использовать машинный ноль вместо B.',
 f'До установки просверлить {v["holes"]} отверстий Ø8 в отходе по holes_coordinates.csv. Обеспечить прилегание листа к столу, прижимы вне зон реза и отверстий. Поддержать свес листа 210 мм относительно указанного поля Y2500.',
 'Проверить ходы и свободный объём инструмента с держателем, в том числе при отрицательных координатах B. Начать с инструмента на безопасной высоте. Прижимы и их высоты расчётом не проверены.',
 'В общей папке test_checks выполнить CHECK_DWELL_21S_NO_MOTION.nc: без движения осей и запуска шпинделя. Проверить 21 секунду. Затем при свободном инструменте CHECK_SPINDLE_16000_21S_NO_MOTION.nc: шпиндель включается на S16000, оси не движутся, после выдержки M5. Проверить набор оборотов и останов. Задержка пульта может увеличить общее время.',
 f'Выполнить SHEET_{sid}_DVP_AIR_XY.nc: без вращения, весь XY-путь на Z+45. Это не проверка рабочих спусков. При неверной паузе, координатах или наличии препятствий режущий запуск не выполнять.',
 f'После проверок запустить SHEET_{sid}_DVP_D4_CUT.nc с начала. Не возобновлять произвольно с середины. Фреза входит через подготовленные отверстия: G0 до +7, затем F100 до рабочего Z; XY F800. Сохранённые недорез и перемычки должны удерживать лекала.',
 'После полного останова снять лист и отделить перемычки/недорез вручную. Проверить лекала; внутренние R2 остаются в принятой форме.'
 ]
 y=743
 for i,t in enumerate(steps,1):y=para(f'<b>{i}.</b> '+t,y)-13
 y=para(f'<b>Проверено:</b> фактически записанные координаты NC и дуги, {v["plunges"]} входов в отверстия, глубины и подачи, M3/G4/M5, переходы на безопасном Z, отсутствие зареза лекал и перемычек в модели, повторное чтение DXF. Допуск вычисления зоны реза 0,002 мм; это не точность станка.<br/><br/>Схема обоих листов: ../project_overview.pdf. Полные условия: README.md. Источники и отчёт: data/. Код создан скриптом, не экспортом ArtCAM. G4 P в миллисекундах по руководству RichAuto A1X, приложение 3, стр. 59; конкретная прошивка требует указанной проверки.',y,small)
 assert y>45,y;c.save()
print('Created two 2-page PDF setup guides')
