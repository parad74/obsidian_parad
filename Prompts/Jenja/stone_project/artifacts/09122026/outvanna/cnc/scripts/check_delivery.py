from pathlib import Path
import sys,json,re,hashlib
from urllib.parse import unquote
OUT=Path(__file__).resolve().parents[2]
ROOT=OUT.parents[3]
sys.path.insert(0,str(OUT/'work/python_packages'))
import pymupdf
from PIL import Image,ImageDraw

report={}
for md in (OUT/'README.md',ROOT/'CATALOG_PARAD.md'):
    links=re.findall(r'\]\(([^)]+)\)',md.read_text(encoding='utf-8-sig'))
    for link in links:
        if '://' not in link:assert (md.parent/unquote(link)).exists(),(md,link)
    report[str(md.name)+'_links']=len(links)
p=json.loads((OUT/'cnc/data/parameters.json').read_text(encoding='utf-8'))
assert hashlib.sha256(Path(p['source']).read_bytes()).hexdigest()==p['source_sha256']
for name,sha in json.loads((OUT/'cnc/data/output_sha256.json').read_text()).items():
    assert hashlib.sha256((OUT/name).read_bytes()).hexdigest()==sha,name
report['source_and_nc_dxf_hashes_match']=True
cat=pymupdf.open(ROOT/'CATALOG_PARAD.PDF')
assert len(cat)==19 and 'PARAD-017' in cat[-1].get_text()
report['catalog_pages']=len(cat)
renders=OUT/'work/pdf_pages'
for i in (0,1,18):cat[i].get_pixmap(matrix=pymupdf.Matrix(1.25,1.25)).save(renders/f'catalog_{i+1}.png')
for batch in range((len(cat)+5)//6):
    sheet=Image.new('RGB',(960,1360),'#c5cdd0');draw=ImageDraw.Draw(sheet)
    for j in range(6):
        i=batch*6+j
        if i>=len(cat):break
        pix=cat[i].get_pixmap(matrix=pymupdf.Matrix(.5,.5))
        im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
        im.thumbnail((460,425))
        x=(j%2)*480+10;y=(j//2)*450+20
        sheet.paste(im,(x,y));draw.text((x,y-15),str(i+1),fill='black')
    sheet.save(renders/f'catalog_contact_{batch+1}.png')
# Text bounds check supplements visual review, not a replacement for it.
for path in (OUT/'project_overview.pdf',ROOT/'CATALOG_PARAD.PDF'):
    doc=pymupdf.open(path)
    for i,page in enumerate(doc):
        assert page.get_text().strip()
        for b in page.get_text('blocks'):
            assert b[0]>=-1 and b[1]>=-1 and b[2]<=page.rect.width+1 and b[3]<=page.rect.height+1,(path,i,b[:4])
report['pdf_text_within_pages']=True
(OUT/'cnc/data/delivery_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
