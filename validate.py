#!/usr/bin/env python3
"""Post-build validation gate for isaklab.com.

Runs against the generated public/ tree and exits non-zero if anything that
must hold for a correct, indexable site is broken. Wired into CI before the
deploy step, so a malformed feed, broken JSON-LD, or dangling internal link
fails the build instead of being published.

Usage:
    python validate.py            # validate ./public
    python validate.py some/dir   # validate another output directory
"""

from __future__ import annotations

import json
import re
import sys
import xml.dom.minidom as minidom
from pathlib import Path
from urllib.parse import urlsplit

SITE_URL = "https://isaklab.com"

errors: list[str] = []
checked = {"html": 0, "xml": 0, "jsonld": 0, "links": 0}


def fail(msg: str) -> None:
    errors.append(msg)


def check_xml(path: Path) -> None:
    if not path.is_file():
        return fail(f"missing file: {path.name}")
    try:
        minidom.parseString(path.read_text(encoding="utf-8"))
        checked["xml"] += 1
    except Exception as e:  # noqa: BLE001
        fail(f"malformed XML {path.name}: {e}")


def check_json(path: Path) -> None:
    if not path.is_file():
        return fail(f"missing file: {path.name}")
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        fail(f"invalid JSON {path.name}: {e}")


def validate(out: Path) -> None:
    if not out.is_dir():
        fail(f"output directory not found: {out}")
        return

    # 1. Required top-level files.
    required = [
        "index.html", "404.html", "sitemap.xml", "feed.xml", "robots.txt",
        "site.webmanifest", "sw.js", ".well-known/security.txt",
        "og-en.png", "icon-192.png", "icon-512.png", "highlight.css",
    ]
    for rel in required:
        if not (out / rel).is_file():
            fail(f"missing required file: {rel}")

    # 2. XML well-formedness.
    for xml in out.rglob("*.xml"):
        check_xml(xml)

    # 3. Manifest is valid JSON and its icons exist.
    check_json(out / "site.webmanifest")
    if (out / "site.webmanifest").is_file():
        man = json.loads((out / "site.webmanifest").read_text())
        for icon in man.get("icons", []):
            if not (out / icon["src"].lstrip("/")).is_file():
                fail(f"manifest references missing icon: {icon['src']}")

    # 4. security.txt has the RFC 9116 required fields.
    sec = out / ".well-known" / "security.txt"
    if sec.is_file():
        body = sec.read_text()
        for field in ("Contact:", "Expires:"):
            if field not in body:
                fail(f"security.txt missing required field: {field}")

    # 5. Per-page HTML checks + internal link graph.
    html_files = list(out.rglob("*.html"))

    def resolves(href: str) -> bool:
        path = urlsplit(href).path
        if not path:
            return True
        if not path.startswith("/"):
            return True  # relative/anchor — skip
        # Strip query/fragment already done. Try file, dir/index.html, and asset.
        candidates = [path.lstrip("/")]
        if path.endswith("/"):
            candidates.append((path + "index.html").lstrip("/"))
        else:
            candidates.append((path + "/index.html").lstrip("/"))
        return any((out / c).exists() for c in candidates)

    for p in html_files:
        t = p.read_text(encoding="utf-8")
        rel = p.relative_to(out)
        is_root_redirect = (p.name == "index.html" and p.parent == out)

        if not is_root_redirect:
            checked["html"] += 1
            for need in ('rel="canonical"', "og:image", "viewport"):
                if need not in t:
                    fail(f"{rel}: missing {need}")

        # JSON-LD must parse.
        for m in re.findall(r'application/ld\+json">(.*?)</script>', t, re.S):
            checked["jsonld"] += 1
            try:
                json.loads(m)
            except Exception as e:  # noqa: BLE001
                fail(f"{rel}: invalid JSON-LD: {e}")

        # Internal links (href/src) must resolve to a generated file.
        for href in re.findall(r'(?:href|src)="([^"]+)"', t):
            if href.startswith(SITE_URL):
                href = href[len(SITE_URL):] or "/"
            if href.startswith(("http://", "https://", "mailto:", "data:", "#", "tel:")):
                continue
            checked["links"] += 1
            if not resolves(href):
                fail(f"{rel}: dangling internal link -> {href}")


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("public")
    validate(out)
    if errors:
        print(f"validation FAILED ({len(errors)} issue(s)):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print(f"validation OK — html:{checked['html']} xml:{checked['xml']} "
          f"jsonld:{checked['jsonld']} links:{checked['links']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
