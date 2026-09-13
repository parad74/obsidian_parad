from pathlib import Path
import re, html, sys, json, hashlib
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader


ROOT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parent.parent
README_PATH=ROOT/'README.md'
STAGE_PATH=ROOT
required=[
    'podoconnik_drawing_mm.dxf','podoconnik_contour_mm.dxf','podoconnik_section_HV_mm.dxf',
    'podoconnik_volume_3d_mm.dxf','podoconnik_volume_mm.stl','podoconnik_preview.png',
    'podoconnik_drawing.svg','podoconnik_drawing.png','verification.json','README.md',
    'work/stl_verification.json','work/run_parameters.json','work/build_podoconnik3.py',
    'work/convert_podoconnik_stl.py','work/build_project_pdf.py','work/requirements.txt']
assert all((ROOT/name).is_file() and (ROOT/name).stat().st_size>0 for name in required)
params=json.loads((ROOT/'work/run_parameters.json').read_text(encoding='utf8'))
verification=json.loads((ROOT/'verification.json').read_text(encoding='utf8'))
stl_verification=json.loads((ROOT/'work/stl_verification.json').read_text(encoding='utf8'))
for name,entry in verification.items():
    if name.endswith('.dxf'):
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==entry['sha256']
assert hashlib.sha256((ROOT/'podoconnik_volume_mm.stl').read_bytes()).hexdigest()==stl_verification['output_sha256']
assert verification['geometry']['envelope_mm']==[params['length_mm'],params['depth_mm'],params['height_mm']]
assert stl_verification['size_mm']==verification['geometry']['envelope_mm']
before={str(p.relative_to(ROOT)):(p.stat().st_mtime_ns,hashlib.sha256(p.read_bytes()).hexdigest())
        for p in ROOT.rglob('*') if p.is_file() and p.name!='project_overview.pdf'}
pdfmetrics.registerFont(TTFont('Arial','C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('ArialBold','C:/Windows/Fonts/arialbd.ttf'))
pdfmetrics.registerFont(TTFont('Mono','C:/Windows/Fonts/consola.ttf'))
pdfmetrics.registerFontFamily('Arial',normal='Arial',bold='ArialBold',italic='Arial',boldItalic='ArialBold')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='Main',fontName='Arial',fontSize=9,leading=12,spaceAfter=5,textColor=colors.HexColor('#25364a')))
styles.add(ParagraphStyle(name='TitleRu',fontName='ArialBold',fontSize=21,leading=25,spaceAfter=15,textColor=colors.HexColor('#163950')))
styles.add(ParagraphStyle(name='HeadingRu',fontName='ArialBold',fontSize=13,leading=17,spaceBefore=11,spaceAfter=6,keepWithNext=True,textColor=colors.HexColor('#12647b')))
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
            ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
            ('LINEBELOW',(0,0),(-1,0),0.6,colors.HexColor('#b6ccd6'))]))
        story.extend([table,Spacer(1,8)])
    elif s.startswith('!['):
        story.extend([Image(str(STAGE_PATH/'podoconnik_preview.png'),width=515,height=386.25),Spacer(1,8)])
    elif s.startswith('- '): story.append(Paragraph('• '+inline(s[2:]),styles['Main']))
    else:
        parts=[s]
        while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|','- ','![')):
            parts.append(lines[i].strip()); i+=1
        story.append(Paragraph(inline(' '.join(parts)),styles['Main']))

def page_frame(c,doc):
    c.setTitle(f'Подоконник {params["length_mm"]:g} x {params["depth_mm"]:g} x 30 мм - DXF и STL')
    c.setAuthor('stone_project')
    c.setFont('Arial',8)
    c.setFillColor(colors.HexColor('#657988'))
    c.drawString(40,23,f'out3 / {params["length_mm"]:g} x {params["depth_mm"]:g} x 30 mm / ArtCAM 2018 / На проверке')
    c.drawRightString(A4[0]-40,23,str(doc.page))
    c.setStrokeColor(colors.HexColor('#cbd7df'))
    c.line(40,36,A4[0]-40,36)

target=README_PATH.parent/'project_overview.pdf'
doc=SimpleDocTemplate(str(target),pagesize=A4,leftMargin=40,rightMargin=40,
                     topMargin=40,bottomMargin=50,allowSplitting=True)
doc.build(story,onFirstPage=page_frame,onLaterPages=page_frame)
reader=PdfReader(target)
text='\n'.join(p.extract_text() or '' for p in reader.pages)
for term in [f'{params["length_mm"]:g}',f'{params["depth_mm"]:g}','13,5','0,002556','1250','лев','ArtCAM','3DFACE','STL']:
    assert term in text,term
assert all(p.extract_text().strip() for p in reader.pages)
print(f'PDF: {len(reader.pages)} pages, {target.stat().st_size} bytes; text checks passed.')

for name,(mtime,digest) in before.items():
    assert (ROOT/name).stat().st_mtime_ns==mtime
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest
assert target.stat().st_mtime_ns>=max(mtime for mtime,_ in before.values())
print('PDF LAST: all other package files existed and matched their checksums before PDF creation; unchanged afterwards.')
