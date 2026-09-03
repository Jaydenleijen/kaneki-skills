#!/usr/bin/env bash
# Harvest 2026 VSCA judgments by driving the authenticated Firecrawl CLI and capturing stdout.
# The CLI holds the API key; this script never handles it. Paced for the free-tier 10/min cap.
S="/c/Users/JAYDEN~1/AppData/Local/Temp/claude/C--Users-JaydenLeijen-Documents-CLAUDE-ACCESS/5c852ba2-9302-4efe-a5fa-366e965e450f/scratchpad/fc"
cd "$S" || exit 1
mkdir -p vsca_md
err=$(mktemp)
got=0
for n in $(cat vsca_ids.txt); do
  tgt="vsca_md/VSCA_2026_${n}.md"
  if [ -s "$tgt" ] && [ "$(wc -c < "$tgt")" -gt 500 ]; then continue; fi
  saved=0
  for try in 1 2 3 4 5; do
    out=$(firecrawl scrape "https://www.austlii.edu.au/cgi-bin/viewdoc/au/cases/vic/VSCA/2026/${n}.html" --format markdown --only-main-content 2>"$err")
    out=$(printf '%s' "$out" | sed 's/\x1b\[[0-9;]*m//g')
    if [ "${#out}" -gt 500 ]; then printf '%s' "$out" > "$tgt"; got=$((got+1)); saved=1; break; fi
    if grep -qi "rate limit" "$err"; then sleep 32; else sleep 6; fi
  done
  [ "$saved" = 0 ] && echo "MISS $n"
  if [ $((got % 10)) -eq 0 ] && [ "$got" -gt 0 ]; then echo "progress got=$got total=$(ls vsca_md | wc -l)"; fi
  sleep 7
done
rm -f "$err"
echo "VSCA_CLI_DONE got=$got total=$(ls vsca_md | wc -l)"
