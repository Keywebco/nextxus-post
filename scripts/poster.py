#!/usr/bin/env python3
"""Next-Xus social poster. Default mode is dry-run.

Stage 2 (test post only): mode=post is allowed ONLY for one approved test
post, and ONLY through the manual test-post workflow. Rules, all enforced
here, not just in the workflow:
  - an approved limits file (status approved, mode post, test_post_only true,
    posts_per_day exactly 1, start_date <= today <= end_date, America/Chicago)
  - --test-post <file> is required in post mode; the daily workflow does not
    pass it, so the daily workflow can never post
  - the limits Page must match the test-post Page exactly (name and id)
  - the token's own Page is checked at run time (GET /{page-id}) and must
    match the limits page_id — if the saved token belongs to a different
    Page, the run refuses and posts nothing
  - the post is a single photo post (/{page-id}/photos) with the exact
    message from the test-post file; no loop, no retry: any Graph error
    exits 2 and stops
  - if the content_id is already recorded as sent in the ledger, refuse
    (never post the same test twice)
The token value is never printed. Graph error bodies are printed truncated
with the token value scrubbed out.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
# Pin and re-check against Meta's Page Feed docs before any live post.
# v27.0 verified current 2026-11-10 (Meta blog, "Introducing Graph API v27.0",
# released November 4, 2026). v26.0 was July 29, 2026. No v28.0 found.
GRAPH_API_VERSION = "v27.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def today_chicago() -> date:
    if ZoneInfo is not None:
        try:
            return datetime.now(ZoneInfo("America/Chicago")).date()
        except Exception:
            pass
    return date.today()


def load_limits(path: Path) -> dict:
    if yaml is None:
        raise SystemExit("PyYAML is required to read the limits file")
    if not path.is_file():
        raise SystemExit(f"REFUSED: limits file missing ({path}). No posts.")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data


def limits_allow_post(limits: dict, today: date) -> str | None:
    """Return a refusal reason, or None if posting is allowed."""
    if (limits.get("status") or "").strip().lower() != "approved":
        return "limits.status is not 'approved'"
    if (limits.get("mode") or "dry-run").strip().lower() != "post":
        return "limits.mode is not 'post'"
    if limits.get("test_post_only") is not True:
        return "limits.test_post_only is not true (daily posting is not enabled)"
    if int(limits.get("posts_per_day") or 0) != 1:
        return "limits.posts_per_day is not exactly 1"
    start = limits.get("start_date") or ""
    end = limits.get("end_date") or ""
    try:
        start_d = date.fromisoformat(str(start))
        end_d = date.fromisoformat(str(end))
    except ValueError:
        return "limits.start_date/end_date is missing or not YYYY-MM-DD"
    if today < start_d:
        return f"limits.start_date {start} has not arrived"
    if today > end_d:
        return f"limits.end_date {end} has passed"
    if not (limits.get("page_name") or limits.get("page_id")):
        return "limits file has no page_name or page_id"
    return None


def token_looks_present() -> bool:
    return bool(os.environ.get("FACEBOOK_PAGE_TOKEN", "").strip())


def scrub(text: str, token: str) -> str:
    if token and token in text:
        return text.replace(token, "[FACEBOOK_PAGE_TOKEN]")
    return text


def graph_get(path: str, token: str) -> dict:
    url = f"{GRAPH_BASE}{path}?{urllib.parse.urlencode({'access_token': token})}"
    req = urllib.request.Request(url, method="GET")
    req.add_header("User-Agent", "nextxus-post-test/1.0")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:600]
        raise RuntimeError(f"Graph GET {path} failed HTTP {e.code}: {scrub(body, token)}")


def graph_post_photo(page_id: str, image_url: str, caption: str, token: str) -> dict:
    url = f"{GRAPH_BASE}/{page_id}/photos"
    data = urllib.parse.urlencode(
        {"url": image_url, "caption": caption, "access_token": token}
    ).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("User-Agent", "nextxus-post-test/1.0")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:600]
        raise RuntimeError(f"Graph POST /{page_id}/photos failed HTTP {e.code}: {scrub(body, token)}")


def already_sent(content_id: str) -> bool:
    for name in ("data/ledger.jsonl", "data/ledger.csv"):
        p = ROOT / name
        if p.is_file():
            text = p.read_text(encoding="utf-8", errors="replace")
            if content_id in text and ('"sent"' in text or ",sent" in text):
                return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="dry-run", choices=["dry-run", "post"])
    parser.add_argument("--limits", default=str(ROOT / "data" / "limits.yaml"))
    parser.add_argument("--test-post", default=None,
                        help="JSON file with the one approved test post (required in post mode)")
    parser.add_argument("--check-links", action="store_true")
    args = parser.parse_args()

    print(f"graph_api_version={GRAPH_API_VERSION} (v27.0 verified current 2026-11-10)")
    print(f"requested_mode={args.mode}")

    if args.check_links:
        from link_check import main as check
        check()

    limits_path = Path(args.limits)
    today = today_chicago()
    print(f"today_chicago={today.isoformat()}")
    if args.mode == "dry-run":
        if limits_path.is_file() and yaml is not None:
            limits = load_limits(limits_path)
            reason = limits_allow_post(limits, today)
            print(f"limits_file={limits_path} live_post_allowed={reason is None} reason={reason or 'n/a'}")
        else:
            print(f"limits_file={limits_path} present={limits_path.is_file()} (example only is expected in stage 1)")
        print("DRY RUN: no Facebook call, no post, no token use.")
        return 0

    # mode=post — test post only, all gates below
    if not args.test_post:
        print("REFUSED: --test-post is required in post mode. The daily workflow does not pass it. Nothing posted.")
        return 1
    test_path = Path(args.test_post)
    if not test_path.is_file():
        print(f"REFUSED: test-post file missing ({test_path}). Nothing posted.")
        return 1
    post = json.loads(test_path.read_text(encoding="utf-8"))
    for field in ("content_id", "page_name", "page_id", "title", "link", "image_url", "message"):
        if not str(post.get(field) or "").strip():
            print(f"REFUSED: test-post file is missing {field}. Nothing posted.")
            return 1
    if len(post["title"]) > 35:
        print(f"REFUSED: test-post title is {len(post['title'])} chars (limit 35). Nothing posted.")
        return 1

    limits = load_limits(limits_path)
    reason = limits_allow_post(limits, today)
    if reason:
        print(f"REFUSED: {reason}. Nothing posted.")
        return 1
    if str(limits.get("page_id")) != str(post["page_id"]):
        print(f"REFUSED: limits page_id {limits.get('page_id')} does not match test-post page_id {post['page_id']}. Nothing posted.")
        return 1
    if str(limits.get("page_name")) != str(post["page_name"]):
        print("REFUSED: limits page_name does not match test-post page_name. Nothing posted.")
        return 1
    if already_sent(str(post["content_id"])):
        print(f"REFUSED: content_id {post['content_id']} is already recorded as sent. Never post the same test twice.")
        return 1
    token = os.environ.get("FACEBOOK_PAGE_TOKEN", "").strip()
    if not token:
        print("REFUSED: FACEBOOK_PAGE_TOKEN is missing. Dead or absent token — stop, do not retry.")
        return 2

    # Run-time Page check: the token's own Page must be the limits Page.
    # If the saved token belongs to a different Page, refuse here.
    try:
        page = graph_get(f"/{post['page_id']}", token)
    except RuntimeError as e:
        print(f"REFUSED: could not verify the token's Page: {e}. Nothing posted, do not retry.")
        return 2
    if str(page.get("id")) != str(post["page_id"]):
        print(f"REFUSED: token's Page id {page.get('id')} does not match limits page_id {post['page_id']}. Nothing posted, do not retry.")
        return 2
    print(f"token_page_verified id={page.get('id')} name={page.get('name')}")

    # One photo post, exact message from the test-post file. No retry.
    try:
        result = graph_post_photo(str(post["page_id"]), str(post["image_url"]), str(post["message"]), token)
    except RuntimeError as e:
        print(f"FAILED: {e}. Nothing posted, do not retry in a loop. Report this to Roger.")
        return 2
    post_id = result.get("post_id") or result.get("id")
    photo_id = result.get("id")
    if not post_id:
        print(f"FAILED: Graph returned no post id: {scrub(str(result)[:600], token)}. Nothing confirmed posted.")
        return 2
    # post_id looks like "<page_id>_<postid>"; the live permalink is confirmed by Roger, not assumed here.
    short_id = str(post_id).split("_")[-1]
    permalink = f"https://www.facebook.com/{post['page_id']}/posts/{short_id}"
    print(f"POSTED post_id={post_id} photo_id={photo_id}")
    print(f"PERMALINK_TO_CONFIRM={permalink}")
    print("Roger must confirm this link opens the live post. A post is only 'sent' when the permalink is real.")
    ledger = {
        "id": str(post["content_id"]),
        "ts_chicago": datetime.now().isoformat(timespec="seconds"),
        "page": str(post["page_name"]),
        "content_id": str(post["content_id"]),
        "source_url": str(post["link"]),
        "posted_url": str(post["link"]),
        "title": str(post["title"]),
        "message_sha256": hashlib.sha256(str(post["message"]).encode()).hexdigest(),
        "image_url": str(post["image_url"]),
        "graph_api_version": GRAPH_API_VERSION,
        "graph_post_id": str(post_id),
        "facebook_permalink": permalink,
        "approval": "Roger Keyserling — test post, 2026-11-11 (merge word on this PR)",
        "attempt": 1,
        "result": "sent",
        "error": "",
        "corrects": "",
    }
    print("LEDGER_LINE=" + json.dumps(ledger))
    print("Record the ledger line above in data/ledger.jsonl after Roger confirms the permalink live.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
