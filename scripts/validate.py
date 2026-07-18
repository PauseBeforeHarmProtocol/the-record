from __future__ import annotations
import json, re, sys
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site' if (ROOT / 'site').is_dir() else ROOT
errors = []
html_files = sorted(SITE.rglob('*.html'))
for page in html_files:
    text = page.read_text(encoding='utf-8')
    soup = BeautifulSoup(text, 'html.parser')
    if not soup.title or not soup.title.get_text(strip=True):
        errors.append(f'{page}: missing title')
    for a in soup.find_all('a', href=True):
        href = a['href'].split('#',1)[0].split('?',1)[0]
        if not href or re.match(r'^(https?:|mailto:|tel:|/)', href):
            continue
        target = (page.parent / href).resolve()
        if href.endswith('/'):
            target = target / 'index.html'
        if not target.exists():
            errors.append(f'{page.relative_to(SITE)} -> missing {href}')

entries = json.loads((SITE/'data/current_entries.json').read_text(encoding='utf-8'))
ids = {e['id'] for e in entries}
if len(ids) != len(entries): errors.append('duplicate entry IDs')
for e in entries:
    pack = SITE / e['pack_path']
    if not pack.exists(): errors.append(f"missing pack {e['pack_path']}")
    for key in ('facts','significance','goalpost','sources'):
        if not e.get(key): errors.append(f"{e['id']}: empty {key}")

# Prevent accidental credential publication.
secret_patterns = [r'github_pat_[A-Za-z0-9_]+', r'ghp_[A-Za-z0-9]+', r'BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY']
for p in SITE.rglob('*'):
    if p.is_file() and p.suffix.lower() in {'.html','.js','.css','.json','.md','.txt','.csv'}:
        text = p.read_text(encoding='utf-8', errors='ignore')
        for pat in secret_patterns:
            if re.search(pat, text): errors.append(f'{p}: possible secret')

if errors:
    print('FAIL')
    print('\n'.join(f'- {x}' for x in errors))
    sys.exit(1)
print(f'PASS: {len(html_files)} HTML files, {len(entries)} entries, all internal links and packs resolved; no credential patterns found.')
