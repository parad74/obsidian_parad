from pathlib import Path
import re, html, sys
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parent
STAGE_PATH=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT.parent/'out1'
README_PATH=STAGE_PATH/'README.md'
pdfmetrics.registerFont(TTFont('Arial','C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('ArialBold','C:/Windows/Fonts/arialbd.ttf'))
pdfmetrics.registerFont(TTFont('Mono','C:/Windows/Fonts/consola.ttf'))
pdfmetrics.registerFontFamily('Arial',normal='Arial',bold='ArialBold',italic='Arial',boldItalic='ArialBold')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='Main',fontName='Arial',fontSize=9.3,leading=12.8,spaceAfter=6,textColor=colors.HexColor('#25364a')))
styles.add(ParagraphStyle(name='TitleRu',fontName='ArialBold',fontSize=21,leading=25,spaceAfter=15,textColor=colors.HexColor('#163950')))
styles.add(ParagraphStyle(name='HeadingRu',fontName='ArialBold',fontSize=13,leading=17,spaceBefore=13,spaceAfter=7,keepWithNext=True,textColor=colors.HexColor('#12647b')))
styles.add(ParagraphStyle(name='Cell',parent=styles['Main'],fontSize=8.3,leading=11,spaceAfter=0))
styles.add(ParagraphStyle(name='SmallRu',parent=styles['Main'],fontSize=8,leading=11))

def inline(s):
    s=html.escape(s)
    s=re.sub(r'`([^`]+)`',r'<font name="Mono">\1</font>',s)
    s=re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',r'<link href="\2" color="#12647b"><u>\1</u></link>',s)
    return s

lines=README_PATH.read_text(encoding='utf-8-sig').splitlines()
story=[]; i=0
while i<len(lines):
    s=lines[i].strip(); i+=1
    if not s: continue
    if s.startswith('# '): story.append(Paragraph(inline(s[2:]),styles['TitleRu']))
    elif s.startswith('## '): story.append(Paragraph(inline(s[3:]),styles['HeadingRu']))
    elif s.startswith('|'):
        rows=[s]
        while i<len(lines) and lines[i].strip().startswith('|'):
            rows.append(lines[i].strip()); i+=1
        cells=[]
        for row in rows:
            raw=[x.strip() for x in row.strip('|').split('|')]
            if all(re.fullmatch(r'[:\- ]+',v) for v in raw): continue
            cells.append([Paragraph(inline(v),styles['Cell']) for v in raw])
        table=Table(cells,colWidths=[224,291],repeatRows=1,hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e1edf2')),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f5f8fa')]),
            ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
            ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
            ('LINEBELOW',(0,0),(-1,0),0.6,colors.HexColor('#b6ccd6'))]))
        story.extend([table,Spacer(1,8)])
    elif s.startswith('!['):
        story.extend([Image(str(STAGE_PATH/'sill_preview.png'),width=515,height=386.25),Spacer(1,8)])
    elif s.startswith('- '): story.append(Paragraph('• '+inline(s[2:]),styles['Main']))
    else:
        parts=[s]
        while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|','- ','![')):
            parts.append(lines[i].strip()); i+=1
        story.append(Paragraph(inline(' '.join(parts)),styles['Main']))

def page_frame(c,doc):
    c.setTitle('Подоконник - описание проекта и результаты первого этапа')
    c.setAuthor('stone_project')
    c.setFont('Arial',8)
    c.setFillColor(colors.HexColor('#657988'))
    c.drawString(40,23,'stone_project / ArtCAM 2018 / 12.09.2026 / На проверке')
    c.drawRightString(A4[0]-40,23,str(doc.page))
    c.setStrokeColor(colors.HexColor('#cbd7df'))
    c.line(40,36,A4[0]-40,36)

target=README_PATH.parent/'project_overview.pdf'
doc=SimpleDocTemplate(str(target),pagesize=A4,leftMargin=40,rightMargin=40,
                     topMargin=40,bottomMargin=50,allowSplitting=True)
doc.build(story,onFirstPage=page_frame,onLaterPages=page_frame)
reader=PdfReader(target)
text='\n'.join(p.extract_text() or '' for p in reader.pages)
for term in ['1600','1500','270','13,5','0,00256','ArtCAM','3DFACE','Review']:
    assert term in text,term
assert all(p.extract_text().strip() for p in reader.pages)
print(f'PDF: {len(reader.pages)} pages, {target.stat().st_size} bytes; text checks passed.')
