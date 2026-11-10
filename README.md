# Next-Xus posting system — dry-run code (2026-11-10)

This is the Stage 1 dry-run package for the Next-Xus Facebook posting system, starting with the Page Key To The Web.

It is a local dry-run only. The default mode is dry-run. There is no token in these files. Nothing here posts to Facebook, and nothing has been pushed to GitHub by Grok.

## Holds (do not post these until the named work is done)
- Podcast episode: hold until a normal episode page exists. Do not link to the raw `podcast.xml` feed file.
- Real Agency Kit: hold until the page opening “The Votel jobs” is fixed on the page itself.

## Intended GitHub repo
These files are meant to be pushed **branch-first** to `Keywebco/nextxus-post` once Pontus has created that repo. Do not push to `main` first. No token and no posting in that first push.

## Intended repo paths

| File in this Drive folder | Intended path in Keywebco/nextxus-post |
|---|---|
| README.md | README.md |
| REPORT.md | REPORT.md |
| scripts/link_check.py | scripts/link_check.py |
| scripts/poster.py | scripts/poster.py |
| data/RECORD-FORMAT.md | data/RECORD-FORMAT.md |
| data/images.json | data/images.json |
| data/ledger.csv | data/ledger.csv |
| data/ledger.example.jsonl | data/ledger.example.jsonl |
| data/limits.example.yaml | data/limits.example.yaml |
| data/link-check.csv | data/link-check.csv |
| data/link-check.json | data/link-check.json |
| drafts/sample-posts-key-to-the-web.md | drafts/sample-posts-key-to-the-web.md |
| github-workflows/social-poster.yml | .github/workflows/social-poster.yml |

The workflow file is stored here as `github-workflows/social-poster.yml` so the folder name does not start with a dot. On GitHub it belongs at `.github/workflows/social-poster.yml`.

The workflow references the secret name `FACEBOOK_PAGE_TOKEN` only as a GitHub Actions placeholder. No token value is included.

Graph API version in the draft is v27.0; re-check before any live use.

Approval: Drive upload approved by Roger via Pontus on 2026-11-10. The GitHub push is Pontus's step, branch-first. No posting is approved.
