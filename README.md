# jsmithedin.github.io

Personal project portfolio and blog, served at [jamielab.uk](https://jamielab.uk).

## How it works

[Eleventy (11ty)](https://www.11ty.dev/) builds the site from Nunjucks templates. `_data/repos.js` fetches all non-fork repos via the GitHub API (cached 24h). Posts in `posts/*.md` are rendered at `/blog/:slug/`. GitHub Actions deploys the output to GitHub Pages.

The site rebuilds:
- On every push to `main`
- Every Monday at 06:00 UTC (to pick up fresh repo data)
- Manually via the Actions tab (workflow_dispatch)

## Setup

### 1. Create the repo

Name it `jsmithedin.github.io`. Push this code to `main`.

### 2. Enable GitHub Pages

Settings → Pages → Source: `gh-pages` branch, `/ (root)`.

### 3. Custom domain

In Settings → Pages → Custom domain, set `jamielab.uk`.

Add these DNS records with your registrar:

| Type  | Name | Value                |
|-------|------|----------------------|
| A     | @    | 185.199.108.153      |
| A     | @    | 185.199.109.153      |
| A     | @    | 185.199.110.153      |
| A     | @    | 185.199.111.153      |
| CNAME | www  | jsmithedin.github.io |

The `cname: jamielab.uk` line in the workflow writes a `CNAME` file on each deploy.

### 4. Run locally

```bash
npm install
export GITHUB_TOKEN=ghp_yourtoken   # optional, avoids rate limits
npm run build        # outputs to _site/
npm run serve        # live-reload dev server at http://localhost:8080
```

## Adding a blog post

Create a Markdown file in `posts/`:

```
posts/YYYY-MM-DD-your-post-slug.md
```

Frontmatter:

```yaml
---
title: "Your post title"
date: 2026-06-01
tags: [aws, python]
description: "One-sentence summary."
---
```

The date prefix is stripped from the URL — the post will be available at `/blog/your-post-slug/`.

## Customising

- **Subtitle / about text** — edit `index.njk` and `blog.njk`
- **Nav links** — edit `_includes/base.njk`
- **Styles** — edit `css/style.css`
- **Repo filter / data shape** — edit `_data/repos.js`
