# Corpus scripts

These build and measure the corpus behind the judicial-voice profile. Rerun them to refresh or extend it.

## Harvesters

- `harvest_hca.py <base>`: High Court judgments. Reads the court's "Judgments 1998-current" listing (Drupal, `?page=N`), follows each judgment page to its PDF, converts with `pdftotext -layout`. No Firecrawl needed; the High Court site is server-rendered.
- `harvest_qld.py <base>`: Queensland Supreme Court and Court of Appeal, from queenslandjudgments.com.au. Predictable URLs `/caselaw/{qsc|qca}/{year}/{n}`; walks until eight consecutive misses. Plain HTTP.
- `harvest_nsw.py <base> page <year> [<year> ...]`: NSW Court of Appeal, from NSW Caselaw. Uses the server-rendered search (`/search?query=appeal&courts=<COA-id>&years=<year>&page=N`) to list decisions, then fetches each `/decision/<id>` page. Plain HTTP; only the browse landing page is JavaScript, the search and decision pages are not.
- `harvest_vsca.sh`: Victorian Court of Appeal, from AustLII. **Requires Firecrawl** because AustLII blocks scripted HTTP (Cloudflare). Drives the authenticated Firecrawl CLI (`firecrawl scrape <url> --format markdown --only-main-content`) one judgment at a time, capturing stdout, paced under the free-tier ~10 requests/minute cap. The CLI holds the API key; the script never handles it. Edit the id list at the top of the run, or point it at `vsca_ids.txt` (built by mapping `austlii.edu.au/.../VSCA/2026/` with `firecrawl scrape ... --format links`).

## Firecrawl

Firecrawl is the official Claude Code plugin plus the `firecrawl-cli` (installed globally). Authenticate once with `firecrawl login --browser` or `firecrawl login --api-key fc-...`, then `firecrawl --status` shows credits. The free tier is rate-limited to about ten requests a minute, which is why the Victorian harvest is paced and resumable. Scraping the full 2026 VSCA set costs roughly one credit per judgment.

To extend to other AustLII courts (e.g. Federal Court `au/cases/cth/FCA`, WA `au/cases/wa/WASCA`, SA, Tasmania), copy `harvest_vsca.sh`, change the court path, and build the id list with a `firecrawl scrape --format links` on the year listing.

## Analysis

- `analyse.py <base>`: cleans every court's judgments (court-specific cleaners strip catchwords, footnotes, headers, site chrome), then writes `stats.md`: sentence-length and paragraph distributions, punctuation and first-person rates, and per-10,000-word frequencies for the stance/connective/legalese/AI-ism term banks, per court, plus a High Court per-author table. Also writes cleaned text to `clean/`.
- `excerpts.py <base>`: pulls candidate exemplar paragraphs from `clean/`, grouped by rhetorical move (opening, rejecting, accepting, conceding, disposing, short-sentence runs, courteous disagreement), for hand-curation into `references/exemplars.md`.

`base` is the scratch directory holding `hca/txt/`, `qld/`, `nsw/`, and `fc/vsca_md/`. `last-run-stats.md` is the `stats.md` from the build in this repo.
