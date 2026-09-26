"""Render CATALOG_PARAD.md in its existing order; append new <!-- entry --> blocks to the Markdown."""
from pathlib import Path
from urllib.parse import unquote
import re, html, sys, hashlib
from PIL import Image as PILImage
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader

# Catalog branding: Parad only. Do not copy personal profile data into content or metadata.
ROOT = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parent
OUT = Path(sys.argv[2]).resolve() if len(sys.argv)>2 else ROOT
MD = OUT/'CATALOG_PARAD_002_003_004.md'
body = MD.read_text(encoding='utf-8-sig')
parts = body.split('<!-- entry -->')
entries = [p.strip() for p in parts[1:]]
assert entries, 'No catalog entries found'
paths = [ROOT/unquote(p) for p in re.findall(r'\]\(([^)]+)\)',body)]
for path in paths:
    assert path.exists(),path
before = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths+[MD] if p.is_file()}

pdfmetrics.registerFont(TTFont('AR','C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('AB','C:/Windows/Fonts/arialbd.ttf'))
pdfmetrics.registerFontFamily('AR',normal='AR',bold='AB',italic='AR',boldItalic='AB')
normal = ParagraphStyle('Normal',fontName='AR',fontSize=9.1,leading=12.0,spaceAfter=7,textColor=colors.HexColor('#243748'))
small = ParagraphStyle('Small',parent=normal,fontSize=8,leading=10.5,spaceAfter=5)
title = ParagraphStyle('Title',parent=normal,fontName='AB',fontSize=23,leading=28,spaceAfter=12)
head = ParagraphStyle('Head',parent=normal,fontName='AB',fontSize=17,leading=21,spaceAfter=11,keepWithNext=True,textColor=colors.HexColor('#12647b'))

def inline(s):
    chunks = re.split(r'(\[[^\]]+\]\([^)]+\))',s)
    result=''
    for chunk in chunks:
        m=re.fullmatch(r'\[([^\]]+)\]\(([^)]+)\)',chunk)
        if m:
            href=(ROOT/unquote(m[2])).resolve().as_uri()
            result += '<link href="'+html.escape(href,quote=True)+'" color="#12647b"><u>'+html.escape(m[1])+'</u></link>'
        else:
            result += re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',html.escape(chunk))
    return result

def picture(path,maxw,maxh):
    with PILImage.open(path) as im: w,h=im.size
    scale=min(maxw/w,maxh/h)
    return Image(str(path),width=w*scale,height=h*scale)

class CatalogDoc(SimpleDocTemplate):
    def afterFlowable(self,flowable):
        if hasattr(flowable,'catalog_key'):
            self.canv.bookmarkPage(flowable.catalog_key)
            self.canv.addOutlineEntry(flowable.getPlainText(),flowable.catalog_key,level=0)

story=[Paragraph('Каталог подоконников Parad',title),Paragraph('Только PARAD-002, PARAD-003, PARAD-004',normal),Paragraph('Выборка от 26 сентября 2026 · основной каталог сохранён',small),Spacer(1,8)]
story.append(Paragraph('От старых работ к новым',ParagraphStyle('TOCHead',parent=head,keepWithNext=False)))
rows=[]
for entry in entries:
    label=entry.splitlines()[0][3:]
    key=re.match(r'PARAD-\d+',label).group()
    date=entry.split('\n\n')[1]
    image_match=re.search(r'!\[[^\]]*\]\(([^)]+)\)',entry)
    image_path=ROOT/unquote(image_match.group(1)) if image_match else None
    desc=Paragraph('<link href="#'+key+'" color="#12647b"><b>'+html.escape(label)+'</b></link><br/>'+inline(date),small)
    rows.append([picture(image_path,100,48) if image_path else Paragraph('Дополнение',small),desc])
table=Table(rows,colWidths=[116,395],hAlign='LEFT')
table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ROWBACKGROUNDS',(0,0),(-1,-1),[colors.HexColor('#f0f5f7'),colors.white]),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
story.extend([table,Spacer(1,16),Paragraph('Что включено',head)])
for text in [
    'Три проекта: PARAD-002 — 1600 × 270 × 30 мм; PARAD-003 — 2100 × 270 × 30 мм; PARAD-004 — актуально 1280 × 270 × 30 мм с прямым левым торцом.',
    'Для каждого сохранены первоначальное описание, относящиеся к нему дополнения STEP и комплект проверки УП без резания. Описание 1300 мм у PARAD-004 относится только к архиву; далее приведён пересчёт на 1280 мм.',
    'Ссылки и видимые пути от \u005c\u005cJenja\u005c\u005c ведут к папкам результатов, документов, скриптов и проверок. Общий раскрой двух листов остаётся в полном каталоге, записи PARAD-014 и PARAD-015.',
    'Статусы проверки сохранены: расчёт и наличие файлов не означают испытание на станке. Исходный CATALOG_PARAD.md/PDF и инженерные файлы не изменены.'
]: story.append(Paragraph(text,small))

for entry in entries:
    story.append(PageBreak())
    for block in entry.split('\n\n'):
        if block.startswith('## '):
            heading=Paragraph(inline(block[3:]),head)
            heading.catalog_key=re.match(r'PARAD-\d+',block[3:]).group()
            story.append(heading)
        elif block.startswith('| '):
            rows=[]
            for line in block.splitlines():
                if re.match(r'^\|[ :|\-]+\|$',line): continue
                rows.append([Paragraph(inline(v.strip()),small) for v in line.strip().strip('|').split('|')])
            t=Table(rows,colWidths=[265,246],repeatRows=1,hAlign='LEFT')
            t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5eff2')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f4f7f8')]),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#ccd9de'))]))
            story.extend([t,Spacer(1,10)])
        elif block.startswith('**PARAD-') or block.startswith('**Таблица всех файлов'):
            story.extend([PageBreak(),Paragraph(inline(block),head)])
        elif block.startswith('!['):
            image_path=ROOT/unquote(re.search(r'\]\(([^)]+)\)',block).group(1))
            story.extend([picture(image_path,480,190),Spacer(1,8)])
        else: story.append(Paragraph(inline(block.replace('\n',' ')),normal))

def frame(c,d):
    c.setFont('AR',8);c.setFillColor(colors.HexColor('#657988'))
    c.drawString(42,24,'PARAD / История работ / Продолжение в конце каталога')
    c.drawRightString(A4[0]-42,24,str(d.page))

target=OUT/'CATALOG_PARAD_002_003_004.PDF'
CatalogDoc(str(target),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=36,bottomMargin=44,title='Каталог подоконников Parad — 002, 003, 004',author='Parad').build(story,onFirstPage=frame,onLaterPages=frame)
reader=PdfReader(target)
text='\n'.join(p.extract_text() or '' for p in reader.pages)
ids=[re.match(r'## (PARAD-\d+)',entry).group(1) for entry in entries]
assert len(set(ids))==len(ids)
for key in ids: assert key in text,key
assert all((p.extract_text() or '').strip() for p in reader.pages)
for name,digest in before.items(): assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest,name
print(f'PDF: {len(reader.pages)} pages; {len(entries)} entries; {len(paths)} valid local references; source files unchanged.')
