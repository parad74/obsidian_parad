from pathlib import Path
import sys,re,html,json,hashlib
from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,TableStyle,Image,Spacer,PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader
ROOT=Path(sys.argv[1]).resolve()
manifest=json.loads((ROOT/'work/package_manifest.json').read_text(encoding='utf8'))
for name,digest in manifest.items():
 assert (ROOT/name).is_file() and hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
before={str(p.relative_to(ROOT)):(p.stat().st_mtime_ns,hashlib.sha256(p.read_bytes()).hexdigest()) for p in ROOT.rglob('*') if p.is_file() and p.name!='project_overview.pdf'}
for name,file in [('Arial','arial.ttf'),('ArialBold','arialbd.ttf'),('Mono','consola.ttf')]:pdfmetrics.registerFont(TTFont(name,'C:/Windows/Fonts/'+file))
styles={
 'body':ParagraphStyle('Body',fontName='Arial',fontSize=9,leading=12,spaceAfter=6,textColor=colors.HexColor('#25364a')),
 'title':ParagraphStyle('Title',fontName='ArialBold',fontSize=22,leading=26,spaceAfter=13,textColor=colors.HexColor('#17445b')),
 'heading':ParagraphStyle('Heading',fontName='ArialBold',fontSize=13,leading=17,spaceBefore=10,spaceAfter=7,keepWithNext=True,textColor=colors.HexColor('#12647b')),
 'cell':ParagraphStyle('Cell',fontName='Arial',fontSize=8.2,leading=11,spaceAfter=0),
}
def inline(s):
 s=html.escape(s);s=re.sub(r'`([^`]+)`',r'<font name="Mono">\1</font>',s);return s
lines=(ROOT/'README.md').read_text(encoding='utf8').splitlines();story=[];i=0
while i<len(lines):
 s=lines[i].strip();i+=1
 if not s:continue
 if s=='<!-- pagebreak -->':story.append(PageBreak())
 elif s.startswith('# '):story.append(Paragraph(inline(s[2:]),styles['title']))
 elif s.startswith('## '):story.append(Paragraph(inline(s[3:]),styles['heading']))
 elif s.startswith('!['):
  name=re.search(r'\]\(([^)]+)\)',s)[1]
  if 'stock_' in name:width,height=410,410*1780/1150
  else:width,height=480,400
  story.extend([Image(str(ROOT/name),width=width,height=height),Spacer(1,6)])
 elif s.startswith('|'):
  rows=[s]
  while i<len(lines) and lines[i].strip().startswith('|'):rows.append(lines[i].strip());i+=1
  cells=[]
  for row in rows:
   raw=[v.strip() for v in row.strip('|').split('|')]
   if all(re.fullmatch(r'[-: ]+',v) for v in raw):continue
   cells.append([Paragraph(inline(v),styles['cell']) for v in raw])
  table=Table(cells,colWidths=[220,295],repeatRows=1)
  table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dfedf2')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f4f7f9')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
  story.extend([table,Spacer(1,7)])
 else:story.append(Paragraph(('• ' if s.startswith('- ') else '')+inline(s[2:] if s.startswith('- ') else s),styles['body']))
def frame(c,d):
 c.setTitle('Столешница острова - лист 1645 x 3200 - out4');c.setAuthor('stone_project')
 c.setFont('Arial',8);c.setFillColor(colors.HexColor('#657988'))
 c.drawString(40,23,'out4 / 13.09.2026 / Поворот 5° / На пользовательской проверке');c.drawRightString(A4[0]-40,23,str(d.page))
 c.setStrokeColor(colors.HexColor('#cbd7df'));c.line(40,36,A4[0]-40,36)
target=ROOT/'project_overview.pdf'
SimpleDocTemplate(str(target),pagesize=A4,leftMargin=40,rightMargin=40,topMargin=38,bottomMargin=50).build(story,onFirstPage=frame,onLaterPages=frame)
r=PdfReader(target);txt='\n'.join(p.extract_text() or '' for p in r.pages)
for term in ['1645','3200','25 мм','669,577','135330','STL','0,022']:assert term in txt,term
assert all(p.extract_text().strip() for p in r.pages)
for name,(mtime,digest) in before.items():
 assert (ROOT/name).stat().st_mtime_ns==mtime and hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
assert target.stat().st_mtime_ns>=max(v[0] for v in before.values())
print(f'PDF LAST verified: {len(r.pages)} pages; other files unchanged. {target.stat().st_size} bytes.')
