import re,html,sys,os,urllib.request,time
base=sys.argv[1]; os.makedirs(os.path.join(base,'qld'),exist_ok=True)
UA={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/128.0'}
def strip(t):
    t=re.sub(r'<(script|style)[^>]*>.*?</\1>','',t,flags=re.S|re.I)
    t=re.sub(r'</(p|div|li|h[1-6]|tr|br)>','\n',t,flags=re.I)
    t=re.sub(r'<[^>]+>',' ',t); t=html.unescape(t)
    t=re.sub(r'[ \t]+',' ',t); t=re.sub(r'\n\s*\n+','\n',t); return t
for court,year,maxn in [('qsc',2026,400),('qca',2026,300),('qsc',2025,400),('qca',2025,300)]:
    miss=0; got=0
    for n in range(1,maxn+1):
        url=f'https://www.queenslandjudgments.com.au/caselaw/{court}/{year}/{n}'
        try:
            r=urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=30); t=r.read().decode('utf-8','ignore')
        except Exception as e:
            miss+=1
            if miss>=8: break
            continue
        if 'SUPREME COURT OF QUEENSLAND' not in t and 'COURT OF APPEAL' not in t:
            miss+=1
            if miss>=8: break
            continue
        miss=0; got+=1
        i=t.find('SUPREME COURT OF QUEENSLAND')
        txt=strip(t[i-200 if i>200 else 0:])
        open(os.path.join(base,'qld',f'{court.upper()}_{year}_{n}.txt'),'w',encoding='utf-8').write(txt)
        time.sleep(0.3)
    print(court,year,'got',got,'stopped at',n,flush=True)
