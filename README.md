# Next-Xus posting system — dry-run code, plus Stage 2 test post (2026-11-10/11)

This is the Stage 1 dry-run package for the Next-Xus Facebook posting system, starting with the Page Key To The Web, plus the Stage 2 test-post stage (one post, manual only, see below).

The daily workflow is still dry-run by default. There is no token value in these files. Nothing posts unless the test-post workflow is run by hand with confirm=yes and the approved limits file in `data/limits.yaml` is in force.

## Stage 2 — one test post (manual only)
- Workflow `.github/workflows/test-post.yml`: manual dispatch only, no schedule, no push trigger. Run once from the Actions tab with confirm=yes.
- Post: Day 1 post 1, Roger Sim — `data/test-post.json`. Photo post (the Roger Sim page has no og tags, so a plain link post would scrape with no image; the 640×640 image from the sample post is attached and the link is in the caption). Link: https://next-xus.net/nextxus-sim/roger-sim.html (verified 200).
- Limits: `data/limits.yaml` — one post, one Page, one day only (2026-11-11). After that date it expires by itself. Daily posting is NOT enabled.
- Safety: `poster.py` refuses post mode without `--test-post` (the daily workflow never passes it), checks the limits Page against the test-post Page, checks the token's own Page at run time and refuses if it does not match, refuses if the test was already recorded as sent, and never retries. A failed run stops and is reported to Roger.

## PAGE CONFLICT — resolve before merging the test-post PR
- README / limits.example / dry-run samples say the Page is **Key To The Web, 105137908362972**.
- The main-chat record says the saved `FACEBOOK_PAGE_TOKEN` is for **Keys To Success, 270012706198023**.
- The test-post files default to Key To The Web (the system as designed). If Roger confirms Keys To Success, change `page_name`, `page_id` and `allow_pages` in `data/limits.yaml` and `data/test-post.json` to Keys To Success / 270012706198023 before merging. Do not merge with the conflict unresolved.

## Holds (do not post these until the named work is done)
- Podcast episode: hold lifted — the normal episode page now exists (nextxus-music PR #12, live 200). But Day 2 post 2 in the samples still links the raw `podcast.xml` file; swap its link to the episode page before that post is ever used.
- Real Agency Kit: hold lifted — the page opening is fixed (nextxus-tools PR #14, live 200).

Follow-up, not blocking this test: add og:title / og:description / og:image to the Roger Sim page so future link posts scrape a proper preview instead of needing a photo post.

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
