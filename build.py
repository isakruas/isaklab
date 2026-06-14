#!/usr/bin/env python3
"""Static site generator for isaklab.com.

Reads Markdown from content/<lang>/, renders it through Jinja2 templates, and
writes a fully static, trilingual (pt/en/es) site to public/. No backend, no
database, no JavaScript framework.

Usage:
    python build.py            # build published content into public/
    python build.py --drafts   # include posts marked `draft: true`
    python build.py --serve    # build, then serve public/ on localhost:8000

Layout:
    content/<lang>/posts/<YYYY-MM-DD-slug>.md   one file per post
    content/<lang>/pages/<slug>.md              standalone pages (about, ...)

Front matter (minimal `key: value`; lists are comma-separated):

    ---
    title: A precise title
    date: 2026-06-13
    tags: rust, avr
    summary: One sentence shown in listings and meta description.
    draft: true            # optional
    ---
"""

from __future__ import annotations

import argparse
import datetime as dt
import email.utils
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pygments.formatters import HtmlFormatter

# --------------------------------------------------------------------------- #
# Configuration                                                               #
# --------------------------------------------------------------------------- #

SITE = {
    "title": "isaklab",
    "author": "Isak",
    "callsign": "PU3IAR",
    "url": "https://isaklab.com",          # no trailing slash
    # External, language-independent links shown in the footer.
    "social": [
        {"label": "github", "href": "https://github.com/isakruas"},
        {"label": "linkedin", "href": "https://www.linkedin.com/in/isakruas/"},
        {"label": "id-qsl", "href": "https://id.qsl.br/op/PU3IAR"},
    ],
}

LANGS = ["en", "pt", "es"]
DEFAULT_LANG = "en"

# Per-language UI strings.
I18N = {
    "pt": {
        "name": "Português",
        "tagline": "Notas sobre criptografia, rádio e sistemas embarcados.",
        "nav_posts": "posts",
        "nav_about": "sobre",
        "all_posts": "todos os posts",
        "search": "buscar",
        "no_results": "Nenhum post corresponde.",
        "no_posts": "Ainda não há posts.",
        "not_found": "Esta página não existe.",
        "return_home": "Voltar ao início.",
        "feed": "feed",
    },
    "en": {
        "name": "English",
        "tagline": "Notes on cryptography, radio, and embedded systems.",
        "nav_posts": "posts",
        "nav_about": "about",
        "all_posts": "all posts",
        "search": "search",
        "no_results": "No matching posts.",
        "no_posts": "No posts yet.",
        "not_found": "This page does not exist.",
        "return_home": "Return to the index.",
        "feed": "feed",
    },
    "es": {
        "name": "Español",
        "tagline": "Notas sobre criptografía, radio y sistemas embebidos.",
        "nav_posts": "posts",
        "nav_about": "acerca",
        "all_posts": "todas las entradas",
        "search": "buscar",
        "no_results": "Ninguna entrada coincide.",
        "no_posts": "Aún no hay entradas.",
        "not_found": "Esta página no existe.",
        "return_home": "Volver al inicio.",
        "feed": "feed",
    },
}

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
OUTPUT = ROOT / "public"

MD_EXTENSIONS = ["fenced_code", "codehilite", "tables", "toc", "attr_list", "sane_lists"]
MD_CONFIG = {"codehilite": {"css_class": "highlight", "guess_lang": False}}


# --------------------------------------------------------------------------- #
# Content model                                                              #
# --------------------------------------------------------------------------- #


@dataclass
class Document:
    lang: str
    slug: str
    meta: dict
    html: str
    source: Path

    @property
    def title(self) -> str:
        return self.meta.get("title", self.slug)

    @property
    def summary(self) -> str:
        return self.meta.get("summary", "")

    @property
    def url(self) -> str:
        return f"/{self.lang}/{self.slug}/"


@dataclass
class Post(Document):
    date: dt.date = dt.date(1970, 1, 1)
    tags: list[str] = field(default_factory=list)

    @property
    def url(self) -> str:
        return f"/{self.lang}/posts/{self.slug}/"

    @property
    def iso_date(self) -> str:
        return self.date.isoformat()

    @property
    def display_date(self) -> str:
        return self.date.strftime("%Y-%m-%d")


# --------------------------------------------------------------------------- #
# Front matter + Markdown                                                     #
# --------------------------------------------------------------------------- #

_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_front_matter(text: str) -> tuple[dict, str]:
    match = _FM_RE.match(text)
    if not match:
        return {}, text
    meta: dict = {}
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta, text[match.end():]


def render_markdown(body: str) -> str:
    md = markdown.Markdown(extensions=MD_EXTENSIONS, extension_configs=MD_CONFIG)
    return md.convert(body)


def slug_from_path(path: Path, meta: dict) -> str:
    if meta.get("slug"):
        return meta["slug"].strip()
    name = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.stem)
    return name


def load_posts(lang: str, include_drafts: bool) -> list[Post]:
    posts: list[Post] = []
    folder = CONTENT / lang / "posts"
    for path in sorted(folder.glob("*.md")):
        meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
        if str(meta.get("draft", "")).lower() == "true" and not include_drafts:
            continue
        date_raw = meta.get("date", "1970-01-01")
        try:
            date = dt.date.fromisoformat(date_raw)
        except ValueError:
            sys.exit(f"error: {path}: invalid date {date_raw!r} (use YYYY-MM-DD)")
        tags = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
        posts.append(
            Post(
                lang=lang,
                slug=slug_from_path(path, meta),
                meta=meta,
                html=render_markdown(body),
                source=path,
                date=date,
                tags=tags,
            )
        )
    posts.sort(key=lambda p: (p.date, p.slug), reverse=True)
    return posts


def load_pages(lang: str) -> list[Document]:
    pages: list[Document] = []
    folder = CONTENT / lang / "pages"
    for path in sorted(folder.glob("*.md")):
        meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
        pages.append(
            Document(
                lang=lang,
                slug=slug_from_path(path, meta),
                meta=meta,
                html=render_markdown(body),
                source=path,
            )
        )
    return pages


# --------------------------------------------------------------------------- #
# Rendering helpers                                                           #
# --------------------------------------------------------------------------- #


def make_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals["site"] = SITE
    return env


def nav_for(lang: str) -> list[dict]:
    t = I18N[lang]
    return [
        {"label": t["nav_posts"], "href": f"/{lang}/"},
        {"label": t["nav_about"], "href": f"/{lang}/about/"},
    ]


def links_for(lang: str) -> list[dict]:
    return list(SITE["social"]) + [
        {"label": I18N[lang]["feed"], "href": f"/{lang}/feed.xml"}
    ]


def page_switcher(current: str, rest: str, avail: set) -> list[dict]:
    """Language links that preserve the current page when a translation exists,
    falling back to the language home when it does not."""
    return [
        {"code": code, "name": I18N[code]["name"],
         "href": f"/{code}/{rest}" if code in avail else f"/{code}/",
         "active": code == current}
        for code in LANGS
    ]


def base_context(lang: str) -> dict:
    return {
        "lang": lang,
        "t": I18N[lang],
        "nav": nav_for(lang),
        "links": links_for(lang),
    }


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;").replace("<", "&lt;")
        .replace(">", "&gt;").replace('"', "&quot;")
    )


# --------------------------------------------------------------------------- #
# Build                                                                       #
# --------------------------------------------------------------------------- #


def build(include_drafts: bool = False) -> None:
    env = make_env()
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)

    index_tpl = env.get_template("index.html")
    post_tpl = env.get_template("post.html")
    page_tpl = env.get_template("page.html")

    # Preload all languages so the switcher knows which translations exist.
    posts_by_lang = {lang: load_posts(lang, include_drafts) for lang in LANGS}
    pages_by_lang = {lang: load_pages(lang) for lang in LANGS}
    post_langs: dict = {}
    for lang, posts in posts_by_lang.items():
        for p in posts:
            post_langs.setdefault(p.slug, set()).add(lang)
    page_langs: dict = {}
    for lang, pages in pages_by_lang.items():
        for p in pages:
            page_langs.setdefault(p.slug, set()).add(lang)

    counts = {}
    for lang in LANGS:
        ctx = base_context(lang)
        posts = posts_by_lang[lang]
        pages = pages_by_lang[lang]
        counts[lang] = (len(posts), len(pages))

        all_tags = sorted({tag for p in posts for tag in p.tags})
        write(
            OUTPUT / lang / "index.html",
            index_tpl.render(
                path=f"/{lang}/", posts=posts, all_tags=all_tags,
                langs=page_switcher(lang, "", set(LANGS)), **ctx,
            ),
        )
        for post in posts:
            write(
                OUTPUT / lang / "posts" / post.slug / "index.html",
                post_tpl.render(
                    path=post.url, post=post,
                    langs=page_switcher(lang, f"posts/{post.slug}/", post_langs[post.slug]),
                    **ctx,
                ),
            )
        for page in pages:
            write(
                OUTPUT / lang / page.slug / "index.html",
                page_tpl.render(
                    path=page.url, page=page,
                    langs=page_switcher(lang, f"{page.slug}/", page_langs[page.slug]),
                    **ctx,
                ),
            )
        write(OUTPUT / lang / "feed.xml", build_rss(lang, posts))

    # Root: redirect to the default language.
    write(OUTPUT / "index.html", render_redirect(f"/{DEFAULT_LANG}/"))
    write(OUTPUT / "feed.xml", build_rss(DEFAULT_LANG, posts_by_lang[DEFAULT_LANG]))

    # 404 (GitHub Pages serves /404.html); use the default language.
    ctx = base_context(DEFAULT_LANG)
    write(OUTPUT / "404.html", env.get_template("404.html").render(
        path="/404.html", langs=page_switcher(DEFAULT_LANG, "", set(LANGS)), **ctx))

    # Sitemap, robots, highlight stylesheet.
    write(OUTPUT / "sitemap.xml", build_sitemap(include_drafts))
    write(OUTPUT / "robots.txt",
          f"User-agent: *\nAllow: /\nSitemap: {SITE['url']}/sitemap.xml\n")
    write(OUTPUT / "highlight.css", build_highlight_css())

    # Static assets and host config.
    if STATIC.exists():
        shutil.copytree(STATIC, OUTPUT, dirs_exist_ok=True)
    (OUTPUT / ".nojekyll").write_text("", encoding="utf-8")
    (OUTPUT / "CNAME").write_text(SITE["url"].split("://", 1)[-1] + "\n", encoding="utf-8")

    summary = ", ".join(f"{l}: {counts[l][0]}p" for l in LANGS)
    print(f"built [{summary}] -> {OUTPUT}")


def render_redirect(target: str) -> str:
    return (
        "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"UTF-8\">"
        f"<meta http-equiv=\"refresh\" content=\"0; url={target}\">"
        f"<link rel=\"canonical\" href=\"{SITE['url']}{target}\">"
        f"<script>location.replace(\"{target}\")</script>"
        f"</head><body><a href=\"{target}\">{SITE['title']}</a></body></html>"
    )


def build_rss(lang: str, posts: list[Post]) -> str:
    now = email.utils.format_datetime(dt.datetime.now(dt.timezone.utc))
    items = []
    for post in posts[:30]:
        pub = email.utils.format_datetime(
            dt.datetime.combine(post.date, dt.time(12, 0), dt.timezone.utc)
        )
        link = f"{SITE['url']}{post.url}"
        items.append(
            "<item>"
            f"<title>{xml_escape(post.title)}</title>"
            f"<link>{link}</link>"
            f"<guid isPermaLink=\"true\">{link}</guid>"
            f"<pubDate>{pub}</pubDate>"
            f"<description>{xml_escape(post.summary)}</description>"
            "</item>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0"><channel>'
        f"<title>{xml_escape(SITE['title'])}</title>"
        f"<link>{SITE['url']}/{lang}/</link>"
        f"<language>{lang}</language>"
        f"<description>{xml_escape(I18N[lang]['tagline'])}</description>"
        f"<lastBuildDate>{now}</lastBuildDate>"
        + "".join(items)
        + "</channel></rss>"
    )


def build_sitemap(include_drafts: bool) -> str:
    urls = [SITE["url"] + "/"]
    for lang in LANGS:
        urls.append(f"{SITE['url']}/{lang}/")
        for post in load_posts(lang, include_drafts):
            urls.append(f"{SITE['url']}{post.url}")
        for page in load_pages(lang):
            urls.append(f"{SITE['url']}{page.url}")
    body = "".join(f"<url><loc>{xml_escape(u)}</loc></url>" for u in urls)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + body + "</urlset>"
    )


def build_highlight_css() -> str:
    # Dark is the default; light is applied only when the toggle sets data-theme.
    dark = HtmlFormatter(style="github-dark").get_style_defs(".highlight")
    light = HtmlFormatter(style="default").get_style_defs(
        'html[data-theme="light"] .highlight'
    )
    return "/* generated by build.py — do not edit */\n" + dark + "\n" + light + "\n"


# --------------------------------------------------------------------------- #
# Local preview                                                               #
# --------------------------------------------------------------------------- #


def serve() -> None:
    import functools
    import http.server
    import socketserver

    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(OUTPUT)
    )
    with socketserver.TCPServer(("", 8000), handler) as httpd:
        print("serving http://localhost:8000  (Ctrl-C to stop)")
        httpd.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build isaklab.com")
    parser.add_argument("--drafts", action="store_true", help="include draft posts")
    parser.add_argument("--serve", action="store_true", help="serve after building")
    args = parser.parse_args()
    build(include_drafts=args.drafts or args.serve)
    if args.serve:
        serve()


if __name__ == "__main__":
    main()
