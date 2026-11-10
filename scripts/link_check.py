#!/usr/bin/env python3
"""Stage-1 dry-run link check and content list. No Facebook calls. No posting."""
from __future__ import annotations

import csv
import json
import re
import ssl
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
UA = "Next-Xus-social-poster-dryrun/0.1 (+https://next-xus.net/)"
TIMEOUT = 15
ALLOWED_HOSTS = re.compile(r"^(www\.)?next-xus\.(net|org|info|com)$", re.I)

FEED_URLS = {
    "blog": "https://raw.githubusercontent.com/Keywebco/nextxus-blog/HEAD/feed.xml",
    "archives": "https://raw.githubusercontent.com/Keywebco/nextxus-archives/HEAD/feed.xml",
    "music": "https://raw.githubusercontent.com/Keywebco/nextxus-music/HEAD/feed.xml",
}

# Live hub pages named in the stage-1 brief, plus the priority pages needed for Pontus's order.
HUB_PAGES = [
    {"id": "hub-tools", "title": "NextXus Tools — Federation Tools Directory", "url": "https://next-xus.net/nextxus-tools/", "source": "hub", "topic": "tools"},
    {"id": "hub-music", "title": "NextXus Music — Voices AI Songs", "url": "https://next-xus.net/nextxus-music/", "source": "hub", "topic": "music"},
    {"id": "hub-research", "title": "NextXus Research & API Hub", "url": "https://next-xus.net/nextxus-research-hub/", "source": "hub", "topic": "structure"},
    {"id": "hub-blog", "title": "NextXus Blog — Federation News & Updates", "url": "https://next-xus.net/nextxus-blog/", "source": "hub", "topic": "structure"},
    {"id": "live-roger-sim", "title": "Roger Sim — An Architect's Mind", "url": "https://next-xus.net/nextxus-sim/roger-sim.html", "source": "live-page", "topic": "sim"},
    {"id": "live-sim-hub", "title": "NextXus SIM — The Shared Mind", "url": "https://next-xus.net/nextxus-sim/", "source": "live-page", "topic": "sim"},
    {"id": "live-agency-kit", "title": "Real Agency Kit — the Votel jobs, for $0, as files you own", "url": "https://next-xus.net/nextxus-tools/real-agency-kit.html", "source": "live-page", "topic": "kit"},
    {"id": "live-ring-12", "title": "The Ring of 12 — Foundational Pillars of the HumanCodex", "url": "https://next-xus.net/ring-of-12/", "source": "live-page", "topic": "ring"},
    {"id": "live-ring-6", "title": "Ring of 6 — NextXus HumanCodex Federation", "url": "https://next-xus.net/ring-of-12/ring-of-6.html", "source": "live-page", "topic": "ring"},
    {"id": "live-podcast-feed", "title": "Ring of 12 podcast feed", "url": "https://next-xus.net/nextxus-music/podcast.xml", "source": "live-page", "topic": "music"},
]

TOPIC_ORDER = {"sim": 1, "kit": 2, "music": 3, "ring": 4, "tools": 4, "structure": 5, "other": 6}


def fetch(url: str, binary: bool = False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    # Do not silently follow http downgrades: we open each candidate URL ourselves.
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as resp:
        data = resp.read()
        final = resp.geturl()
        status = resp.status
        ctype = resp.headers.get("Content-Type", "")
    if final.lower().startswith("http://"):
        raise RuntimeError(f"redirected to insecure URL: {final}")
    return status, final, ctype, (data if binary else data.decode("utf-8", "replace"))


def head_or_get(url: str):
    try:
        status, final, ctype, body = fetch(url)
        return status, final, ctype, body, None
    except urllib.error.HTTPError as e:
        return e.code, url, "", "", str(e)
    except Exception as e:
        return 0, url, "", "", type(e).__name__ + ": " + str(e)


def repair(url: str) -> tuple[str, str]:
    """Return (candidate_url, repair_kind). kind is 'unchanged', 'repaired', or 'cannot-repair'."""
    url = (url or "").strip()
    p = urlparse(url)
    host = (p.hostname or "").lower()
    path = p.path or "/"

    if p.scheme == "http" and ALLOWED_HOSTS.match(host):
        return f"https://{host}{path}" + (f"?{p.query}" if p.query else ""), "repaired"
    if p.scheme == "https" and ALLOWED_HOSTS.match(host):
        return url, "unchanged"

    if host in {"keywebco.github.io", "www.keywebco.github.io"}:
        # Press articles live at https://next-xus.info/press/<file>
        m = re.match(r"^/nextxus-free-satellites/press/([^/]+)$", path)
        if m:
            return f"https://next-xus.info/press/{m.group(1)}", "repaired"
        if path in {"", "/"}:
            return "https://next-xus.net/", "repaired"
        return f"https://next-xus.net{path}" + (f"?{p.query}" if p.query else ""), "repaired"

    return url, "cannot-repair"


def parse_feed(name: str, xml_text: str) -> list[dict]:
    items = []
    root = ET.fromstring(xml_text)
    channel = root.find("channel")
    if channel is None:
        return items
    for i, item in enumerate(channel.findall("item"), 1):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = (item.findtext("description") or "").strip()
        guid = (item.findtext("guid") or "").strip()
        topic = guess_topic(name, title, link)
        items.append({
            "id": f"feed-{name}-{i}",
            "title": title,
            "url": link,
            "description": desc,
            "guid": guid,
            "source": f"feed:{name}",
            "topic": topic,
        })
    return items


def guess_topic(feed: str, title: str, url: str) -> str:
    blob = f"{title} {url}".lower()
    if feed == "music":
        return "music"
    if "roger-sim" in blob or re.search(r"\broger sim\b", blob):
        return "sim"
    if "agency kit" in blob or "votel" in blob:
        return "kit"
    if "ring of" in blob or "ring-of-12" in blob:
        return "ring"
    if "nextxus-tools" in blob or re.search(r"\btools?\b", blob):
        return "tools"
    if feed == "archives":
        return "structure"
    if feed == "blog":
        return "structure"
    return "other"


class MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self._in_title = False
        self.meta = {}

    def handle_starttag(self, tag, attrs):
        d = {k.lower(): v for k, v in attrs}
        if tag == "title":
            self._in_title = True
        if tag == "meta":
            key = (d.get("property") or d.get("name") or "").lower()
            if key and "content" in d:
                self.meta[key] = d["content"]

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def page_meta(html: str) -> dict:
    p = MetaParser()
    try:
        p.feed(html)
    except Exception:
        pass
    title = (p.title or p.meta.get("og:title") or "").strip()
    desc = (p.meta.get("og:description") or p.meta.get("description") or "").strip()
    image = (p.meta.get("og:image") or p.meta.get("twitter:image") or "").strip()
    return {"live_title": title, "live_description": desc, "og_image": image}


def title_fits(original: str, live: str) -> bool:
    if not original:
        return True
    if not live:
        return False
    a = re.sub(r"\W+", " ", original).strip().lower()
    b = re.sub(r"\W+", " ", live).strip().lower()
    if a in b or b in a:
        return True
    aw, bw = set(a.split()), set(b.split())
    if not aw:
        return True
    return len(aw & bw) / len(aw) >= 0.5


def main() -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    items: list[dict] = []
    for name, url in FEED_URLS.items():
        status, final, ctype, body, err = head_or_get(url)
        if status != 200 or err:
            print(f"FAILED to load feed {name}: {status} {err}", file=sys.stderr)
            continue
        items.extend(parse_feed(name, body))
    items.extend(HUB_PAGES)

    results = []
    counts = {"ok": 0, "repaired": 0, "skipped": 0}
    for item in items:
        rec = dict(item)
        original = item["url"]
        candidate, kind = repair(original)
        rec["original_url"] = original
        rec["repaired_url"] = candidate if kind != "cannot-repair" else ""
        rec["repair_kind"] = kind

        if kind == "cannot-repair":
            rec["status"] = "skipped"
            rec["skip_reason"] = f"not a next-xus.* URL and no known mapping: {original}"
            counts["skipped"] += 1
            results.append(rec)
            continue

        # Must be https next-xus.*
        host = (urlparse(candidate).hostname or "")
        if urlparse(candidate).scheme != "https" or not ALLOWED_HOSTS.match(host):
            rec["status"] = "skipped"
            rec["skip_reason"] = f"repaired URL is not https next-xus.*: {candidate}"
            counts["skipped"] += 1
            results.append(rec)
            continue

        status, final, ctype, body, err = head_or_get(candidate)
        rec["http_status"] = status
        rec["final_url"] = final
        rec["content_type"] = ctype
        if status != 200 or err:
            rec["status"] = "skipped"
            rec["skip_reason"] = f"repaired URL did not return 200: status={status} error={err}"
            counts["skipped"] += 1
            results.append(rec)
            continue
        if not final.lower().startswith("https://"):
            rec["status"] = "skipped"
            rec["skip_reason"] = f"final URL was not https: {final}"
            counts["skipped"] += 1
            results.append(rec)
            continue

        if "html" in (ctype or "").lower() or candidate.endswith((".html", "/")):
            meta = page_meta(body)
            rec.update(meta)
            if item.get("title") and meta["live_title"] and not title_fits(item["title"], meta["live_title"]):
                rec["status"] = "skipped"
                rec["skip_reason"] = f"live title does not still fit feed title: live={meta['live_title']!r}"
                counts["skipped"] += 1
                results.append(rec)
                continue
        else:
            rec["live_title"] = item.get("title", "")
            rec["live_description"] = item.get("description", "")
            rec["og_image"] = ""

        rec["status"] = "repaired" if kind == "repaired" else "ok"
        rec["checked_url"] = candidate
        counts[rec["status"]] += 1
        rec["topic_rank"] = TOPIC_ORDER.get(rec.get("topic") or "other", 6)
        results.append(rec)

    # sort accepted first by topic rank then title
    results.sort(key=lambda r: (0 if r["status"] in {"ok", "repaired"} else 1, TOPIC_ORDER.get(r.get("topic") or "other", 6), r.get("title") or ""))

    (DATA / "link-check.json").write_text(json.dumps({"counts": counts, "items": results}, indent=2), encoding="utf-8")
    fields = ["id", "status", "topic", "source", "title", "original_url", "repaired_url", "http_status", "skip_reason", "live_title", "og_image"]
    with (DATA / "link-check.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in results:
            w.writerow(r)

    accepted = [r for r in results if r["status"] in {"ok", "repaired"}]
    print(f"OK={counts['ok']} repaired={counts['repaired']} skipped={counts['skipped']} total={len(results)} accepted={len(accepted)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
