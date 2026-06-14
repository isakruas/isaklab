# isaklab.com

A static site. Markdown in, HTML out, no backend.

A single Python script (`build.py`) reads Markdown from `content/`, renders it
through Jinja2 templates in `templates/`, and writes static HTML to `public/`.
GitHub Actions builds and publishes to GitHub Pages on every push to `main`.

## Write a post

Add a Markdown file to `content/posts/`. Name it `YYYY-MM-DD-slug.md` (the date
prefix is stripped from the URL). Start it with front matter:

```markdown
---
title: The title
date: 2026-06-13
tags: rust, avr
summary: One sentence shown in listings and as the meta description.
image: /some-card.png   # optional; social preview. Defaults to a generated card.
draft: true        # optional; omit or set false to publish
---

The body, in Markdown. Fenced code blocks are syntax-highlighted.
```

The post is published at `/posts/slug/`. Standalone pages (like `about`) live in
`content/pages/` and are published at `/slug/`.

## Build locally

```sh
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

python build.py            # build to public/
python build.py --drafts   # include drafts
python build.py --serve    # build, then serve http://localhost:8000
```

## Deploy

Push to `main`. The workflow in `.github/workflows/deploy.yml` does the rest.

One-time setup in the repository settings: **Settings → Pages → Build and
deployment → Source: GitHub Actions**. The custom domain `isaklab.com` is set via
the `CNAME` file, which `build.py` writes into `public/` on every build.

## Layout

```
build.py              site generator
requirements.txt      Markdown, Pygments, Jinja2
content/posts/        one Markdown file per post
content/pages/        standalone pages (about, ...)
templates/            Jinja2 templates
static/               style.css and other assets, copied verbatim
public/               generated output (gitignored)
```

Site configuration — title, tagline, nav, links, locales — lives in the `SITE`
dict at the top of `build.py`.

## SEO & social

Every build generates, with no manual step:

- `sitemap.xml` — sitemaps.org 0.9 with per-URL `hreflang` alternates (each
  translation links its siblings plus `x-default`), `<lastmod>`, `changefreq`
  and `priority`.
- `feed.xml` and `/<lang>/feed.xml` — RSS 2.0 with `atom:link rel="self"`,
  `dc:creator`, per-item categories, and full-text `content:encoded`.
- `og-<lang>.png` — 1200×630 Open Graph cards (one per language), plus
  `icon-192.png` / `icon-512.png` maskable PWA icons and `site.webmanifest`.
- Per-page canonical, `hreflang`, Open Graph / Twitter Card meta, and
  schema.org JSON-LD (`WebSite`/`Blog`, `BlogPosting`, `WebPage`,
  `BreadcrumbList`).
- `.well-known/security.txt` (RFC 9116), and a `sw.js` service worker that
  serves static assets offline (network-first; HTML is never cached).

`validate.py` runs in CI after the build and fails the deploy if anything is
broken — malformed XML/JSON, invalid JSON-LD, missing required files, or a
dangling internal link. Run it locally with `python validate.py public`.

To verify domain ownership in Google Search Console or Bing, paste the token
into `SITE["verification"]` in `build.py`; empty entries emit no tag.

CSS and JS are minified on build. Set `SITE["twitter"]` to an `@handle` to emit
`twitter:site`/`twitter:creator` (left empty by default, so the tags are
omitted rather than faked).

Generating the social cards and icons requires Pillow (in `requirements.txt`);
without it the build still succeeds and simply skips those images.
