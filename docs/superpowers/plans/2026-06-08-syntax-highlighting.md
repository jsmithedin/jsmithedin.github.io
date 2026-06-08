# Syntax Highlighting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add GitHub Dark syntax highlighting to fenced code blocks in posts, rendered at build time with no client-side JavaScript.

**Architecture:** Call `highlight.js` directly inside the existing custom `fence` renderer in `.eleventy.js`. The renderer keeps its existing `div.code-block` wrapper structure; it just replaces plain HTML-escaped content with hljs-tokenised HTML. The github-dark theme CSS is appended to `css/style.css` so it continues to be inlined at build time.

**Tech Stack:** highlight.js (npm), Eleventy 3, markdown-it 14

---

## File Map

| File | Action | What changes |
|------|--------|--------------|
| `package.json` | Modify | Add `highlight.js` to dependencies |
| `.eleventy.js` | Modify | `require("highlight.js")` at top; replace fence renderer body |
| `css/style.css` | Modify | Remove `color: #c8f0c8` from `.code-block code`; add `.code-block code.hljs` override; append github-dark theme |

---

### Task 1: Install highlight.js

**Files:**
- Modify: `package.json`

- [ ] **Step 1: Install the package**

```bash
npm install highlight.js
```

- [ ] **Step 2: Verify it installed**

```bash
ls node_modules/highlight.js/styles/github-dark.css
```

Expected: file exists (no error).

- [ ] **Step 3: Commit**

```bash
git add package.json package-lock.json
git commit -m "chore: add highlight.js dependency"
```

---

### Task 2: Update fence renderer in .eleventy.js

**Files:**
- Modify: `.eleventy.js:1-3` (add require) and `.eleventy.js:47-55` (replace fence renderer body)

- [ ] **Step 1: Add the require at the top of the file**

In `.eleventy.js`, add `highlight.js` to the requires at the top. The file currently starts:

```js
const fs = require("fs");
const path = require("path");
const markdownIt = require("markdown-it");
```

Change to:

```js
const fs = require("fs");
const path = require("path");
const markdownIt = require("markdown-it");
const hljs = require("highlight.js");
```

- [ ] **Step 2: Replace the fence renderer body**

Find the existing fence renderer (currently around line 47):

```js
  md.renderer.rules.fence = (tokens, idx) => {
    const lang = (tokens[idx].info || "").trim();
    const langLabel = lang ? `<span class="code-lang">${lang}</span>` : "";
    const escaped = tokens[idx].content
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
    return `<div class="code-block">${langLabel}<pre><code>${escaped}</code></pre></div>\n`;
  };
```

Replace with:

```js
  md.renderer.rules.fence = (tokens, idx) => {
    const lang = (tokens[idx].info || "").trim();
    const langLabel = lang ? `<span class="code-lang">${lang}</span>` : "";
    let highlighted;
    if (lang && hljs.getLanguage(lang)) {
      highlighted = hljs.highlight(tokens[idx].content, { language: lang }).value;
    } else {
      highlighted = hljs.highlightAuto(tokens[idx].content).value;
    }
    return `<div class="code-block">${langLabel}<pre><code class="hljs">${highlighted}</code></pre></div>\n`;
  };
```

- [ ] **Step 3: Build to verify no errors**

```bash
npm run build 2>&1 | tail -5
```

Expected: build completes with no errors (Eleventy prints `[11ty] Wrote N files in X seconds`).

- [ ] **Step 4: Verify hljs tokens are in the output**

```bash
grep -c "hljs-keyword" _site/blog/building-the-house-of-knowledge-bedrock-api/index.html
```

Expected: a number greater than 0 (confirms the Python code blocks are highlighted).

- [ ] **Step 5: Commit**

```bash
git add .eleventy.js
git commit -m "feat: add highlight.js syntax highlighting to code blocks"
```

---

### Task 3: Update CSS

**Files:**
- Modify: `css/style.css:580-585` (`.code-block code` rule) and append github-dark theme

- [ ] **Step 1: Remove the hardcoded color from `.code-block code`**

Find this rule in `css/style.css` (around line 580):

```css
.code-block code {
  font-family: var(--font-mono);
  font-size: 13px;
  color: #c8f0c8;
  line-height: 1.6;
}
```

Change to:

```css
.code-block code {
  font-family: var(--font-mono);
  font-size: 13px;
  line-height: 1.6;
}

.code-block code.hljs {
  background: var(--bg-surface);
}
```

- [ ] **Step 2: Append the github-dark theme CSS**

```bash
echo "" >> css/style.css
echo "/* ── Syntax highlighting (highlight.js github-dark) ── */" >> css/style.css
cat node_modules/highlight.js/styles/github-dark.css >> css/style.css
```

- [ ] **Step 3: Build to verify no errors**

```bash
npm run build 2>&1 | tail -5
```

Expected: build completes with no errors.

- [ ] **Step 4: Verify the theme CSS is in the inlined output**

```bash
grep -c "hljs-keyword" _site/blog/building-the-house-of-knowledge-bedrock-api/index.html
grep "hljs-keyword" _site/index.html | head -1
```

First command: confirm token spans exist in post output (count > 0).
Second command: confirm the theme CSS is inlined in the homepage `<style>` block (should show the `.hljs-keyword` rule).

- [ ] **Step 5: Commit**

```bash
git add css/style.css
git commit -m "style: apply github-dark syntax highlighting theme"
```

---

### Task 4: Smoke-test the live site

**Files:** (none — verification only)

- [ ] **Step 1: Start the dev server**

```bash
npm run serve
```

Expected: Eleventy starts a local server, prints something like `[11ty] Server at http://localhost:8080/`.

- [ ] **Step 2: Check a post with code blocks**

Open `http://localhost:8080/blog/building-the-house-of-knowledge-bedrock-api/` in a browser.

Verify:
- Code blocks show coloured tokens (keywords in red-orange, strings in light blue, comments in grey).
- The language label (e.g. `python`) still appears in the top-right corner of each block.
- Inline code (e.g. `boto3.client(...)`) is unchanged — still uses the site's `--accent-dim` green.

- [ ] **Step 3: Check a block with no language hint**

In your browser, find a code block that has no language specified (plain ` ``` ` fencing). Verify it renders without errors — content displays as plain text, no broken HTML.

- [ ] **Step 4: Stop the server**

`Ctrl+C`
