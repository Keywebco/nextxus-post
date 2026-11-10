#!/usr/bin/env python3
"""Next-Xus social poster. Default mode is dry-run. No Facebook call unless mode=post
and a Roger-approved limits file is present. Never loops on a dead token."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
# Pin and re-check against Meta's Page Feed docs before any live post.
# Official examples on 2026-11-10 used v27.0.
GRAPH_API_VERSION = "v27.0"


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
    end = limits.get("end_date") or ""
    try:
        end_d = date.fromisoformat(str(end))
    except ValueError:
        return "limits.end_date is missing or not YYYY-MM-DD"
    if today > end_d:
        return f"limits.end_date {end} has passed"
    if int(limits.get("posts_per_day") or 0) < 1:
        return "limits.posts_per_day is not a positive number"
    if not (limits.get("page_name") or limits.get("page_id")):
        return "limits file has no page_name or page_id"
    return None


def token_looks_present() -> bool:
    return bool(os.environ.get("FACEBOOK_PAGE_TOKEN", "").strip())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="dry-run", choices=["dry-run", "post"])
    parser.add_argument("--limits", default=str(ROOT / "data" / "limits.yaml"))
    parser.add_argument("--check-links", action="store_true")
    args = parser.parse_args()

    print(f"graph_api_version={GRAPH_API_VERSION} (re-check before live use)")
    print(f"requested_mode={args.mode}")

    if args.check_links:
        from link_check import main as check
        check()

    limits_path = Path(args.limits)
    if args.mode == "dry-run":
        if limits_path.is_file() and yaml is not None:
            limits = load_limits(limits_path)
            reason = limits_allow_post(limits, date.today())
            print(f"limits_file={limits_path} live_post_allowed={reason is None} reason={reason or 'n/a'}")
        else:
            print(f"limits_file={limits_path} present={limits_path.is_file()} (example only is expected in stage 1)")
        print("DRY RUN: no Facebook call, no post, no token use.")
        return 0

    # mode=post
    limits = load_limits(limits_path)
    reason = limits_allow_post(limits, date.today())
    if reason:
        print(f"REFUSED: {reason}. Nothing posted.")
        return 1
    if not token_looks_present():
        print("REFUSED: FACEBOOK_PAGE_TOKEN is missing. Dead or absent token — stop, do not retry.")
        return 2
    # A live debug_token check belongs here in a later stage. Stage 1 must not call Facebook.
    print("REFUSED: live Facebook posting is not enabled in this stage-1 copy.")
    return 3


if __name__ == "__main__":
    sys.exit(main())
