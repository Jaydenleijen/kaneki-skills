import re,sys,os,urllib.request,subprocess,time
base,pdftotext=sys.argv[1],sys.argv[2]
UA={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/128.0'}
os.makedirs(os.path.join(base,'hca','pdf'),exist_ok=True); os.makedirs(os.path.join(base,'hca','txt'),exist_ok=True)
def get(url):
    return urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=60).read()
ok=0
for line in open(os.path.join(base,'hca','list_u.tsv'),encoding='utf-8'):
    yr,num,slug=line.rstrip('\n').split('\t')
    if yr=='?': continue
    out=os.path.join(base,'hca','txt',f'HCA_{yr}_{num}.txt')
    if os.path.exists(out) and os.path.getsize(out)>1000: ok+=1; continue
    try:
        page=get(f'https://www.hcourt.gov.au/cases-and-judgments/judgments/judgments-1998-current/{slug}').decode('utf-8','ignore')
    except Exception as e:
        print('PAGEFAIL',slug,e,flush=True); continue
    m=re.search(r'href="([^"]*\.pdf[^"]*)"',page)
    if not m: print('NOPDF',slug,flush=True); continue
    href=m.group(1); url=href if href.startswith('http') else 'https://www.hcourt.gov.au'+href
    pdf=os.path.join(base,'hca','pdf',f'HCA_{yr}_{num}.pdf')
    try:
        open(pdf,'wb').write(get(url))
    except Exception as e:
        print('PDFFAIL',slug,e,flush=True); continue
    r=subprocess.run([pdftotext,'-layout',pdf,out],capture_output=True)
    if r.returncode!=0: print('P2TFAIL',slug,r.stderr[:200],flush=True); continue
    ok+=1; time.sleep(0.4)
print('done',ok,flush=True)
