# Stage 1 dry run — 2026-11-10, America/Chicago

Approved scope: local dry run only. No token, no Facebook calls, no posts, no merges, no pushes, no Drive writes.

## Link-check summary (FACT, from this run)

- Source: `nextxus-blog`, `nextxus-archives`, and `nextxus-music` feeds, plus the four named hub pages, plus the live Roger Sim, Real Agency Kit, Ring of 12 / Ring of 6, and podcast-feed pages needed for Pontus's order.
- Totals: **55** items checked. **OK 10**, **repaired 10**, **skipped 35**. **20** accepted.

Repair rules that worked (quiet, no change note on the destination site):
- `https://keywebco.github.io/nextxus-free-satellites/press/<file>` → `https://next-xus.info/press/<file>` (https 200; the `next-xus.net/.../press/` path 301s to **http**, which fails).
- Other `https://keywebco.github.io/<path>` → `https://next-xus.net/<path>` when that https URL returns 200 and the live title still fits.

Skipped, with reasons:
- 16 music-feed songs on `getvoices.ai` (not a next-xus.* host; no per-song Next-Xus page). The catalog itself is accepted at https://next-xus.net/nextxus-music/.
- 9 Blogspot articles and 1 Gumroad link (no Next-Xus mapping).
- 9 archive or portal milestones whose feed title no longer fits the live homepage title (for example “Roger Sim AI goes live with 13 topics” now lands on a page titled “Roger Sim — An Architect's Mind”; “Thirteen new Federation sites launched” lands on “NextXus Archives — Federation History”). The current Sim, Tools, Blog, and related pages were still accepted as hub or live pages.

None of the 20 accepted pages had an `og:image`. Custom previews need a real existing square image at least 458×458. Usable files (measured): six `deepai-gallery` JPEGs at 640×640, and `https://next-xus.net/nextxus-music/episodes/episode-cover.jpg` at 1600×1600. Not usable for a custom preview: `roger-sim-face.jpg` (1070×1034, not 1:1), both mascots (not 1:1), `ring-of-6-poster.jpg` (202×200, too small).

## Files (all local)

- `/workspace/ops/social-poster/scripts/link_check.py`
- `/workspace/ops/social-poster/scripts/poster.py` (dry-run default; refuses to post in this stage)
- `/workspace/ops/social-poster/.github/workflows/social-poster.yml` (draft only, not pushed)
- `/workspace/ops/social-poster/data/link-check.json`
- `/workspace/ops/social-poster/data/link-check.csv`
- `/workspace/ops/social-poster/data/images.json`
- `/workspace/ops/social-poster/data/limits.example.yaml`
- `/workspace/ops/social-poster/data/ledger.example.jsonl`
- `/workspace/ops/social-poster/data/ledger.csv`
- `/workspace/ops/social-poster/data/RECORD-FORMAT.md`
- `/workspace/ops/social-poster/drafts/sample-posts-key-to-the-web.md`
- `/workspace/ops/social-poster/REPORT.md`

Graph API version pinned in the draft script: **v27.0** (from Meta's Page Feed examples on 2026-11-10). Re-check before any live post.
