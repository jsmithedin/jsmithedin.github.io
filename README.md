# jsmithedin.github.io

Personal project portfolio, auto-generated from GitHub repos and served at [jamielab.uk](https://jamielab.uk).

## How it works

`build.py` fetches all non-fork repos via the GitHub API, generates a static `index.html`, and GitHub Actions deploys it to GitHub Pages.

The site rebuilds:
- On every push to `main`
- Every Monday at 06:00 UTC
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

The `cname: jamielab.uk` line in the workflow writes a `CNAME` file on each deploy, so you don't need to keep re-entering it in Settings.

### 4. Run locally

```bash
pip install requests
export GITHUB_TOKEN=ghp_yourtoken   # optional, avoids rate limits
python build.py
open output/index.html
```

## Adding a blog

When ready, uncomment the blog link in `build.py`:

```python
NAV_LINKS = [
    ...
    {"label": "blog", "url": "/blog", "icon": "ti-pencil"},
]
```

Then add a `blog/` directory to `output/` with its own `index.html`.

## Customising the about text

Edit the `header-subtitle` content in `render_html()` inside `build.py`.
