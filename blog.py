"""
blog.py — generates blog listing and individual post pages
from Markdown files in posts/ with YAML frontmatter.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path

import frontmatter
import mistune

POSTS_DIR = Path("posts")


# ── Markdown renderer ────────────────────────────────────────────────────────

class TerminalRenderer(mistune.HTMLRenderer):
    """Renders Markdown to HTML using the portfolio's terminal aesthetic."""

    def heading(self, text: str, level: int, **attrs) -> str:
        cls = f"post-h{level}"
        return f'<h{level} class="{cls}">{text}</h{level}>\n'

    def block_code(self, code: str, **attrs) -> str:
        lang = (attrs.get("info") or "").strip()
        lang_label = f'<span class="code-lang">{lang}</span>' if lang else ""
        escaped = (
            code.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
        )
        return (
            f'<div class="code-block">'
            f'{lang_label}'
            f'<pre><code>{escaped}</code></pre>'
            f'</div>\n'
        )

    def codespan(self, code: str) -> str:
        return f'<code class="inline-code">{code}</code>'

    def paragraph(self, text: str) -> str:
        return f'<p class="post-p">{text}</p>\n'

    def list(self, text: str, ordered: bool, **attrs) -> str:
        tag = "ol" if ordered else "ul"
        return f'<{tag} class="post-list">{text}</{tag}>\n'

    def list_item(self, text: str, **attrs) -> str:
        return f'<li>{text}</li>\n'

    def block_quote(self, text: str) -> str:
        return f'<blockquote class="post-quote">{text}</blockquote>\n'

    def link(self, text: str, url: str, title: str | None = None) -> str:
        return f'<a href="{url}" class="post-link">{text}</a>'

    def thematic_break(self) -> str:
        return '<hr class="post-hr">\n'


md = mistune.create_markdown(renderer=TerminalRenderer())


# ── Post loading ─────────────────────────────────────────────────────────────

def slugify(filename: str) -> str:
    """posts/2026-05-01-my-title.md -> my-title"""
    stem = Path(filename).stem
    # strip leading date prefix YYYY-MM-DD-
    return re.sub(r"^\d{4}-\d{2}-\d{2}-", "", stem)


def load_posts() -> list[dict]:
    posts = []
    for path in sorted(POSTS_DIR.glob("*.md"), reverse=True):
        post = frontmatter.load(path)
        raw_date = post.get("date")
        if isinstance(raw_date, datetime):
            post_date = raw_date.date()
        elif isinstance(raw_date, date):
            post_date = raw_date
        else:
            post_date = date.today()

        posts.append({
            "slug": slugify(path.name),
            "title": post.get("title", path.stem),
            "date": post_date,
            "date_fmt": post_date.strftime("%d %b %Y"),
            "tags": post.get("tags") or [],
            "description": post.get("description") or "",
            "content": md(post.content),
            "reading_time": max(1, len(post.content.split()) // 200),
        })
    return posts


# ── Templates ────────────────────────────────────────────────────────────────

def _post_extra_css() -> str:
    return """
    .post-content { max-width: 68ch; }
    .post-h2 { font-family: var(--font-display); font-size: 1.4rem; font-weight: 600;
               color: var(--text-primary); margin: 2.5rem 0 0.75rem; letter-spacing: -0.02em; }
    .post-h3 { font-family: var(--font-mono); font-size: 1rem; font-weight: 700;
               color: var(--accent); margin: 2rem 0 0.5rem; }
    .post-p  { color: var(--text-secondary); line-height: 1.8; margin-bottom: 1.25rem; font-size: 14px; }
    .post-list { color: var(--text-secondary); line-height: 1.8; margin: 0 0 1.25rem 1.5rem; font-size: 14px; }
    .post-list li { margin-bottom: 0.35rem; }
    .post-link { color: var(--accent-dim); text-decoration: underline; text-decoration-color: var(--border-hover); }
    .post-link:hover { color: var(--accent); }
    .post-hr { border: none; border-top: 1px solid var(--border); margin: 2rem 0; }
    .post-quote { border-left: 2px solid var(--accent); margin: 1.5rem 0; padding: 0.5rem 1.25rem;
                  color: var(--text-muted); font-style: italic; }
    .code-block { position: relative; margin: 1.5rem 0; border: 1px solid var(--border);
                  border-radius: 2px; overflow: hidden; }
    .code-block pre { margin: 0; padding: 1.25rem; overflow-x: auto; }
    .code-block code { font-family: var(--font-mono); font-size: 13px; color: #c8f0c8; line-height: 1.6; }
    .code-lang { position: absolute; top: 0; right: 0; font-size: 10px; font-family: var(--font-mono);
                 color: var(--text-muted); padding: 3px 8px; background: var(--bg-surface);
                 border-bottom: 1px solid var(--border); border-left: 1px solid var(--border); }
    .inline-code { font-family: var(--font-mono); font-size: 12px; color: var(--accent-dim);
                   background: var(--bg-surface); padding: 1px 5px; border-radius: 2px;
                   border: 1px solid var(--border); }
    """


def render_post_page(post: dict, css: str, js: str) -> str:
    tags = "".join(f'<span class="badge badge-topic">{t}</span>' for t in post["tags"])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{post['title']} &mdash; jsmithedin</title>
  <meta name="description" content="{post['description']}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Syne:wght@400;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.19.0/dist/tabler-icons.min.css">
  <style>{css}{_post_extra_css()}</style>
</head>
<body>
  <nav class="site-nav">
    <div class="nav-inner">
      <a href="/" class="nav-brand"><span class="prompt">~/</span>jsmithedin</a>
      <div class="nav-links">
        <a href="/blog" class="nav-link"><i class="ti ti-pencil" aria-hidden="true"></i> blog</a>
        <a href="https://github.com/jsmithedin" class="nav-link" target="_blank" rel="noopener">
          <i class="ti ti-brand-github" aria-hidden="true"></i> github</a>
        <a href="https://www.linkedin.com/in/jamie-smith-engineer" class="nav-link" target="_blank" rel="noopener">
          <i class="ti ti-brand-linkedin" aria-hidden="true"></i> linkedin</a>
      </div>
    </div>
  </nav>

  <main class="site-main">
    <div class="post-header">
      <a href="/blog" class="back-link"><i class="ti ti-arrow-left" aria-hidden="true"></i> all posts</a>
      <p class="header-label"><span class="prompt">$</span> cat ./posts/{post['slug']}.md</p>
      <h1 class="post-title">{post['title']}</h1>
      <div class="post-meta-bar">
        <span class="meta-item"><i class="ti ti-calendar" aria-hidden="true"></i> {post['date_fmt']}</span>
        <span class="meta-item"><i class="ti ti-clock" aria-hidden="true"></i> {post['reading_time']} min read</span>
        <div class="badges">{tags}</div>
      </div>
      <p class="post-description">{post['description']}</p>
    </div>
    <article class="post-content">
      {post['content']}
    </article>
  </main>

  <footer class="site-footer">
    <p class="footer-text">
      <span class="prompt">$</span> <a href="/blog" class="footer-link">← back to posts</a>
    </p>
  </footer>
  <script>{js}</script>
</body>
</html>"""


def render_blog_index(posts: list[dict], css: str, js: str) -> str:
    rows = ""
    for post in posts:
        tags = "".join(f'<span class="badge badge-topic">{t}</span>' for t in post["tags"])
        rows += f"""
        <a href="/blog/{post['slug']}/" class="blog-row">
          <div class="blog-row-main">
            <span class="blog-row-title">{post['title']}</span>
            <span class="blog-row-desc">{post['description']}</span>
          </div>
          <div class="blog-row-meta">
            <div class="badges">{tags}</div>
            <div class="blog-row-stats">
              <span class="meta-item"><i class="ti ti-calendar" aria-hidden="true"></i> {post['date_fmt']}</span>
              <span class="meta-item"><i class="ti ti-clock" aria-hidden="true"></i> {post['reading_time']} min</span>
            </div>
          </div>
        </a>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>blog &mdash; jsmithedin</title>
  <meta name="description" content="Technical writing on AWS, Python, applied AI, and consulting.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Syne:wght@400;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.19.0/dist/tabler-icons.min.css">
  <style>{css}</style>
</head>
<body>
  <nav class="site-nav">
    <div class="nav-inner">
      <a href="/" class="nav-brand"><span class="prompt">~/</span>jsmithedin</a>
      <div class="nav-links">
        <a href="/blog" class="nav-link"><i class="ti ti-pencil" aria-hidden="true"></i> blog</a>
        <a href="https://github.com/jsmithedin" class="nav-link" target="_blank" rel="noopener">
          <i class="ti ti-brand-github" aria-hidden="true"></i> github</a>
        <a href="https://www.linkedin.com/in/jamie-smith-engineer" class="nav-link" target="_blank" rel="noopener">
          <i class="ti ti-brand-linkedin" aria-hidden="true"></i> linkedin</a>
      </div>
    </div>
  </nav>

  <main class="site-main">
    <header class="site-header">
      <div class="header-inner">
        <div class="header-text">
          <p class="header-label"><span class="prompt">$</span> ls -lt ./posts/</p>
          <h1 class="header-title">writing</h1>
          <p class="header-subtitle">AWS, Python, applied AI, consulting. Mostly things I wish I'd found written down.</p>
        </div>
        <div class="header-stats">
          <div class="stat">
            <span class="stat-value">{len(posts)}</span>
            <span class="stat-label">posts</span>
          </div>
        </div>
      </div>
    </header>

    <section class="blog-list" aria-label="Blog posts">
      {rows}
    </section>
  </main>

  <footer class="site-footer">
    <p class="footer-text">
      <span class="prompt">$</span> <a href="/" class="footer-link">← projects</a>
    </p>
  </footer>
  <script>{js}</script>
</body>
</html>"""


# ── Blog CSS additions (appended to main stylesheet) ─────────────────────────

BLOG_CSS = """

/* ── Blog listing ── */
.blog-list {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border);
}

.blog-row {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1.5rem;
  border-bottom: 1px solid var(--border);
  transition: background 0.15s;
  position: relative;
  cursor: pointer;
}

.blog-row::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  width: 2px;
  height: 0;
  background: var(--accent);
  transition: height 0.2s ease;
}

.blog-row:hover { background: var(--bg-card-hover); }
.blog-row:hover::before { height: 100%; }
.blog-row:last-child { border-bottom: none; }

.blog-row-main { display: flex; flex-direction: column; gap: 0.3rem; }

.blog-row-title {
  font-family: var(--font-display);
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.02em;
  transition: color 0.15s;
}

.blog-row:hover .blog-row-title { color: var(--accent); }

.blog-row-desc {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.blog-row-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
  margin-top: 0.25rem;
}

.blog-row-stats {
  display: flex;
  gap: 1rem;
}

/* ── Post page ── */
.post-header {
  padding: 3.5rem 0 2.5rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: 3rem;
  max-width: 68ch;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 1.5rem;
  transition: color 0.15s;
}

.back-link:hover { color: var(--accent); }

.post-title {
  font-family: var(--font-display);
  font-size: clamp(1.6rem, 4vw, 2.4rem);
  font-weight: 600;
  line-height: 1.15;
  letter-spacing: -0.03em;
  color: var(--text-primary);
  margin: 0.75rem 0 1rem;
}

.post-meta-bar {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}

.post-description {
  font-size: 13px;
  color: var(--text-muted);
  font-style: italic;
  line-height: 1.6;
  border-left: 2px solid var(--border-hover);
  padding-left: 1rem;
  margin-top: 1rem;
}
"""


def build_blog(output_dir: Path, css: str, js: str) -> None:
    posts = load_posts()
    if not posts:
        print("No posts found in posts/")
        return

    full_css = css + BLOG_CSS

    # Blog index
    blog_dir = output_dir / "blog"
    blog_dir.mkdir(exist_ok=True)
    (blog_dir / "index.html").write_text(render_blog_index(posts, full_css, js))

    # Individual post pages
    for post in posts:
        post_dir = blog_dir / post["slug"]
        post_dir.mkdir(exist_ok=True)
        (post_dir / "index.html").write_text(render_post_page(post, full_css, js))

    print(f"Built {len(posts)} blog posts → output/blog/")
