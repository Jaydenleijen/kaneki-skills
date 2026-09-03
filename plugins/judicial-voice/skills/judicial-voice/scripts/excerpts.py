"""Pull candidate exemplary paragraphs out of the cleaned corpus for curation."""
import re, os, sys, glob, random

base = sys.argv[1]
out = open(os.path.join(base, 'excerpts.md'), 'w', encoding='utf-8')
random.seed(7)


def P(*a):
    print(*a, file=out)


def paras(path):
    t = open(path, encoding='utf-8', errors='ignore').read()
    return [p.strip() for p in t.split('\n') if 25 <= len(p.split()) <= 140]


CATS = {
    'Opening paragraphs (how the issue is framed at the outset)': None,
    'Concluding / dispositive paragraphs': r'^(For (these|those) reasons|In the result|It follows that the appeal|The appeal (should|must) be|I would (allow|dismiss|order)|The (application|appeal) (should|must|is to) be)',
    'Rejecting a submission': r'(should be rejected|cannot be accepted|must be rejected|is misconceived|does not assist|is not to the point|is beside the point|no substance|without merit|I do not accept|cannot accept)',
    'Accepting a submission / finding for a party': r'(should be accepted|I accept the submission|is correct\.|was correct to|That submission (is|should be) accepted|there is force in|has force)',
    'Stating principle crisply': r'^(It is (well )?(established|settled|accepted)|The principles? (is|are) (not in doubt|well established|settled|clear)|The (starting point|relevant principles?)|There is no dispute|It is not in dispute|It was not (disputed|in dispute))',
    'Calibrated / hedged reasoning': r'(It may be (accepted|that)|It is at least arguable|arguably|it is unnecessary to (decide|resolve|determine)|need not be (decided|resolved|determined)|I am not persuaded|on balance|It is not necessary to)',
    'Explaining with "That is because" / "The reason is"': r'^(That is because|The reason (is|for that)|This is because|That is so because|The short (point|answer))',
    'Signposting and structure': r'^(It is convenient|Before turning|I turn|It is necessary (first|next|to)|Three|Two|Four|Several|A number of|Two (things|points|matters)|First,|Secondly,|Second,|Thirdly,|Third,|Finally,)',
    'Short punchy sentences in sequence (paragraph with 3+ sentences under 12 words)': 'SHORT',
    'Rhetorical question used to frame': r'\?',
    'Disagreeing with a lower court or another judge courteously': r'(with respect|respectfully|erred in|was in error|fell into error|I am unable to agree|I respectfully disagree|regrettably)',
}


def short_run(p):
    ss = re.split(r'(?<=[.?!])\s+(?=[A-Z])', p)
    return sum(1 for s in ss if len(s.split()) < 12) >= 3 and len(ss) >= 3


for court in ['HCA', 'QCA', 'QSC', 'NSWCA', 'VSCA']:
    files = sorted(glob.glob(os.path.join(base, 'clean', court + '_*.txt')), reverse=True)
    if not files:
        continue
    P(f'\n\n# {court}\n')
    for cat, pat in CATS.items():
        hits = []
        for f in files:
            name = os.path.basename(f)[:-4].replace('_', ' ')
            head = open(f, encoding='utf-8', errors='ignore').read(200)
            raw = os.path.join(base, 'nsw', os.path.basename(f))    # NSW raw file keeps the CITATION header
            if court == 'NSWCA' and os.path.exists(raw):
                head = open(raw, encoding='utf-8', errors='ignore').read(200)
            m = re.search(r'CITATION:\s*\[(20\d\d)\]\s*(NSWCA|VSCA)\s*(\d+)', head)
            if m:
                name = f'{m.group(2)} {m.group(1)} {m.group(3)}'
            elif court == 'VSCA':
                vm = re.search(r'VSCA_(20\d\d)_(\d+)', os.path.basename(f))
                if vm:
                    name = f'VSCA {vm.group(1)} {vm.group(2)}'
            ps = paras(f)
            if pat is None:
                hits += [(name, p) for p in ps[:2]]
            elif pat == 'SHORT':
                hits += [(name, p) for p in ps if short_run(p)]
            else:
                hits += [(name, p) for p in ps if re.search(pat, p)]
        random.shuffle(hits)
        P(f'\n## {cat}  ({len(hits)} candidates)\n')
        for name, p in hits[:14]:
            P(f'**[{name}]** {p}\n')
out.close()
print('ok')
