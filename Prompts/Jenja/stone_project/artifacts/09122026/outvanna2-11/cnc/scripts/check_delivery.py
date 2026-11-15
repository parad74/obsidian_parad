"""Verify the exported files, original images embedded in the PDF, and catalog entry."""
import hashlib
import io
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

out = Path(__file__).resolve().parents[2]
old = out.parent / 'outvanna2'
jenja = out.parents[3]
sys.path.insert(0, str(out.parent/'outvanna/work/python_packages'))
import pymupdf
from PIL import Image, ImageChops


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_manifest(folder):
    items = json.loads((folder / 'cnc/data/output_sha256.json').read_text('utf-8'))
    for name, expected in items.items():
        assert sha256(folder / name) == expected, folder / name
    return len(items)


def check_links(path):
    targets = re.findall(r'\]\(([^)]+)\)', path.read_text('utf-8-sig'))
    for target in targets:
        assert (path.parent / unquote(target)).exists(), target
    return len(targets)


summary = {'current_manifest_files': check_manifest(out),
           'previous_release_manifest_files': check_manifest(old),
           'readme_links': check_links(out / 'README.md'),
           'catalog_links': check_links(jenja / 'CATALOG_PARAD.md')}
baseline = json.loads((out/'work/source_project_hashes.json').read_text('utf-8'))
for name, expected in baseline.items():
    assert sha256(old/name) == expected, name
summary['previous_project_files_unchanged'] = len(baseline)
params = json.loads((out / 'cnc/data/parameters.json').read_text('utf-8'))
with pymupdf.open(out / 'project_overview.pdf') as doc:
    summary['project_pages'] = len(doc)
    for page in doc:
        assert page.get_text().strip()
        for word in page.get_text('words'):
            assert page.rect.contains(pymupdf.Rect(word[:4])), (page.number, word)
    for index, key in enumerate(('source', 'overlay')):
        path = out / params[key]
        assert sha256(path) == params[key + '_sha256']
        ref, = doc[index].get_images()
        data = doc.extract_image(ref[0])['image']
        with Image.open(path) as expected, Image.open(io.BytesIO(data)) as embedded:
            assert expected.size == embedded.size, key
            assert ImageChops.difference(expected.convert('RGB'), embedded.convert('RGB')).getbbox() is None, key
        summary[f'page_{index+1}_matches'] = path.name

with pymupdf.open(jenja / 'CATALOG_PARAD.PDF') as catalog:
    summary['catalog_pages'] = len(catalog)
    match, = [item for item in catalog.get_toc() if item[1].startswith(params['catalog_id'])]
    entry = catalog[match[2] - 1]
    assert params['catalog_id'] in entry.get_text()
    assert 'outvanna2-11' in entry.get_text() and entry.get_images() and entry.get_links()
    summary['catalog_entry_page'] = match[2]

summary['test_program_sha256'] = {p.name: sha256(p) for p in sorted((out/'cnc/test_checks').glob('*.nc'))}
summary['project_pdf_sha256'] = sha256(out / 'project_overview.pdf')
(out / 'cnc/data/delivery_verification.json').write_text(
    json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
