# isaklab.com

A static site. Markdown in, HTML out, no backend.

A single Python script (`build.py`) reads Markdown from `content/`, renders it
through Jinja2 templates in `templates/`, and writes static HTML to `public/`.
GitHub Actions builds and publishes to GitHub Pages on every push to `master`.

## Write a post

Add a Markdown file to `content/posts/`. Name it `YYYY-MM-DD-slug.md` (the date
prefix is stripped from the URL). Start it with front matter:

```markdown
---
title: The title
date: 2026-06-13
tags: rust, avr
summary: One sentence shown in listings and as the meta description.
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

Push to `master`. The workflow in `.github/workflows/deploy.yml` does the rest.

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

Site configuration — title, tagline, nav, links — lives in the `SITE` dict at
the top of `build.py`.
