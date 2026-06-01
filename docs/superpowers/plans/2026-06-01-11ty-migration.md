# 11ty Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate jsmithedin.github.io from a custom Python SSG (`build.py` + `blog.py`) to Eleventy (11ty) with Nunjucks templates, preserving the dark terminal theme exactly and adding a 3-post preview section above the repos grid on the homepage.

**Architecture:** 11ty runs with `input: "."` at the project root. `_data/repos.js` fetches GitHub repos async using `@11ty/eleventy-fetch` (24h cache). `_includes/base.njk` is the shared HTML shell; all pages extend it. Posts in `posts/*.md` use layout chaining: `posts/posts.11tydata.js` assigns `layout: post.njk` and a computed permalink; `post.njk` in turn sets `layout: base.njk`. OG/Twitter tags are rendered in `base.njk` conditionally based on whether `tags` contains `"post"`. A custom `markdown-it` renderer preserves the terminal-style `code-block`, `post-p`, `post-h2` etc. class output from the original Python `TerminalRenderer`.

**Tech Stack:** Node 20, `@11ty/eleventy` v3, `@11ty/eleventy-fetch` v5, `markdown-it`, Nunjucks

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Create | `package.json` | npm project, build scripts |
| Create | `.eleventy.js` | 11ty config, filters, shortcodes, markdown-it |
| Create | `.eleventyignore` | exclude docs/, README.md from processing |
| Create | `_data/repos.js` | async GitHub API fetch with 24h cache |
| Create | `_data/build.js` | build timestamp for footer |
| Create | `_includes/base.njk` | HTML shell: head, OG tags, nav, footer, CSS/JS inline |
| Create | `_includes/post.njk` | post page layout (chains to base.njk) |
| Create | `index.njk` | homepage: 3 post preview + repos grid |
| Create | `blog.njk` | blog listing at /blog/ |
| Create | `posts/posts.11tydata.js` | directory data: layout, tags, computed permalink |
| Modify | `css/style.css` | append blog, post, section-heading CSS rules |
| Modify | `.github/workflows/deploy.yml` | swap Python for Node 20 + 11ty |
| Modify | `.gitignore` | add node_modules/, _site/, .cache/ |
| Delete | `build.py`, `blog.py`, `requirements.txt` | replaced by 11ty |

---

### Task 1: Scaffold the 11ty project

**Files:**
- Create: `package.json`
- Create: `.eleventy.js`
- Create: `.eleventyignore`
- Modify: `.gitignore`

- [ ] **Step 1: Create `package.json`**

```json
{
  "name": "jsmithedin-site",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "build": "eleventy",
    "serve": "eleventy --serve"
  },
  "dependencies": {
    "@11ty/eleventy": "^3.0.0",
    "@11ty/eleventy-fetch": "^5.0.0",
    "markdown-it": "^14.0.0"
  }
}
```

- [ ] **Step 2: Install dependencies**

```bash
npm install
```

Expected: `node_modules/` created, `package-lock.json` created, no errors.

- [ ] **Step 3: Create `.eleventy.js`**

```js
const fs = require("fs");
const markdownIt = require("markdown-it");

const LANG_MAP = {
  Python: "lang-python",
  TypeScript: "lang-ts",
  JavaScript: "lang-js",
  Rust: "lang-rust",
  Go: "lang-go",
  Shell: "lang-shell",
  HCL: "lang-hcl",
};

module.exports = function (eleventyConfig) {
  eleventyConfig.addPassthroughCopy("css");
  eleventyConfig.addPassthroughCopy("js");

  // Inline file contents into <style> and <script> tags
  eleventyConfig.addShortcode("inlineCSS", () => fs.readFileSync("css/style.css", "utf8"));
  eleventyConfig.addShortcode("inlineJS", () => fs.readFileSync("js/main.js", "utf8"));

  // Filters
  eleventyConfig.addFilter("limit", (arr, n) => (arr || []).slice(0, n));
  eleventyConfig.addFilter("isoDate", (date) => new Date(date).toISOString());
  eleventyConfig.addFilter("formatDate", (date) =>
    new Date(date).toLocaleDateString("en-GB", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    })
  );
  eleventyConfig.addFilter("readingTime", (content) => {
    const text = (content || "").replace(/<[^>]+>/g, "");
    return Math.max(1, Math.round(text.split(/\s+/).length / 200));
  });
  eleventyConfig.addFilter("languageClass", (lang) => LANG_MAP[lang] || "lang-other");
  // Exclude the internal "post" collection tag from displayed badge lists
  eleventyConfig.addFilter("displayTags", (tags) =>
    (tags || []).filter((t) => t !== "post")
  );

  // Custom markdown-it renderer preserving terminal aesthetic class names
  const md = markdownIt({ html: false, linkify: true, typographer: true });

  md.renderer.rules.fence = (tokens, idx) => {
    const lang = (tokens[idx].info || "").trim();
    const langLabel = lang ? `<span class="code-lang">${lang}</span>` : "";
    const escaped = tokens[idx].content
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
    return `<div class="code-block">${langLabel}<pre><code>${escaped}</code></pre></div>\n`;
  };

  md.renderer.rules.code_inline = (tokens, idx) =>
    `<code class="inline-code">${tokens[idx].content}</code>`;

  md.renderer.rules.paragraph_open = (tokens, idx, options, env, self) => {
    tokens[idx].attrSet("class", "post-p");
    return self.renderToken(tokens, idx, options);
  };

  md.renderer.rules.heading_open = (tokens, idx, options, env, self) => {
    tokens[idx].attrSet("class", `post-${tokens[idx].tag}`);
    return self.renderToken(tokens, idx, options);
  };

  md.renderer.rules.blockquote_open = (tokens, idx, options, env, self) => {
    tokens[idx].attrSet("class", "post-quote");
    return self.renderToken(tokens, idx, options);
  };

  md.renderer.rules.bullet_list_open = (tokens, idx, options, env, self) => {
    tokens[idx].attrSet("class", "post-list");
    return self.renderToken(tokens, idx, options);
  };

  md.renderer.rules.ordered_list_open = (tokens, idx, options, env, self) => {
    tokens[idx].attrSet("class", "post-list");
    return self.renderToken(tokens, idx, options);
  };

  md.renderer.rules.link_open = (tokens, idx, options, env, self) => {
    tokens[idx].attrSet("class", "post-link");
    return self.renderToken(tokens, idx, options);
  };

  md.renderer.rules.hr = () => '<hr class="post-hr">\n';

  eleventyConfig.setLibrary("md", md);

  return {
    dir: {
      input: ".",
      output: "_site",
      includes: "_includes",
      data: "_data",
    },
    markdownTemplateEngine: "njk",
    htmlTemplateEngine: "njk",
  };
};
```

- [ ] **Step 4: Create `.eleventyignore`**

```
docs/
README.md
.superpowers/
{.github/
```

- [ ] **Step 5: Append to `.gitignore`** (create it first if it doesn't exist)

Add these lines at the bottom:

```
node_modules/
_site/
.cache/
```

- [ ] **Step 6: Verify 11ty is installed**

```bash
npx eleventy --version
```

Expected: prints `3.x.x` — no errors.

- [ ] **Step 7: Commit**

```bash
git add package.json package-lock.json .eleventy.js .eleventyignore .gitignore
git commit -m "feat: scaffold 11ty project with config, filters, and markdown renderer"
```

---

### Task 2: Add data layer

**Files:**
- Create: `_data/repos.js`
- Create: `_data/build.js`

- [ ] **Step 1: Create `_data/repos.js`**

```js
const EleventyFetch = require("@11ty/eleventy-fetch");

const USERNAME = "jsmithedin";

function formatDate(iso) {
  return new Date(iso).toLocaleDateString("en-GB", {
    month: "short",
    year: "numeric",
  });
}

module.exports = async function () {
  const token = process.env.GITHUB_TOKEN;
  const headers = { Accept: "application/vnd.github+json" };
  if (token) headers["Authorization"] = `token ${token}`;

  const repos = [];
  let page = 1;

  while (true) {
    const url =
      `https://api.github.com/users/${USERNAME}/repos` +
      `?page=${page}&per_page=100&sort=updated&direction=desc`;
    const batch = await EleventyFetch(url, {
      duration: "1d",
      type: "json",
      fetchOptions: { headers },
    });
    if (!batch || !batch.length) break;
    repos.push(...batch);
    page++;
  }

  return repos
    .filter((r) => !r.fork)
    .map((r) => ({
      name: r.name,
      description: r.description || "",
      html_url: r.html_url,
      homepage: r.homepage || "",
      language: r.language || null,
      stargazers_count: r.stargazers_count || 0,
      updated: formatDate(r.updated_at),
      topics: (r.topics || []).slice(0, 5),
    }));
};
```

- [ ] **Step 2: Create `_data/build.js`**

```js
module.exports = {
  time: new Date().toISOString().replace("T", " ").slice(0, 16) + " UTC",
};
```

- [ ] **Step 3: Verify the data files load without crashing**

```bash
GITHUB_TOKEN="" npx eleventy --dryrun 2>&1 | head -30
```

Expected: 11ty processes files and reports stats — no `Cannot find module` or unhandled promise rejection errors. If you have a real token exported, use it to see repo data flow through.

- [ ] **Step 4: Commit**

```bash
git add _data/repos.js _data/build.js
git commit -m "feat: add 11ty data files for GitHub repos and build timestamp"
```

---

### Task 3: Create the shared base layout

**Files:**
- Create: `_includes/base.njk`

- [ ] **Step 1: Create `_includes/base.njk`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ title or "jsmithedin — projects" }}</title>
  <meta name="description" content="{{ description or 'Jamie Smith — Principal Engineer. Projects and open source work.' }}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Syne:wght@400;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.19.0/dist/tabler-icons.min.css">
  <meta property="og:title" content="{{ title or 'jsmithedin' }}">
  <meta property="og:description" content="{{ description or 'Principal engineer. AWS &amp; Python. Applied AI in energy &amp; utilities.' }}">
  <meta property="og:type" content="{% if tags and 'post' in tags %}article{% else %}website{% endif %}">
  <meta property="og:url" content="https://jamielab.uk{{ page.url }}">
  {% if tags and 'post' in tags %}
  <meta property="article:published_time" content="{{ date | isoDate }}">
  {% endif %}
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{{ title or 'jsmithedin' }}">
  <meta name="twitter:description" content="{{ description or 'Principal engineer. AWS &amp; Python. Applied AI in energy &amp; utilities.' }}">
  <style>{% inlineCSS %}</style>
</head>
<body>
  <nav class="site-nav">
    <div class="nav-inner">
      <a href="/" class="nav-brand"><span class="prompt">~/</span>jsmithedin</a>
      <div class="nav-links">
        <a href="/blog/" class="nav-link"><i class="ti ti-pencil" aria-hidden="true"></i> blog</a>
        <a href="https://github.com/jsmithedin" class="nav-link" target="_blank" rel="noopener">
          <i class="ti ti-brand-github" aria-hidden="true"></i> github</a>
        <a href="https://www.linkedin.com/in/jamie-smith-engineer" class="nav-link" target="_blank" rel="noopener">
          <i class="ti ti-brand-linkedin" aria-hidden="true"></i> linkedin</a>
      </div>
    </div>
  </nav>
  {{ content | safe }}
  <footer class="site-footer">
    <p class="footer-text">
      <span class="prompt">$</span> built {{ build.time }} &mdash;
      <a href="https://github.com/jsmithedin/jsmithedin.github.io" class="footer-link">source</a>
    </p>
  </footer>
  <script>{% inlineJS %}</script>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add _includes/base.njk
git commit -m "feat: add base.njk shared layout with nav, footer, and OG meta tags"
```

---

### Task 4: Create the homepage

**Files:**
- Create: `index.njk`

- [ ] **Step 1: Create `index.njk`**

```nunjucks
---
layout: base.njk
permalink: /
title: jsmithedin — projects
description: Jamie Smith — Principal Engineer. Projects and open source work.
---

<main class="site-main">
  <header class="site-header">
    <div class="header-inner">
      <div class="header-text">
        <p class="header-label"><span class="prompt">$</span> ls --sort=date ./</p>
        <h1 class="header-title">jsmithedin</h1>
        <p class="header-subtitle">Principal engineer. AWS &amp; Python. Applied AI in energy &amp; utilities.</p>
      </div>
      <div class="header-stats">
        <div class="stat">
          <span class="stat-value">{{ collections.post | length }}</span>
          <span class="stat-label">posts</span>
        </div>
        <div class="stat-divider">/</div>
        <div class="stat">
          <span class="stat-value">{{ repos | length }}</span>
          <span class="stat-label">repos</span>
        </div>
        <div class="stat-divider">/</div>
        <div class="stat">
          <span class="stat-value">Edinburgh</span>
          <span class="stat-label">location</span>
        </div>
      </div>
    </div>
  </header>

  <section class="repos-section">
    <div class="section-heading">
      <span class="section-label"><span class="prompt">$</span> tail -3 ./posts/</span>
      <a href="/blog/" class="section-link"><i class="ti ti-arrow-right" aria-hidden="true"></i> all posts</a>
    </div>
    <div class="blog-preview">
      {% for post in collections.post | reverse | limit(3) %}
      <a href="{{ post.url }}" class="blog-row">
        <div class="blog-row-inner">
          <span class="blog-row-title">{{ post.data.title }}</span>
          <div class="blog-row-meta">
            <span class="meta-item"><i class="ti ti-calendar" aria-hidden="true"></i> {{ post.data.date | formatDate }}</span>
            <span class="meta-item"><i class="ti ti-clock" aria-hidden="true"></i> {{ post.content | readingTime }} min</span>
          </div>
        </div>
        <span class="blog-row-desc">{{ post.data.description }}</span>
        <div class="badges">
          {% for tag in post.data.tags | displayTags %}
          <span class="badge badge-topic">{{ tag }}</span>
          {% endfor %}
        </div>
      </a>
      {% endfor %}
    </div>
  </section>

  <section class="repos-section">
    <div class="section-heading">
      <span class="section-label"><span class="prompt">$</span> ls --sort=date ./projects/</span>
    </div>
    <div class="repo-grid" aria-label="Project repositories">
      {% for repo in repos %}
      <article class="repo-card">
        <div class="card-header">
          <a href="{{ repo.html_url }}" class="card-title" target="_blank" rel="noopener">{{ repo.name }}</a>
          <div class="card-links">
            {% if repo.homepage %}
            <a href="{{ repo.homepage }}" class="card-link external" target="_blank" rel="noopener">
              <i class="ti ti-external-link" aria-hidden="true"></i> live</a>
            {% endif %}
            <a href="{{ repo.html_url }}" class="card-link" target="_blank" rel="noopener">
              <i class="ti ti-brand-github" aria-hidden="true"></i> source</a>
          </div>
        </div>
        <p class="card-desc">{{ repo.description }}</p>
        <div class="card-footer">
          <div class="badges">
            {% if repo.language %}
            <span class="badge {{ repo.language | languageClass }}">{{ repo.language }}</span>
            {% endif %}
            {% for topic in repo.topics %}
            <span class="badge badge-topic">{{ topic }}</span>
            {% endfor %}
          </div>
          <div class="card-meta">
            {% if repo.stargazers_count %}
            <span class="meta-item"><i class="ti ti-star" aria-hidden="true"></i> {{ repo.stargazers_count }}</span>
            {% endif %}
            <span class="meta-item"><i class="ti ti-clock" aria-hidden="true"></i> {{ repo.updated }}</span>
          </div>
        </div>
      </article>
      {% endfor %}
    </div>
  </section>
</main>
```

- [ ] **Step 2: Build and verify**

```bash
npx eleventy 2>&1 | tail -5
```

Expected: `Wrote N files in Xs` — no errors.

```bash
grep -c "repo-card" _site/index.html
```

Expected: > 0

```bash
grep -c "blog-row" _site/index.html
```

Expected: > 0

- [ ] **Step 3: Commit**

```bash
git add index.njk
git commit -m "feat: add homepage with blog preview section and repos grid"
```

---

### Task 5: Create the blog listing page

**Files:**
- Create: `blog.njk`

- [ ] **Step 1: Create `blog.njk`**

```nunjucks
---
layout: base.njk
permalink: /blog/
title: blog — jsmithedin
description: Technical writing on AWS, Python, applied AI, and consulting.
---

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
          <span class="stat-value">{{ collections.post | length }}</span>
          <span class="stat-label">posts</span>
        </div>
      </div>
    </div>
  </header>

  <section class="blog-list" aria-label="Blog posts">
    {% for post in collections.post | reverse %}
    <a href="{{ post.url }}" class="blog-row">
      <div class="blog-row-main">
        <span class="blog-row-title">{{ post.data.title }}</span>
        <span class="blog-row-desc">{{ post.data.description }}</span>
      </div>
      <div class="blog-row-meta">
        <div class="badges">
          {% for tag in post.data.tags | displayTags %}
          <span class="badge badge-topic">{{ tag }}</span>
          {% endfor %}
        </div>
        <div class="blog-row-stats">
          <span class="meta-item"><i class="ti ti-calendar" aria-hidden="true"></i> {{ post.data.date | formatDate }}</span>
          <span class="meta-item"><i class="ti ti-clock" aria-hidden="true"></i> {{ post.content | readingTime }} min</span>
        </div>
      </div>
    </a>
    {% endfor %}
  </section>
</main>
```

- [ ] **Step 2: Build and verify**

```bash
npx eleventy 2>&1 | tail -5
```

```bash
ls _site/blog/
```

Expected: `index.html` present (post subdirectories won't exist until Task 6).

```bash
grep -c "blog-row" _site/blog/index.html
```

Expected: > 0

- [ ] **Step 3: Commit**

```bash
git add blog.njk
git commit -m "feat: add blog listing page at /blog/"
```

---

### Task 6: Set up posts with directory data and post layout

**Files:**
- Create: `posts/posts.11tydata.js`
- Create: `_includes/post.njk`

- [ ] **Step 1: Create `posts/posts.11tydata.js`**

```js
module.exports = {
  layout: "post.njk",
  tags: "post",
  eleventyComputed: {
    permalink: (data) =>
      `/blog/${data.page.fileSlug.replace(/^\d{4}-\d{2}-\d{2}-/, "")}/`,
    slug: (data) => data.page.fileSlug.replace(/^\d{4}-\d{2}-\d{2}-/, ""),
  },
};
```

- [ ] **Step 2: Create `_includes/post.njk`**

```html
---
layout: base.njk
---
<main class="site-main">
  <div class="post-header">
    <a href="/blog/" class="back-link"><i class="ti ti-arrow-left" aria-hidden="true"></i> all posts</a>
    <p class="header-label"><span class="prompt">$</span> cat ./posts/{{ slug }}.md</p>
    <h1 class="post-title">{{ title }}</h1>
    <div class="post-meta-bar">
      <span class="meta-item"><i class="ti ti-calendar" aria-hidden="true"></i> {{ date | formatDate }}</span>
      <span class="meta-item"><i class="ti ti-clock" aria-hidden="true"></i> {{ content | readingTime }} min read</span>
      <div class="badges">
        {% for tag in tags | displayTags %}
        <span class="badge badge-topic">{{ tag }}</span>
        {% endfor %}
      </div>
    </div>
    <p class="post-description">{{ description }}</p>
  </div>
  <article class="post-content">
    {{ content | safe }}
  </article>
</main>
```

- [ ] **Step 3: Build and verify**

```bash
npx eleventy 2>&1 | tail -5
```

```bash
ls _site/blog/
```

Expected: `index.html` plus `terraform-s3-locking/`, `obsidian-consulting-kb/`, `fail-fast-iteration/` subdirectories.

```bash
grep "og:type" _site/blog/terraform-s3-locking/index.html
```

Expected: `<meta property="og:type" content="article">`

```bash
grep "article:published_time" _site/blog/terraform-s3-locking/index.html
```

Expected: line containing `2026-05-01T00:00:00.000Z`

```bash
grep "og:type" _site/index.html
```

Expected: `<meta property="og:type" content="website">`

```bash
grep -c "post-content" _site/blog/terraform-s3-locking/index.html
```

Expected: 1

- [ ] **Step 4: Commit**

```bash
git add posts/posts.11tydata.js _includes/post.njk
git commit -m "feat: add post layout with OG tags and computed /blog/:slug/ permalinks"
```

---

### Task 7: Append blog and post CSS to stylesheet

**Files:**
- Modify: `css/style.css`

- [ ] **Step 1: Append to `css/style.css`**

Open `css/style.css` and add the following at the very end of the file:

```css

/* ── Section headings (homepage) ── */
.repos-section { margin-bottom: 3rem; }

.section-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--border);
}

.section-label {
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.section-link {
  font-size: 11px;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  gap: 4px;
  transition: color 0.15s;
}

.section-link:hover { color: var(--accent); }

/* ── Blog listing ── */
.blog-preview {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border);
}

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

.blog-row-inner {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 1rem;
}

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

.blog-row-stats { display: flex; gap: 1rem; }

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

/* ── Post content ── */
.post-content { max-width: 68ch; }

.post-h2 {
  font-family: var(--font-display);
  font-size: 1.4rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 2.5rem 0 0.75rem;
  letter-spacing: -0.02em;
}

.post-h3 {
  font-family: var(--font-mono);
  font-size: 1rem;
  font-weight: 700;
  color: var(--accent);
  margin: 2rem 0 0.5rem;
}

.post-p {
  color: var(--text-secondary);
  line-height: 1.8;
  margin-bottom: 1.25rem;
  font-size: 14px;
}

.post-list {
  color: var(--text-secondary);
  line-height: 1.8;
  margin: 0 0 1.25rem 1.5rem;
  font-size: 14px;
}

.post-list li { margin-bottom: 0.35rem; }

.post-link {
  color: var(--accent-dim);
  text-decoration: underline;
  text-decoration-color: var(--border-hover);
}

.post-link:hover { color: var(--accent); }

.post-hr {
  border: none;
  border-top: 1px solid var(--border);
  margin: 2rem 0;
}

.post-quote {
  border-left: 2px solid var(--accent);
  margin: 1.5rem 0;
  padding: 0.5rem 1.25rem;
  color: var(--text-muted);
  font-style: italic;
}

.code-block {
  position: relative;
  margin: 1.5rem 0;
  border: 1px solid var(--border);
  border-radius: 2px;
  overflow: hidden;
}

.code-block pre { margin: 0; padding: 1.25rem; overflow-x: auto; }

.code-block code {
  font-family: var(--font-mono);
  font-size: 13px;
  color: #c8f0c8;
  line-height: 1.6;
}

.code-lang {
  position: absolute;
  top: 0;
  right: 0;
  font-size: 10px;
  font-family: var(--font-mono);
  color: var(--text-muted);
  padding: 3px 8px;
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border);
  border-left: 1px solid var(--border);
}

.inline-code {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--accent-dim);
  background: var(--bg-surface);
  padding: 1px 5px;
  border-radius: 2px;
  border: 1px solid var(--border);
}
```

- [ ] **Step 2: Build and verify code block rendering**

```bash
npx eleventy 2>&1 | tail -5
```

```bash
grep "code-block" _site/blog/terraform-s3-locking/index.html | wc -l
```

Expected: > 0 (the Terraform post has HCL code blocks)

```bash
grep "inline-code" _site/blog/terraform-s3-locking/index.html | wc -l
```

Expected: > 0 (post uses inline code)

- [ ] **Step 3: Commit**

```bash
git add css/style.css
git commit -m "feat: append blog listing and post content CSS to stylesheet"
```

---

### Task 8: Update the CI workflow

**Files:**
- Modify: `.github/workflows/deploy.yml`

- [ ] **Step 1: Replace `.github/workflows/deploy.yml` with**

```yaml
name: Build and deploy portfolio

on:
  schedule:
    - cron: "0 6 * * 1"
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: write

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"

      - name: Install dependencies
        run: npm ci

      - name: Bust fetch cache on scheduled runs
        if: github.event_name == 'schedule'
        run: rm -rf .cache

      - name: Build site
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: npx eleventy

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./_site
          cname: jamielab.uk
```

- [ ] **Step 2: Verify the file**

```bash
grep "setup-node" .github/workflows/deploy.yml
grep "publish_dir" .github/workflows/deploy.yml
grep "Bust fetch cache" .github/workflows/deploy.yml
```

Expected: each grep returns a matching line.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/deploy.yml
git commit -m "ci: switch build from Python to Node 20 + 11ty"
```

---

### Task 9: Remove Python files and final end-to-end verification

**Files:**
- Delete: `build.py`
- Delete: `blog.py`
- Delete: `requirements.txt`

- [ ] **Step 1: Remove Python build files**

```bash
git rm build.py blog.py requirements.txt
```

- [ ] **Step 2: Final full build**

```bash
npx eleventy 2>&1
```

Expected: finishes with `Wrote N files in Xs` — no errors.

- [ ] **Step 3: Verify all expected output paths exist**

```bash
ls _site/index.html _site/blog/index.html \
   _site/blog/terraform-s3-locking/index.html \
   _site/blog/obsidian-consulting-kb/index.html \
   _site/blog/fail-fast-iteration/index.html
```

Expected: all five files present — no "No such file or directory" errors.

- [ ] **Step 4: Verify homepage has both sections**

```bash
grep -c "blog-row" _site/index.html
```

Expected: > 0

```bash
grep -c "repo-card" _site/index.html
```

Expected: > 0

- [ ] **Step 5: Verify OG tags on post vs non-post pages**

```bash
grep "og:type" _site/index.html
```

Expected: `content="website"`

```bash
grep "og:type" _site/blog/terraform-s3-locking/index.html
```

Expected: `content="article"`

- [ ] **Step 6: Commit removal**

```bash
git commit -m "chore: remove Python build scripts, replaced by 11ty"
```
