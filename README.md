# kaneki-skills

Private Claude Code plugin marketplace for Kaneki Law and Cozee.

## Install (each teammate, once)

In Claude Code:

```bash
claude plugin marketplace add Jaydenleijen/kaneki-skills
claude plugin install judicial-voice@kaneki-skills
```

Then restart Claude Code (or run `/plugin` and confirm it is enabled). The skill loads automatically; it triggers on things like "draft advice on this", "write to the client", "make this clearer", or "judicial voice".

Because this is a private repo, each teammate needs read access to it on GitHub and must be signed in to `gh` (or have a GitHub token configured for Claude Code) so the marketplace can be fetched.

## Update (to get new versions)

```bash
claude plugin update judicial-voice
```

## Plugins

### judicial-voice

Draft or rewrite **client correspondence and advice** (letters, emails, advice memos, file notes) so they read with the clarity, measured tone and disciplined vocabulary of senior Australian judges. It borrows how the current High Court and the Queensland, New South Wales and Victorian appeal and supreme courts write, not what they write. It is **not** for writing judgments.

Built from a corpus of 1,504 judgments (2024-26). See the skill's own `references/` for the phrasebank, statistics, judge profiles, and exemplars, and `scripts/` for how the corpus was harvested (New South Wales and Victoria via Firecrawl).

## Maintaining

This repo is the source of truth. Edit the skill in place at `plugins/judicial-voice/skills/judicial-voice/` (SKILL.md, references/, scripts/). To publish a change: bump `version` in both `plugins/judicial-voice/.claude-plugin/plugin.json` and the skill's `SKILL.md` frontmatter, commit and push. Teammates (and the author) pick it up with `claude plugin update judicial-voice`. The author consumes the skill the same way everyone does, through the installed plugin, so there is no separate personal copy to keep in sync.
