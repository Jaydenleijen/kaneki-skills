import re, os, sys, glob, collections, statistics, random

base = sys.argv[1]
out = open(os.path.join(base, 'stats.md'), 'w', encoding='utf-8')


def P(*a):
    print(*a, file=out)


JUDGE = r"(?:[A-Z][A-Za-z'-]+(?: [A-Z][A-Za-z'-]+)? (?:CJ|J|JA|P|AJA|AJ))"
AUTHOR_HEAD = r"((?:[A-Z][A-Z'-]+(?: [A-Z][A-Z'-]+)? (?:CJ|J|JJ)(?:, | AND )?)+)\.\s"


def clean_hca(t):
    blocks = re.split(r'\n\s*\n', t)
    keep = []
    for b in blocks:
        s = b.strip()
        if not s:
            continue
        if re.match(r'^\d{1,3} \S', s) and not re.match(r'^\d{1,3}  ', s) and not re.match(r'^\d{1,3} ' + AUTHOR_HEAD, s):
            continue  # footnote block
        if re.match(r'^\d{1,3}\.?$', s):
            continue  # page number
        if re.match(r'^(?:' + JUDGE + r'\s*)+$', s):
            continue  # running header
        keep.append(re.sub(r'\s+', ' ', s))
    # rebuild real paragraphs: a new paragraph starts at a numbered line or a short heading
    paras = []
    for s in keep:
        is_num = re.match(r'^\d{1,3} ', s)
        is_heading = (len(s.split()) <= 8 and not re.search(r'[.;:,]$', s) and s[0].isupper() and not re.match(r'^\d', s)) or re.fullmatch(r"(?:[A-Z][A-Z'-]+(?: [A-Z][A-Z'-]+)? (?:CJ|J|JJ)(?:, | AND )?)+\.", s)
        if is_num or is_heading or not paras:
            paras.append(s)
        else:
            paras[-1] += ' ' + s
    t = '\n'.join(paras)
    # body starts at first authored paragraph 1
    m = re.search(r'(?:^|\n)1 ' + AUTHOR_HEAD, t)
    if m:
        t = t[m.start():]
    t = re.sub(r'(?m)^\d{1,3} ', '', t)          # paragraph numbers
    t = re.sub(r'([a-z\)\]"\'])\.(\d{1,3})\s', r'\1. ', t)  # footnote markers after full stops
    t = re.sub(r'([a-z\)\]"\'\,;])(\d{1,3})\s', r'\1 ', t)   # footnote markers after other chars
    return t


def clean_qld(t):
    starts = [m.start() for m in re.finditer(r'\n\s*\[1\]\s', t)]
    body = t[starts[0]:] if starts else t
    if len(starts) > 1:                       # footnotes restart numbering at [1]
        body = t[starts[0]:starts[1]]
    for marker in ['Editorial Notes', 'Published Case Name', 'Close Editorial', 'Cited by this judgment', 'Important Note', 'Thanks for reaching out']:
        i = body.find(marker)
        if i > 0:
            body = body[:i]
    body = re.sub(r'\[\d+\]\s+', '\n', body)
    body = re.sub(r'(?m)^\s*\d{1,3}\s*$', '', body)
    body = re.sub(r'(?m)^\s*Powered by.*$', '', body)
    return re.sub(r'\n\s*\n+', '\n', body)


ABBR = r'\b(?:s|ss|r|rr|cl|para|paras|pt|div|sch|no|nos|v|vol|op|cit|ibid|cf|eg|ie|etc|Mr|Mrs|Ms|Dr|Hon|Cth|Qld|NSW|Vic|J|JJ|CJ|JA|P|QC|SC|KC|Pty|Ltd|Co|Inc|St|Sen|Rep|Ex|Re|nn|fn|ch|art|arts|sub-s|subs|reg|regs|Jnr|Snr|Prof|Ors|Anor)\.'


def sentences(t):
    t = re.sub(ABBR, lambda m: m.group(0)[:-1] + '§', t)
    t = re.sub(r'(\d)\.(\d)', r'\1§\2', t)
    ss = re.split(r'(?<=[.?!])["\')\]]?\s+(?=[A-Z"\'(\[])', t)
    return [s.replace('§', '.').strip() for s in ss if len(s.split()) >= 3]


VJUDGE = r"(?:[A-Z][A-Za-z'-]*\.? )?[A-Z][A-Za-z'-]+"     # optional given name/initial + surname: WALKER, John DIXON, McCANN, T FORREST
VHEAD = r"(?m)^\**\s*(?:THE COURT|" + VJUDGE + r"(?:,? (?:AND|&) " + VJUDGE + r")*),? ?(?:JJA|JA|AJA|A-CJ|CJ|P|JR|J)\**\s*:"


def clean_vsca(t):
    """Firecrawl markdown of an AustLII judgment page."""
    for marker in ['#### Print', '#### Download', '#### Cited By', '#### Join the discussion']:
        i = t.find(marker)
        if i > 0:
            t = t[:i]
    lu = re.search(r'(?m)^Last Updated:.*$', t)   # AustLII site chrome sits above this
    if lu:
        t = t[lu.end():]
    toc = re.search(r'(?im)^\s*TABLE OF CONTENTS\b', t)
    heads = list(re.finditer(VHEAD, t))
    if heads:
        # first author heading that is not inside a table-of-contents line
        start = None
        for h in heads:
            line = t[h.start():t.find('\n', h.start()) if t.find('\n', h.start()) > 0 else len(t)]
            if len(line) < 120:                    # a real heading, not a TOC/sentence reference
                start = h.start()
                break
        if start is not None:
            t = t[start:]
    elif toc:
        t = t[toc.end():]
    else:
        cw = re.search(r'(?im)^\s*CATCHWORDS?\b', t)
        if cw:
            t = t[cw.end():]
    fn = re.search(r'(?m)^\[\\\[1\\\]\]\([^)]*#fnB1\)', t)              # footnote list starts here
    if fn:
        t = t[:fn.start()]
    t = re.sub(r'(?m)^\[\\\[\d+\\\]\]\([^)]*#fnB\d+\).*$', '', t)      # any stray footnote entries
    t = re.sub(r'\[\\\[\d+\\\]\]\([^)]*\)', '', t)                     # inline footnote markers
    t = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', t)                    # other links -> text
    t = re.sub(r'(?m)^\|.*$', '', t)                                  # tables
    t = re.sub(r'(?m)^#+ .*$', '', t)
    t = t.replace('\\[', '[').replace('\\]', ']').replace('\\-', '-')
    t = re.sub(r'[*_]{1,2}', '', t)
    # join soft-wrapped lines inside a paragraph; new paragraph at "N. " or a heading-like short line
    out = []
    for line in t.split('\n'):
        s = line.strip()
        if not s:
            continue
        if re.match(r'^\d{1,3}\.\s', s) or not out or (len(s.split()) <= 8 and not re.search(r'[.;:,]$', s) and s[0].isupper()):
            out.append(re.sub(r'^\d{1,3}\.\s+', '', s))
        else:
            out[-1] += ' ' + s
    return '\n'.join(out)


def clean_nsw(t):
    m = re.search(r'(?m)^\s*(JUDGMENT|REASONS FOR (?:JUDGMENT|DECISION)|REASONS)\s*$', t)
    if m:
        t = t[m.end():]
    for marker in ['DISCLAIMER - Every effort', '**********', 'Decision last updated']:
        i = t.find(marker)
        if i > 0:
            t = t[:i]
    t = re.sub(r'(?m)^\s*\d{1,3}\.?\s+(?=[A-Z"\'(\[])', '', t)   # paragraph numbers
    t = re.sub(r'(?m)^\s*\d{1,3}\s*$', '', t)
    return re.sub(r'\n\s*\n+', '\n', t)


def load(court):
    if court == 'HCA':
        files = sorted(glob.glob(os.path.join(base, 'hca', 'txt', 'HCA_*.txt')))
    elif court == 'VSCA':
        files = sorted(glob.glob(os.path.join(base, 'fc', 'vsca_md', 'VSCA_2026_*.md')))
    elif court == 'NSWCA':
        files = sorted(glob.glob(os.path.join(base, 'nsw', 'NSWCA_*.txt')))
    else:
        files = sorted(glob.glob(os.path.join(base, 'qld', court + '_*.txt')))
    docs = {}
    for f in files:
        t = open(f, encoding='utf-8', errors='ignore').read()
        if court == 'HCA':
            c = clean_hca(t)
        elif court == 'VSCA':
            c = clean_vsca(t)
            n = re.search(r'VSCA[_-]2026[_-](\d+)', os.path.basename(f))
            docs['VSCA_2026_' + (n.group(1) if n else os.path.basename(f))] = c
            continue
        elif court == 'NSWCA':
            c = clean_nsw(t)
        else:
            c = clean_qld(t)
        docs[os.path.basename(f)[:-4]] = c
    return docs


corp = {c: load(c) for c in ['HCA', 'QCA', 'QSC', 'NSWCA', 'VSCA']}

TERMS = {
    'Hedging / calibration': ['arguably', 'may be', 'might', 'appears', 'seems', 'perhaps', 'not necessarily', 'on balance', 'in my view', 'in my opinion', 'in our view', 'in our opinion', 'i am satisfied', 'i accept', 'i am not persuaded', 'i am not satisfied', 'it is unnecessary to', 'it is not necessary to', 'need not', 'it suffices', 'tolerably clear', 'at least', 'to some extent', 'not without', 'difficult to see', 'open to', 'tend to', 'likely', 'doubtful', 'it may be accepted', 'it may be that', 'i do not accept', 'i am not persuaded', 'i prefer', 'i consider', 'i find', 'i infer'],
    'Decisive / conclusory': ['it follows that', 'it follows', 'accordingly', 'for those reasons', 'for these reasons', 'the answer is', 'the short answer', 'that is because', 'plainly', 'clearly', 'necessarily', 'must', 'cannot', 'there is no', 'it is well established', 'it is settled', 'the better view', 'correctly', 'wrongly', 'erred', 'no error', 'the result is', 'should be rejected', 'cannot be accepted', 'must be rejected', 'should be accepted', 'is not to the point', 'beside the point', 'does not assist', 'misconceived', 'untenable'],
    'Attribution of argument': ['submitted', 'submits', 'submission', 'contended', 'contends', 'contention', 'argued', 'argues', 'argument', 'asserted', 'maintained', 'it was said', 'it was put', 'put in this way', 'sought to', 'relied on', 'relied upon', 'reliance', 'counsel for', 'senior counsel'],
    'Courtesy / disagreement': ['with respect', 'with great respect', 'respectfully', 'i am unable to agree', 'i agree with', 'i would', 'his honour', 'her honour', 'their honours', 'the primary judge', 'the trial judge', 'the learned', 'the court below', 'the majority', 'in dissent', 'i agree', 'for the reasons given by', 'i have had the advantage', 'i gratefully adopt'],
    'Statutory construction': ['text, context and purpose', 'properly construed', 'proper construction', 'on its proper construction', 'ordinary meaning', 'natural and ordinary', 'statutory scheme', 'the legislature', 'parliament', 'legislative purpose', 'statutory purpose', 'the provision', 'the section', 'the words', 'operates', 'engaged', 'enliven', 'enlivened', 'within the meaning of', 'for the purposes of', 'so construed', 'construction', 'purposive'],
    'Latin / legal formulae': ['prima facie', 'inter alia', 'ratio decidendi', 'obiter', 'ex parte', 'bona fide', 'mutatis mutandis', 'per se', 'a fortiori', 'de novo', 'inter se', 'sui generis', 'ex hypothesi', 'in limine', 'ab initio', 'quantum', 'ipso facto', 'pro tanto', 'sub silentio', 'simpliciter', 'ex tempore', 'nunc pro tunc', 'in personam', 'in rem', 'mens rea', 'actus reus', 'ultra vires', 'functus officio', 'res judicata', 'locus standi', 'onus'],
    'Archaic / legalese': ['hereinafter', 'aforesaid', 'the said', 'whereby', 'wherein', 'hereby', 'notwithstanding', 'thereto', 'therein', 'thereof', 'hereof', 'thereby', 'hereto', 'herein', 'forthwith', 'aforementioned', 'henceforth', 'whilst', 'amongst', 'albeit', 'save that', 'save for'],
    'Connectives': ['however', 'moreover', 'further,', 'furthermore', 'nevertheless', 'nonetheless', 'rather,', 'that is,', 'put differently', 'in other words', 'in short', 'first,', 'secondly', 'thirdly', 'second,', 'third,', 'finally', 'relevantly', 'critically', 'importantly', 'significantly', 'ultimately', 'consequently', 'thus', 'hence', 'indeed', 'conversely', 'by contrast', 'in any event', 'in the present case', 'in this case', 'here,', 'so understood', 'so much', 'of course', 'but', 'nor', 'yet,', 'equally', 'likewise', 'to the contrary', 'on the contrary', 'in that regard', 'in this regard', 'in that respect', 'to that extent', 'on that basis', 'on any view', 'at all events'],
    'Framing devices': ['the question is', 'the issue is', 'the question whether', 'the real question', 'the central question', 'the critical question', 'the starting point', 'it is convenient', 'it is appropriate', 'it is necessary', 'before turning', 'turning to', 'i turn', 'we turn', 'for the following reasons', 'for reasons that follow', 'the following reasons', 'in summary', 'to summarise', 'in the result', 'the appeal should be', 'the appeal must be', 'the application should be', 'dismissed with costs', 'allowed with costs', 'it is unnecessary', 'the point may be illustrated', 'two things', 'three things', 'several reasons', 'a number of reasons', 'the difficulty with', 'the problem with', 'the answer to', 'the premise', 'the proposition', 'the point'],
    'AI-isms (should be ~0)': ['delve', 'leverage', 'navigate', 'tapestry', 'multifaceted', 'robust', 'crucial', 'pivotal', 'underscore', 'landscape', 'holistic', 'streamline', 'it is important to note', 'it is worth noting', 'in conclusion', 'additionally', 'moreover,', 'showcase', 'testament to', 'in today\'s', 'ensure that', 'foster', 'seamless', 'nuanced', 'comprehensive'],
}


def per10k(n, words):
    return n * 10000 / words if words else 0


def count(term, low):
    return len(re.findall(r'(?<![a-z])' + re.escape(term) + r'(?![a-z])', low))


def analyse(name, docs):
    text = '\n'.join(docs.values())
    low = text.lower()
    words = len(re.findall(r"[A-Za-z']+", text))
    ss = sentences(text)
    lens = [len(s.split()) for s in ss]
    P(f'\n# {name}: {len(docs)} judgments, {words:,} words, {len(ss):,} sentences\n')
    P(f'- Mean sentence length: {statistics.mean(lens):.1f} words; median {statistics.median(lens):.0f}; 10th pct {sorted(lens)[len(lens)//10]}; 90th pct {sorted(lens)[9*len(lens)//10]}')
    P(f'- Sentences under 10 words: {100*sum(l<10 for l in lens)/len(lens):.1f}%; 10-25 words: {100*sum(10<=l<=25 for l in lens)/len(lens):.1f}%; over 40 words: {100*sum(l>40 for l in lens)/len(lens):.1f}%')
    paras = [p for p in text.split('\n') if len(p.split()) > 15]
    pl = [len(p.split()) for p in paras]
    P(f'- Mean paragraph length: {statistics.mean(pl):.0f} words (median {statistics.median(pl):.0f}); mean sentences per paragraph {statistics.mean([len(sentences(p)) for p in paras]):.1f}')
    wl = [len(w) for w in re.findall(r"[A-Za-z']+", text)]
    P(f'- Mean word length {statistics.mean(wl):.2f}; words of 10+ letters {100*sum(l>=10 for l in wl)/len(wl):.1f}%')
    passive = len(re.findall(r'\b(?:is|are|was|were|be|been|being)\s+(?:\w+ly\s+)?\w+(?:ed|en|ought|ught|ade|one|aid|eld|ound)\b', text))
    P(f'- Passive-ish constructions per 10k words: {per10k(passive,words):.0f}')
    fp_i = len(re.findall(r'\bI\b', text))
    fp_we = len(re.findall(r'\b[Ww]e\b', text))
    P(f'- "I" per 10k: {per10k(fp_i,words):.0f}; "we" per 10k: {per10k(fp_we,words):.0f}; "the Court" per 10k: {per10k(text.count("the Court"),words):.0f}; "this Court" per 10k: {per10k(text.count("this Court"),words):.0f}')
    P(f'- Semicolons per 10k words: {per10k(text.count(";"),words):.0f}; colons {per10k(text.count(":"),words):.0f}; em/en dashes {per10k(text.count(chr(8212))+text.count(chr(8211)),words):.0f}; parentheses {per10k(text.count("("),words):.0f}; double quotes {per10k(text.count(chr(34))+text.count(chr(8220)),words):.0f}; exclamation marks {text.count("!")}; question marks per 10k {per10k(text.count("?"),words):.1f}')
    contractions = len(re.findall(r"\b(?:don't|doesn't|isn't|wasn't|can't|won't|it's|that's|there's|didn't|couldn't|wouldn't|shouldn't|hasn't|haven't|aren't|weren't)\b", low))
    P(f'- Contractions per 10k words: {per10k(contractions,words):.1f} (mostly inside quoted evidence)')
    for cat, terms in TERMS.items():
        rows = sorted(((per10k(count(t, low), words), t) for t in terms), reverse=True)
        P(f'\n## {cat}\n')
        P('| term | per 10k words |')
        P('|---|---|')
        for r, t in rows:
            if r > 0:
                P(f'| {t} | {r:.1f} |')
        zero = [t for r, t in rows if r == 0]
        if zero:
            P(f'\nZero occurrences: {", ".join(zero)}')
    op = collections.Counter()
    op2 = collections.Counter()
    for s in ss:
        w = s.split()
        if w:
            op[re.sub(r'[^A-Za-z]', '', w[0])] += 1
        if len(w) > 1:
            op2[' '.join(re.sub(r'[^A-Za-z,]', '', x) for x in w[:2])] += 1
    P('\n## Most common sentence openers (single word)\n')
    P(', '.join(f'{k} ({100*v/len(ss):.1f}%)' for k, v in op.most_common(40) if k))
    P('\n## Most common two-word openers\n')
    P(', '.join(f'"{k}" ({v})' for k, v in op2.most_common(60)))
    toks = re.findall(r"[a-z']+", low)
    STOP = {'of', 'the', 'in', 'to', 'and', 'a', 'that', 'is', 'it', 'be', 'by', 'as', 'was', 'for', 'or', 'an', 'on', 'with', 'at', 'not', 'which', 'this', 'from', 'are', 'has', 'have', 'had', 'been', 'were', 'his', 'her', 'their', 'its', 'he', 'she', 'they', 'i', 'would', 'should', 'may', 'must', 'can', 'could', 'no', 'any', 'so', 'if', 'but', 'than', 'then', 'there', 'those', 'these', 'such', 'what', 'who', 'whom', 'whose', 'into', 'under', 'upon', 'about', 'between', 'each', 'other', 'more', 'also', 'only', 'all', 'some', 'one', 'two', 'do', 'does', 'did', 'will', 'shall', 'being', 'because', 'whether', 'when', 'where', 'while', 'after', 'before', 'both', 'out', 'up', 'made'}
    ng = collections.Counter(zip(toks, toks[1:], toks[2:], toks[3:]))
    P('\n## Frequent 4-grams (needing at least 2 content words; case/statute names filtered)\n')
    P(', '.join(f'"{" ".join(k)}" ({v})' for k, v in ng.most_common(1500) if len(set(k) - STOP) >= 2 and not re.search(r'court|act|australia|wales|queensland|victoria|territory|cj|jj|s$|ss$|pty|ltd|minister|commonwealth|constitution|division|section', ' '.join(k)))[:3500])
    tri = collections.Counter(zip(toks, toks[1:], toks[2:]))
    P('\n## Frequent 3-grams that are discourse moves (start with it/that/this/there/as/so/nor/but)\n')
    P(', '.join(f'"{" ".join(k)}" ({v})' for k, v in tri.most_common(20000) if k[0] in {'it', 'that', 'this', 'there', 'as', 'so', 'nor', 'but', 'no', 'nothing', 'whether'} and len(set(k) - STOP) >= 1)[:3000])
    short = [s for s in ss if 4 <= len(s.split()) <= 10 and not re.search(r'\d|"|“', s) and s[0].isupper()]
    random.seed(1)
    P('\n## Sample short sentences (4-10 words, no quotes or numbers)\n')
    for s in random.sample(short, min(60, len(short))):
        P(f'- {s}')
    return ss


for c, d in corp.items():
    if d:
        analyse(c, d)

P('\n\n# HCA per-author blocks (reasons split on the judge-name heading)\n')
auth = collections.defaultdict(list)
for k, t in corp['HCA'].items():
    parts = re.split(r'(?:^|\n)' + AUTHOR_HEAD, t)
    for i in range(1, len(parts) - 1, 2):
        auth[parts[i].strip()].append(parts[i + 1])
rows = []
for a, ts in auth.items():
    text = '\n'.join(ts)
    low = text.lower()
    words = len(re.findall(r"[A-Za-z']+", text))
    if words < 12000:
        continue
    ss = sentences(text)
    lens = [len(s.split()) for s in ss]
    rows.append((a, len(ts), words, statistics.mean(lens), statistics.median(lens), 100 * sum(l < 10 for l in lens) / len(lens), per10k(len(re.findall(r'\bI\b', text)), words), per10k(count('it follows', low), words), per10k(count('however', low), words), per10k(count('with respect', low), words), per10k(count('accordingly', low), words), per10k(count('must', low), words), per10k(count('may be', low) + count('might', low), words), per10k(text.count(':'), words), per10k(text.count(';'), words), per10k(count('but', low), words)))
P('| author block | reasons | words | mean sent | median sent | % <10w | "I"/10k | it follows | however | with respect | accordingly | must | may be+might | colons | semicolons | but |')
P('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
for r in sorted(rows, key=lambda r: -r[2]):
    P('| ' + ' | '.join([r[0], str(r[1]), f'{r[2]:,}'] + [f'{x:.1f}' for x in r[3:]]) + ' |')

os.makedirs(os.path.join(base, 'clean'), exist_ok=True)
for c, d in corp.items():
    for k, t in d.items():
        open(os.path.join(base, 'clean', k + '.txt'), 'w', encoding='utf-8').write(t)
out.close()
print('ok')
