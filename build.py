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
    # BCP-47 / Open Graph locales, used for og:locale and og:locale:alternate.
    "locales": {"en": "en_US", "pt": "pt_BR", "es": "es_ES"},
    # Optional X/Twitter handle (with @). Leave "" if there is no account —
    # the twitter:site/creator tags are then omitted rather than faked.
    "twitter": "",
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
        "skip_to_content": "Pular para o conteúdo",
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
        "skip_to_content": "Skip to content",
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
        "skip_to_content": "Saltar al contenido",
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


_IMG_RE = re.compile(r"<img\s+([^>]*?)/?>", re.IGNORECASE)


def _enhance_images(html: str) -> str:
    """Add lazy loading and async decoding to every <img>, and stamp intrinsic
    width/height for local images so the browser can reserve space (no layout
    shift). Remote images are left dimensionless — we cannot measure them."""

    def repl(match: re.Match) -> str:
        attrs = match.group(1)
        if "loading=" not in attrs:
            attrs += ' loading="lazy"'
        if "decoding=" not in attrs:
            attrs += ' decoding="async"'
        src = re.search(r'src="([^"]+)"', attrs)
        if src and "width=" not in attrs and "height=" not in attrs:
            dims = _local_image_size(src.group(1))
            if dims:
                attrs += f' width="{dims[0]}" height="{dims[1]}"'
        return f"<img {attrs.strip()}>"

    return _IMG_RE.sub(repl, html)


def _local_image_size(src: str) -> tuple[int, int] | None:
    if src.startswith(("http://", "https://", "//", "data:")):
        return None
    candidate = STATIC / src.lstrip("/")
    if not candidate.is_file():
        return None
    try:
        from PIL import Image

        with Image.open(candidate) as im:
            return im.size
    except Exception:
        return None


def render_markdown(body: str) -> str:
    md = markdown.Markdown(extensions=MD_EXTENSIONS, extension_configs=MD_CONFIG)
    return _enhance_images(md.convert(body))


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


def abs_url(path_or_url: str) -> str:
    """Turn a site-relative path into an absolute https URL; pass through URLs."""
    if path_or_url.startswith(("http://", "https://")):
        return path_or_url
    if not path_or_url.startswith("/"):
        path_or_url = "/" + path_or_url
    return SITE["url"] + path_or_url


def absolutize_html(html: str) -> str:
    """Rewrite root-relative href/src to absolute URLs, for feed readers that
    do not resolve against a base."""
    return re.sub(r'(href|src)="(/[^"]*)"', rf'\1="{SITE["url"]}\2"', html)


def resolved_image(lang: str, meta: dict) -> str:
    """Absolute URL of a document's social image: an explicit `image:` from the
    front matter, otherwise the generated per-language Open Graph card."""
    custom = str(meta.get("image", "")).strip()
    return abs_url(custom) if custom else f"{SITE['url']}/og-{lang}.png"


def x_default_from(langs: list[dict]) -> str:
    """The hreflang=x-default target: the default-language version of this page."""
    for entry in langs:
        if entry["code"] == DEFAULT_LANG:
            return entry["href"]
    return f"/{DEFAULT_LANG}/"


# --------------------------------------------------------------------------- #
# Structured data (schema.org JSON-LD)                                         #
# --------------------------------------------------------------------------- #


def person_node() -> dict:
    return {
        "@type": "Person",
        "@id": SITE["url"] + "/#person",
        "name": SITE["author"],
        "url": SITE["url"],
        "image": SITE["url"] + "/icon-512.png",
        "sameAs": [s["href"] for s in SITE["social"]],
    }


def breadcrumb_node(trail: list[tuple[str, str]]) -> dict:
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": name, "item": abs_url(url)}
            for i, (name, url) in enumerate(trail)
        ],
    }


def website_node(lang: str) -> dict:
    return {
        "@type": "WebSite",
        "@id": SITE["url"] + "/#website",
        "name": SITE["title"],
        "url": SITE["url"],
        "inLanguage": lang,
        "description": I18N[lang]["tagline"],
        "publisher": {"@id": SITE["url"] + "/#person"},
    }


def index_jsonld(lang: str, posts: list["Post"]) -> dict:
    blog = {
        "@type": "Blog",
        "@id": f"{SITE['url']}/{lang}/#blog",
        "name": SITE["title"],
        "url": f"{SITE['url']}/{lang}/",
        "inLanguage": lang,
        "description": I18N[lang]["tagline"],
        "publisher": {"@id": SITE["url"] + "/#person"},
        "blogPost": [
            {
                "@type": "BlogPosting",
                "headline": p.title,
                "url": abs_url(p.url),
                "datePublished": p.iso_date,
                "inLanguage": lang,
            }
            for p in posts
        ],
    }
    return {"@context": "https://schema.org", "@graph": [person_node(), website_node(lang), blog]}


def post_jsonld(lang: str, post: "Post", image: str) -> dict:
    article = {
        "@type": "BlogPosting",
        "@id": abs_url(post.url) + "#article",
        "headline": post.title,
        "description": post.summary,
        "url": abs_url(post.url),
        "datePublished": post.iso_date,
        "dateModified": post.iso_date,
        "inLanguage": lang,
        "image": image,
        "author": {"@id": SITE["url"] + "/#person"},
        "publisher": {"@id": SITE["url"] + "/#person"},
        "isPartOf": {"@id": SITE["url"] + "/#website"},
        "mainEntityOfPage": {"@type": "WebPage", "@id": abs_url(post.url)},
    }
    if post.tags:
        article["keywords"] = post.tags
    trail = breadcrumb_node([(SITE["title"], f"/{lang}/"),
                             (I18N[lang]["nav_posts"], f"/{lang}/"),
                             (post.title, post.url)])
    return {"@context": "https://schema.org", "@graph": [person_node(), article, trail]}


def page_jsonld(lang: str, page: "Document", image: str) -> dict:
    node = {
        "@type": "WebPage",
        "@id": abs_url(page.url),
        "name": page.title,
        "description": page.summary or I18N[lang]["tagline"],
        "url": abs_url(page.url),
        "inLanguage": lang,
        "image": image,
        "isPartOf": {"@id": SITE["url"] + "/#website"},
        "about": {"@id": SITE["url"] + "/#person"},
    }
    trail = breadcrumb_node([(SITE["title"], f"/{lang}/"), (page.title, page.url)])
    return {"@context": "https://schema.org", "@graph": [person_node(), node, trail]}


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
        index_langs = page_switcher(lang, "", set(LANGS))
        write(
            OUTPUT / lang / "index.html",
            index_tpl.render(
                path=f"/{lang}/", posts=posts, all_tags=all_tags,
                langs=index_langs, x_default=x_default_from(index_langs),
                og_image=resolved_image(lang, {}), jsonld=index_jsonld(lang, posts),
                **ctx,
            ),
        )
        for post in posts:
            post_langs_sw = page_switcher(lang, f"posts/{post.slug}/", post_langs[post.slug])
            image = resolved_image(lang, post.meta)
            write(
                OUTPUT / lang / "posts" / post.slug / "index.html",
                post_tpl.render(
                    path=post.url, post=post,
                    langs=post_langs_sw, x_default=x_default_from(post_langs_sw),
                    og_image=image, jsonld=post_jsonld(lang, post, image),
                    **ctx,
                ),
            )
        for page in pages:
            page_langs_sw = page_switcher(lang, f"{page.slug}/", page_langs[page.slug])
            image = resolved_image(lang, page.meta)
            write(
                OUTPUT / lang / page.slug / "index.html",
                page_tpl.render(
                    path=page.url, page=page,
                    langs=page_langs_sw, x_default=x_default_from(page_langs_sw),
                    og_image=image, jsonld=page_jsonld(lang, page, image),
                    **ctx,
                ),
            )
        write(OUTPUT / lang / "feed.xml", build_rss(lang, posts))

    # Root: redirect to the default language.
    write(OUTPUT / "index.html", render_redirect(f"/{DEFAULT_LANG}/"))
    write(OUTPUT / "feed.xml",
          build_rss(DEFAULT_LANG, posts_by_lang[DEFAULT_LANG], feed_path="/feed.xml"))

    # 404 (GitHub Pages serves /404.html); use the default language.
    ctx = base_context(DEFAULT_LANG)
    nf_langs = page_switcher(DEFAULT_LANG, "", set(LANGS))
    write(OUTPUT / "404.html", env.get_template("404.html").render(
        path="/404.html", langs=nf_langs, x_default=x_default_from(nf_langs),
        og_image=resolved_image(DEFAULT_LANG, {}), jsonld=None, **ctx))

    # Sitemap, robots, highlight stylesheet.
    write(OUTPUT / "sitemap.xml",
          build_sitemap(posts_by_lang, pages_by_lang, post_langs, page_langs))
    write(OUTPUT / "robots.txt",
          f"User-agent: *\nAllow: /\nSitemap: {SITE['url']}/sitemap.xml\n")
    write(OUTPUT / "highlight.css", build_highlight_css())
    write(OUTPUT / "site.webmanifest", build_webmanifest())

    # Static assets and host config.
    if STATIC.exists():
        shutil.copytree(STATIC, OUTPUT, dirs_exist_ok=True)
    build_og_assets(OUTPUT)  # social cards + maskable PWA icons
    minify_assets(OUTPUT)    # collapse CSS/JS after everything is in place
    (OUTPUT / ".nojekyll").write_text("", encoding="utf-8")
    (OUTPUT / "CNAME").write_text(SITE["url"].split("://", 1)[-1] + "\n", encoding="utf-8")

    summary = ", ".join(f"{l}: {counts[l][0]}p" for l in LANGS)
    print(f"built [{summary}] -> {OUTPUT}")


def render_redirect(target: str) -> str:
    alts = "".join(
        f'<link rel="alternate" hreflang="{l}" href="{SITE["url"]}/{l}/">'
        for l in LANGS
    )
    return (
        "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"UTF-8\">"
        f"<meta http-equiv=\"refresh\" content=\"0; url={target}\">"
        f"<link rel=\"canonical\" href=\"{SITE['url']}{target}\">"
        + alts
        + f'<link rel="alternate" hreflang="x-default" href="{SITE["url"]}{target}">'
        f"<script>location.replace(\"{target}\")</script>"
        f"</head><body><a href=\"{target}\">{SITE['title']}</a></body></html>"
    )


def build_rss(lang: str, posts: list[Post], feed_path: str | None = None) -> str:
    feed_path = feed_path or f"/{lang}/feed.xml"
    self_url = f"{SITE['url']}{feed_path}"
    now = email.utils.format_datetime(dt.datetime.now(dt.timezone.utc))
    items = []
    for post in posts[:30]:
        pub = email.utils.format_datetime(
            dt.datetime.combine(post.date, dt.time(12, 0), dt.timezone.utc)
        )
        link = f"{SITE['url']}{post.url}"
        categories = "".join(
            f"<category>{xml_escape(tag)}</category>" for tag in post.tags
        )
        content = absolutize_html(post.html).replace("]]>", "]]]]><![CDATA[>")
        items.append(
            "<item>"
            f"<title>{xml_escape(post.title)}</title>"
            f"<link>{link}</link>"
            f"<guid isPermaLink=\"true\">{link}</guid>"
            f"<pubDate>{pub}</pubDate>"
            f"<dc:creator>{xml_escape(SITE['author'])}</dc:creator>"
            + categories
            + f"<description>{xml_escape(post.summary)}</description>"
            f"<content:encoded><![CDATA[{content}]]></content:encoded>"
            "</item>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" '
        'xmlns:atom="http://www.w3.org/2005/Atom" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:content="http://purl.org/rss/1.0/modules/content/">'
        "<channel>"
        f"<title>{xml_escape(SITE['title'])}</title>"
        f"<link>{SITE['url']}/{lang}/</link>"
        f'<atom:link href="{self_url}" rel="self" type="application/rss+xml"/>'
        f"<language>{lang}</language>"
        f"<description>{xml_escape(I18N[lang]['tagline'])}</description>"
        f"<lastBuildDate>{now}</lastBuildDate>"
        "<generator>build.py</generator>"
        "<docs>https://www.rssboard.org/rss-specification</docs>"
        f"<ttl>1440</ttl>"
        + "".join(items)
        + "</channel></rss>"
    )


def _iso(d: dt.date | None) -> str | None:
    return d.isoformat() if d else None


def _iso_from_mtime(path: Path) -> str:
    ts = path.stat().st_mtime
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).date().isoformat()


def build_sitemap(posts_by_lang: dict, pages_by_lang: dict,
                  post_langs: dict, page_langs: dict) -> str:
    """Sitemaps.org 0.9 with per-URL hreflang alternates (Google's multilingual
    annotation) and W3C-datetime <lastmod>. Every translation of a document
    lists all its siblings plus x-default."""
    entries: list[str] = []

    def url_block(loc: str, lastmod: str | None, changefreq: str, priority: str,
                  alternates: list[tuple[str, str]]) -> str:
        links = "".join(
            f'<xhtml:link rel="alternate" hreflang="{hl}" '
            f'href="{xml_escape(abs_url(href))}"/>'
            for hl, href in alternates
        )
        lm = f"<lastmod>{lastmod}</lastmod>" if lastmod else ""
        return (f"<url><loc>{xml_escape(abs_url(loc))}</loc>{lm}"
                f"<changefreq>{changefreq}</changefreq>"
                f"<priority>{priority}</priority>{links}</url>")

    def emit_group(url_for, group_langs: set, lastmod_for,
                   changefreq: str, priority: str) -> None:
        present = [l for l in LANGS if l in group_langs]
        alternates = [(l, url_for(l)) for l in present]
        xdef = url_for(DEFAULT_LANG) if DEFAULT_LANG in group_langs else f"/{DEFAULT_LANG}/"
        alternates.append(("x-default", xdef))
        for l in present:
            entries.append(
                url_block(url_for(l), lastmod_for(l), changefreq, priority, alternates))

    # Language homes — lastmod is the newest post in that language.
    def home_lastmod(l: str) -> str | None:
        return _iso(max((p.date for p in posts_by_lang.get(l, [])), default=None))

    emit_group(lambda l: f"/{l}/", set(LANGS), home_lastmod, "weekly", "1.0")

    # Posts.
    post_date = {(p.lang, p.slug): p.date
                 for ps in posts_by_lang.values() for p in ps}
    for slug, glangs in sorted(post_langs.items()):
        emit_group(lambda l, s=slug: f"/{l}/posts/{s}/", glangs,
                   lambda l, s=slug: _iso(post_date.get((l, s))), "monthly", "0.8")

    # Standalone pages — lastmod from source file mtime.
    page_mtime = {(l, pg.slug): _iso_from_mtime(pg.source)
                  for l, pages in pages_by_lang.items() for pg in pages}
    for slug, glangs in sorted(page_langs.items()):
        emit_group(lambda l, s=slug: f"/{l}/{s}/", glangs,
                   lambda l, s=slug: page_mtime.get((l, s)), "monthly", "0.5")

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">'
        + "".join(entries) + "</urlset>"
    )


def build_webmanifest() -> str:
    import json

    data = {
        "name": SITE["title"],
        "short_name": SITE["title"],
        "description": I18N[DEFAULT_LANG]["tagline"],
        "lang": DEFAULT_LANG,
        "dir": "ltr",
        "start_url": f"/{DEFAULT_LANG}/",
        "scope": "/",
        "id": "/",
        "display": "standalone",
        "background_color": "#0d1117",
        "theme_color": "#0d1117",
        "icons": [
            {"src": "/favicon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any"},
            {"src": "/favicon-32.png", "sizes": "32x32", "type": "image/png"},
            {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
            {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
            {"src": "/apple-touch-icon.png", "sizes": "180x180", "type": "image/png"},
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def build_highlight_css() -> str:
    # Dark is the default; light is applied only when the toggle sets data-theme.
    dark = HtmlFormatter(style="github-dark").get_style_defs(".highlight")
    light = HtmlFormatter(style="default").get_style_defs(
        'html[data-theme="light"] .highlight'
    )
    return "/* generated by build.py — do not edit */\n" + dark + "\n" + light + "\n"


# --------------------------------------------------------------------------- #
# Asset minification                                                          #
# --------------------------------------------------------------------------- #


def _minify_css(css: str) -> str:
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)   # comments
    css = re.sub(r"\s+", " ", css)                          # collapse whitespace
    css = re.sub(r"\s*([{}:;,>~+])\s*", r"\1", css)         # trim around tokens
    css = css.replace(";}", "}")                            # drop trailing semicolons
    return css.strip()


def _minify_js(js: str) -> str:
    # Conservative: keep newlines (so automatic semicolon insertion is safe),
    # drop indentation, blank lines, full-line // comments, and block comments.
    js = re.sub(r"/\*.*?\*/", "", js, flags=re.DOTALL)
    lines = []
    for line in js.splitlines():
        s = line.strip()
        if s and not s.startswith("//"):
            lines.append(s)
    return "\n".join(lines)


def minify_assets(output: Path) -> None:
    for path in output.rglob("*.css"):
        path.write_text(_minify_css(path.read_text(encoding="utf-8")), encoding="utf-8")
    for path in output.rglob("*.js"):
        path.write_text(_minify_js(path.read_text(encoding="utf-8")), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Generated images: Open Graph social cards + maskable PWA icons              #
# --------------------------------------------------------------------------- #

_FONT_DIRS = [
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/dejavu",
    "/usr/share/fonts/TTF",
    "/Library/Fonts",
    "/System/Library/Fonts/Supplemental",
]


def _load_font(names: list[str], size: int):
    from PIL import ImageFont

    for name in names:
        for d in _FONT_DIRS:
            path = Path(d) / name
            if path.is_file():
                return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _wrap(draw, text: str, font, max_width: int) -> list[str]:
    words, lines, line = text.split(), [], ""
    for word in words:
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def build_og_assets(output: Path) -> None:
    """Render the 1200×630 Open Graph cards (one per language) and the 192/512
    maskable PWA icons. Degrades to a no-op if Pillow is unavailable."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("warning: Pillow not installed — skipping OG cards and PWA icons")
        return

    BG, FG, MUTED, FAINT, ACCENT = "#0d1117", "#e6edf3", "#8b949e", "#6e7681", "#1f6feb"
    mono_bold = ["DejaVuSansMono-Bold.ttf", "DejaVuSans-Bold.ttf"]
    sans = ["DejaVuSans.ttf"]

    # --- Open Graph cards, per language ---------------------------------- #
    f_word = _load_font(mono_bold, 112)
    f_badge = _load_font(mono_bold, 92)
    f_tag = _load_font(sans, 38)
    f_foot = _load_font(mono_bold, 28)

    for lang in LANGS:
        img = Image.new("RGB", (1200, 630), BG)
        d = ImageDraw.Draw(img)
        # "ik" badge, matching favicon.svg.
        d.rounded_rectangle((90, 84, 246, 240), radius=34, fill=ACCENT)
        bx = d.textbbox((0, 0), "ik", font=f_badge)
        d.text((168 - (bx[2] - bx[0]) / 2, 162 - (bx[3] - bx[1]) / 2 - bx[1]),
               "ik", font=f_badge, fill="#ffffff")
        # Wordmark.
        d.text((90, 300), SITE["title"], font=f_word, fill=FG)
        # Tagline (wrapped).
        y = 440
        for line in _wrap(d, I18N[lang]["tagline"], f_tag, 1020)[:3]:
            d.text((92, y), line, font=f_tag, fill=MUTED)
            y += 52
        # Footer.
        d.text((92, 560), f"{SITE['author']} · {SITE['callsign']} · "
               f"{SITE['url'].split('://')[-1]}", font=f_foot, fill=FAINT)
        img.save(output / f"og-{lang}.png", optimize=True)

    # --- Maskable PWA icons --------------------------------------------- #
    for size in (192, 512):
        img = Image.new("RGB", (size, size), ACCENT)
        d = ImageDraw.Draw(img)
        f = _load_font(mono_bold, int(size * 0.42))
        bb = d.textbbox((0, 0), "ik", font=f)
        d.text((size / 2 - (bb[2] - bb[0]) / 2, size / 2 - (bb[3] - bb[1]) / 2 - bb[1]),
               "ik", font=f, fill="#ffffff")
        img.save(output / f"icon-{size}.png", optimize=True)


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
