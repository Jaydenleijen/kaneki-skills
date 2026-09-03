"""Harvest NSW Court of Appeal judgments from NSW Caselaw (server-rendered search + decision pages).
usage: harvest_nsw.py <base_dir> <page_param> <year> [<year> ...]
"""
import re, sys, os, time, html, urllib.request, urllib.parse

base, page_param = sys.argv[1], sys.argv[2]
years = sys.argv[3:]
COA = '54a634063004de94513d8278'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/128.0'}
out_dir = os.path.join(base, 'nsw')
os.makedirs(out_dir, exist_ok=True)


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read().decode('utf-8', 'ignore')


def strip(t):
    t = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', t, flags=re.S | re.I)
    t = re.sub(r'</(p|div|li|h[1-6]|tr|br)>', '\n', t, flags=re.I)
    t = re.sub(r'</?(span|a|b|i|em|strong|sup|sub|u|font)\b[^>]*>', '', t, flags=re.I)   # inline tags split words
    t = re.sub(r'<[^>]+>', ' ', t)
    t = html.unescape(t)
    t = re.sub(r'[ \t\xa0]+', ' ', t)
    return re.sub(r'\n\s*\n+', '\n', t)


for year in years:
    ids = {}
    for p in range(0, 40):
        url = (f'https://www.caselaw.nsw.gov.au/search?query=appeal&courts={COA}&_courts=on&_tribunals=on'
               f'&years={year}&_years=on&sort=&hide=&{page_param}={p}')
        try:
            t = get(url)
        except Exception as e:
            print('LISTFAIL', year, p, e, flush=True)
            break
        found = re.findall(r'href="/decision/([0-9a-f]+)"[^>]*>(.*?)</a>', t, flags=re.S)
        new = 0
        for i, title in found:
            if i not in ids:
                ids[i] = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', title)).strip()
                new += 1
        total = re.findall(r'([0-9,]+) results', t)
        print(year, 'page', p, 'new', new, 'total ids', len(ids), 'reported', total[:1], flush=True)
        if new == 0:
            break
        time.sleep(0.5)
    print(year, 'collected', len(ids), flush=True)
    for i, title in ids.items():
        out = os.path.join(out_dir, f'NSWCA_{year}_{i}.txt')
        if os.path.exists(out) and os.path.getsize(out) > 2000:
            continue
        try:
            h = get(f'https://www.caselaw.nsw.gov.au/decision/{i}')
        except Exception as e:
            print('DECFAIL', i, e, flush=True)
            continue
        cite = re.search(r'\[(20\d\d)\] NSWCA (\d+)', h)
        if not cite:
            print('NOCITE', i, title[:60], flush=True)
            continue
        os.makedirs(os.path.join(out_dir, 'html'), exist_ok=True)
        open(os.path.join(out_dir, 'html', f'NSWCA_{year}_{i}.html'), 'w', encoding='utf-8').write(h)
        txt = strip(h)
        open(out, 'w', encoding='utf-8').write(f'CITATION: [{cite.group(1)}] NSWCA {cite.group(2)}\nTITLE: {title}\n' + txt)
        time.sleep(0.4)
    print(year, 'done', flush=True)
