# 11ty Migration Design

**Date:** 2026-06-01
**Status:** Approved

## Summary

Migrate jsmithedin.github.io from a custom Python static site generator (`build.py` + `blog.py`) to [Eleventy (11ty)](https://www.11ty.dev/). The visual theme is preserved exactly. The homepage gains a "latest 3 posts" section above the existing repos grid. All existing Markdown posts require no changes.

## Goals

- Replace Python build with 11ty + Nunjucks
- Keep the dark terminal aesthetic (colours, fonts, card styles, scanline) identical
- Show 3 latest blog posts above the repos grid on the homepage
- Fetch GitHub repos via 11ty's data file system (no Python)
- Maintain the existing deploy to jamielab.uk via GitHub Pages

## File Structure

```
jsmithedin.github.io/
├── _data/
│   └── repos.js              # async GitHub API fetch, cached 24h via @11ty/eleventy-fetch
├── _includes/
│   ├── base.njk              # shared <head>, nav, footer, JS
│   └── post.njk              # individual post layout
├── css/
│   └── style.css             # unchanged
├── js/
│   └── main.js               # unchanged
├── posts/                    # unchanged — same .md files, same frontmatter
│   └── posts.json            # directory data file: sets layout: post.njk, tags: post
├── index.njk                 # homepage
├── blog.njk                  # blog listing at /blog/
├── .eleventy.js              # 11ty config
└── package.json
```

Files removed: `build.py`, `blog.py`, `requirements.txt`.

## Templates

### `_includes/base.njk`
Shared page shell. Provides:
- `<head>` with Google Fonts (JetBrains Mono + Syne), Tabler Icons CDN, inlined `css/style.css`
- Sticky nav: brand (`~/jsmithedin`) + links (blog, github, linkedin)
- Footer with build timestamp and source link
- Inlined `js/main.js` (typewriter effect on `.header-label`)

All pages `{% extends "_includes/base.njk" %}` and fill a `content` block.

### `index.njk` — Homepage

**Header:** same as current — `$ ls --sort=date ./` label, "jsmithedin" title, subtitle. Stats block shows posts count / repos count / Edinburgh.

**Latest posts section** (new):
- Section label: `$ tail -3 ./posts/`
- "all posts →" link top-right pointing to `/blog/`
- Lists 3 most recent posts using `collections.post | reverse | limit(3)`
- Each row: title, date, reading time, description, tag badges
- Same left-accent hover style as the blog listing page

**Repos grid** (unchanged visual):
- Section label: `$ ls --sort=date ./projects/`
- Loops over `repos` from `_data/repos.js`
- Same card layout, language badges, star count, updated date

### `blog.njk` — Blog listing at `/blog/`

Identical to current Python-generated blog index. Lists all posts (`collections.post | reverse`) as rows with title, description, date, reading time, tags.

### `_includes/post.njk` — Individual posts at `/blog/:slug/`

Applied automatically to all `posts/*.md` via `posts/posts.json`. Layout identical to current: back link, `$ cat ./posts/slug.md` label, post title, meta bar (date, reading time, tags), description block, Markdown content.

11ty's built-in Markdown processing replaces the custom `TerminalRenderer`. Post-specific CSS (code blocks, inline code, blockquotes, etc.) moves to `css/style.css` under a `/* Post */` section rather than being injected inline.

**OpenGraph / social meta tags** are injected in the `<head>` for post pages via an overridable `head` block in `base.njk`. Post pages set:

```html
<meta property="og:title" content="{{ title }}">
<meta property="og:description" content="{{ description }}">
<meta property="og:type" content="article">
<meta property="og:url" content="https://jamielab.uk/blog/{{ page.fileSlug }}/">
<meta property="article:published_time" content="{{ date | isoDate }}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{{ title }}">
<meta name="twitter:description" content="{{ description }}">
```

`base.njk` provides sensible defaults for non-post pages (`og:type: website`, title and description from page-level data). An `isoDate` filter in `.eleventy.js` formats the post date as ISO 8601 for `article:published_time`.

## Data: GitHub Repos (`_data/repos.js`)

Uses `@11ty/eleventy-fetch` to call the GitHub API:

```js
const EleventyFetch = require("@11ty/eleventy-fetch");

module.exports = async function () {
  const token = process.env.GITHUB_TOKEN;
  const headers = { Accept: "application/vnd.github+json" };
  if (token) headers.Authorization = `token ${token}`;

  // fetches all pages, filters forks, sorts by updated_at
  // cache duration: "1d" for local dev; CI deletes .cache/ on scheduled runs
};
```

The data shape mirrors what `build.py` currently computes: `name`, `description`, `html_url`, `homepage`, `language`, `stargazers_count`, `updated_at` (formatted), `topics`.

## Blog Posts

`posts/*.md` frontmatter is unchanged:

```yaml
---
title: "Post title"
date: 2026-05-01
tags: [terraform, aws, iac]
description: "Short description."
---
```

11ty's `collections.post` tag is applied via `posts/posts.json` (directory data file), so no per-post changes are needed.

`posts/posts.json` sets a computed `permalink` to strip the `YYYY-MM-DD-` date prefix and place posts under `/blog/`:

```json
{
  "layout": "post.njk",
  "tags": "post",
  "permalink": "/blog/{{ page.fileSlug | replace(r/^\d{4}-\d{2}-\d{2}-/, '') }}/"
}
```

This produces `/blog/terraform-s3-locking/` from `posts/2026-05-01-terraform-s3-locking.md`, matching the current URL structure exactly.

Reading time and the `limit` filter are both registered as custom filters in `.eleventy.js`:
- `readingTime`: `Math.max(1, content.split(/\s+/).length / 200)`
- `limit(n)`: returns the first `n` items of an array (used on homepage to cap posts at 3)
- `isoDate`: formats a JS Date as ISO 8601 string for `article:published_time`

## Styling

`css/style.css` is preserved entirely. Post-specific styles (currently injected as inline `<style>` by `blog.py`) move into a `/* Post */` section at the bottom of `style.css`. No visual changes.

The scanline overlay (`body::after`), all CSS custom properties, card hover animations, and badge colours are untouched.

## CI / Deploy

`.github/workflows/deploy.yml` changes:

| Before | After |
|---|---|
| `actions/setup-python@v5` | `actions/setup-node@v4` (Node 20) |
| `pip install -r requirements.txt` | `npm ci` |
| `python build.py` | `npx eleventy` |
| `publish_dir: ./output` | `publish_dir: ./_site` |

The scheduled Monday cron (`0 6 * * 1`) is kept. On scheduled runs, the workflow deletes `.cache/` before building so `@11ty/eleventy-fetch` re-fetches fresh repo data.

`GITHUB_TOKEN` is passed as an environment variable to the build step, same as now.

`cname: jamielab.uk` is unchanged.

## What Is Not Changing

- Domain and GitHub Pages deployment mechanism
- All `posts/*.md` content and frontmatter
- `css/style.css` (structurally — post CSS is appended, not replaced)
- `js/main.js` (typewriter effect)
- Visual theme: colours, fonts, card layout, hover animations, scanline overlay
- Nav links and their targets
- URL structure: `/`, `/blog/`, `/blog/:slug/`
