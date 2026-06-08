# Umami Cloud Analytics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Umami Cloud analytics tracking to all pages of the site.

**Architecture:** Add a single `<script defer>` tag to `_includes/base.njk` immediately before `</head>`. All pages use this shared layout, so one change covers the entire site. No new dependencies, no build changes.

**Tech Stack:** Nunjucks (Eleventy template), Umami Cloud CDN

---

## File Map

| File | Action | What changes |
|------|--------|--------------|
| `_includes/base.njk` | Modify | Add Umami script tag before `</head>` |

---

### Task 1: Add Umami script tag to base template

**Files:**
- Modify: `_includes/base.njk:28` (line immediately before `</head>`)

- [ ] **Step 1: Add the script tag**

Open `_includes/base.njk`. Find the `<style>` line (line 28):

```html
  <style>{% inlineCSS %}</style>
</head>
```

Change to:

```html
  <style>{% inlineCSS %}</style>
  <script defer src="https://cloud.umami.is/script.js" data-website-id="a43298d8-e577-4567-bf64-8cf6bf0a620b"></script>
</head>
```

- [ ] **Step 2: Build to verify no errors**

```bash
npm run build 2>&1 | tail -5
```

Expected: `[11ty] Copied 5 Wrote 4 files in X seconds (v3.1.5)` — no errors.

- [ ] **Step 3: Verify the script tag appears in built output**

```bash
grep -r "umami" _site/ | head -5
```

Expected: every HTML file in `_site/` shows the Umami script tag. You should see output like:

```
_site/index.html:  <script defer src="https://cloud.umami.is/script.js" data-website-id="a43298d8-e577-4567-bf64-8cf6bf0a620b"></script>
_site/blog/index.html:  <script defer src="https://cloud.umami.is/script.js" ...
_site/blog/building-the-house-of-knowledge-bedrock-api/index.html:  <script defer ...
```

- [ ] **Step 4: Commit**

```bash
git add _includes/base.njk
git commit -m "feat: add Umami Cloud analytics"
```
