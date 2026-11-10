# Append-only post record

Use `ledger.jsonl` as the live record (one JSON object per line). `ledger.csv` is a mirror of the same fields for easy reading.

Rules:
- Only append. Never edit or delete a line.
- A correction is a new line whose `corrects` field holds the earlier `id`.
- `result` is one of: dry-run, queued, sent, failed, skipped, corrected.
- A post is only `sent` when `facebook_permalink` is a real live URL, not merely a tool success.
- Monthly, copy the file to Echo64 / Echo Core. Do not delete the GitHub copy.

Required fields: id, ts_chicago, page, content_id, source_url, posted_url, title, message_sha256, image_url, graph_api_version, graph_post_id, facebook_permalink, approval, attempt, result, error, corrects.
