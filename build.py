import os
import requests
from datetime import datetime
from pathlib import Path

GITHUB_USERNAME = "jsmithedin"
OUTPUT_DIR = Path("output")

NAV_LINKS = [
    {"label": "github", "url": f"https://github.com/{GITHUB_USERNAME}", "icon": "ti-brand-github"},
    {"label": "linkedin", "url": "https://www.linkedin.com/in/jamie-smith-engineer", "icon": "ti-brand-linkedin"},
    # Uncomment when blog is ready:
    # {"label": "blog", "url": "/blog", "icon": "ti-pencil"},
]


def get_repos(token: str | None = None) -> list[dict]:
    headers = {"Authorization": f"token {token}"} if token else {}
    headers["Accept"] = "application/vnd.github+json"
    url = f"https://api.github.com/users/{GITHUB_USERNAME}/repos"

    repos = []
    page = 1
    while True:
        r = requests.get(
            url,
            headers=headers,
            params={"page": page, "per_page": 100, "sort": "updated", "direction": "desc"},
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1

    return [r for r in repos if not r["fork"]]


def format_date(iso: str) -> str:
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return dt.strftime("%b %Y")


def language_class(lang: str | None) -> str:
    mapping = {
        "Python": "lang-python",
        "TypeScript": "lang-ts",
        "JavaScript": "lang-js",
        "Rust": "lang-rust",
        "Go": "lang-go",
        "Shell": "lang-shell",
        "HCL": "lang-hcl",
    }
    return mapping.get(lang or "", "lang-other")


def render_repo_card(repo: dict) -> str:
    name = repo["name"]
    desc = repo.get("description") or ""
    url = repo["html_url"]
    lang = repo.get("language")
    stars = repo["stargazers_count"]
    updated = format_date(repo["updated_at"])
    homepage = repo.get("homepage") or ""
    topics = repo.get("topics") or []

    lang_badge = (
        f'<span class="badge {language_class(lang)}">{lang}</span>' if lang else ""
    )

    topic_badges = "".join(
        f'<span class="badge badge-topic">{t}</span>' for t in topics[:5]
    )

    homepage_link = (
        f'<a href="{homepage}" class="card-link external" target="_blank" rel="noopener">'
        f'<i class="ti ti-external-link" aria-hidden="true"></i> live</a>'
        if homepage
        else ""
    )

    stars_display = f'<span class="meta-item"><i class="ti ti-star" aria-hidden="true"></i> {stars}</span>' if stars else ""

    return f"""
    <article class="repo-card">
      <div class="card-header">
        <a href="{url}" class="card-title" target="_blank" rel="noopener">{name}</a>
        <div class="card-links">
          {homepage_link}
          <a href="{url}" class="card-link" target="_blank" rel="noopener">
            <i class="ti ti-brand-github" aria-hidden="true"></i> source
          </a>
        </div>
      </div>
      <p class="card-desc">{desc}</p>
      <div class="card-footer">
        <div class="badges">
          {lang_badge}
          {topic_badges}
        </div>
        <div class="card-meta">
          {stars_display}
          <span class="meta-item"><i class="ti ti-clock" aria-hidden="true"></i> {updated}</span>
        </div>
      </div>
    </article>"""


def render_nav() -> str:
    links = "".join(
        f'<a href="{l["url"]}" class="nav-link" target="_blank" rel="noopener">'
        f'<i class="ti {l["icon"]}" aria-hidden="true"></i> {l["label"]}</a>'
        for l in NAV_LINKS
    )
    return f"""
    <nav class="site-nav">
      <div class="nav-inner">
        <a href="/" class="nav-brand">
          <span class="prompt">~/</span>jsmithedin
        </a>
        <div class="nav-links">{links}</div>
      </div>
    </nav>"""


def render_html(repos: list[dict]) -> str:
    cards = "".join(render_repo_card(r) for r in repos)
    nav = render_nav()
    count = len(repos)
    built = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    css = Path("css/style.css").read_text()
    js = Path("js/main.js").read_text()

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>jsmithedin &mdash; projects</title>
  <meta name="description" content="Jamie Smith &mdash; Principal Engineer. Projects and open source work.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Syne:wght@400;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.19.0/dist/tabler-icons.min.css">
  <style>{css}</style>
</head>
<body>
  {nav}
  <main class="site-main">
    <header class="site-header">
      <div class="header-inner">
        <div class="header-text">
          <p class="header-label"><span class="prompt">$</span> ls --sort=date ./projects</p>
          <h1 class="header-title">projects</h1>
          <p class="header-subtitle">Principal engineer. AWS &amp; Python. Applied AI in energy &amp; utilities.</p>
        </div>
        <div class="header-stats">
          <div class="stat">
            <span class="stat-value">{count}</span>
            <span class="stat-label">repositories</span>
          </div>
          <div class="stat-divider">/</div>
          <div class="stat">
            <span class="stat-value">Edinburgh</span>
            <span class="stat-label">location</span>
          </div>
        </div>
      </div>
    </header>

    <section class="repo-grid" aria-label="Project repositories">
      {cards}
    </section>
  </main>

  <footer class="site-footer">
    <p class="footer-text">
      <span class="prompt">$</span> built {built} &mdash;
      <a href="https://github.com/{GITHUB_USERNAME}/jsmithedin.github.io" class="footer-link">source</a>
    </p>
  </footer>

  <script>{js}</script>
</body>
</html>"""


def build():
    token = os.environ.get("GITHUB_TOKEN")
    repos = get_repos(token)
    print(f"Fetched {len(repos)} repos for {GITHUB_USERNAME}")

    OUTPUT_DIR.mkdir(exist_ok=True)
    html = render_html(repos)
    (OUTPUT_DIR / "index.html").write_text(html)
    print(f"Built output/index.html")


if __name__ == "__main__":
    build()
