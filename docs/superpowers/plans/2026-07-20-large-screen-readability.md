# Large-Screen Readability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make blog post pages scale proportionally on large/high-res screens by replacing fixed `max-width` and `font-size` values with `clamp()` expressions.

**Architecture:** Four targeted single-line edits to `css/style.css` — one for the body font size, three for the shared `1100px` container cap used by nav, main, and footer. No template changes. Post content column (`68ch`) inherits the font-size growth automatically.

**Tech Stack:** CSS `clamp()`, Eleventy 3.x (`npm run serve` to preview)

## Global Constraints

- Do not touch any `.njk` templates — CSS-only change
- Mobile breakpoint (`@media (max-width: 640px)`) must remain unaffected
- Line length stays at `68ch` — do not change `.post-content` or `.post-header` max-width values
- Preserve the terminal/hacker aesthetic — no colour, spacing, or structural changes beyond those listed

---

### Task 1: Apply fluid clamp() sizing

**Files:**
- Modify: `css/style.css`

**Interfaces:**
- Produces: fluid outer container and font size visible in the built site

- [ ] **Step 1: Change body font-size (line 34)**

Find this block in `css/style.css`:

```css
body {
  background: var(--bg);
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: 14px;
  line-height: 1.6;
  min-height: 100vh;
}
```

Change `font-size: 14px` to:

```css
  font-size: clamp(14px, 1vw, 17px);
```

- [ ] **Step 2: Change .nav-inner max-width (around line 52)**

Find:

```css
.nav-inner {
  max-width: 1100px;
```

Change to:

```css
.nav-inner {
  max-width: clamp(1100px, 82vw, 1600px);
```

- [ ] **Step 3: Change .site-main max-width (around line 93)**

Find:

```css
.site-main {
  max-width: 1100px;
```

Change to:

```css
.site-main {
  max-width: clamp(1100px, 82vw, 1600px);
```

- [ ] **Step 4: Change .site-footer max-width (around line 305)**

Find:

```css
.site-footer {
  border-top: 1px solid var(--border);
  padding: 1.5rem 2rem;
  max-width: 1100px;
```

Change to:

```css
.site-footer {
  border-top: 1px solid var(--border);
  padding: 1.5rem 2rem;
  max-width: clamp(1100px, 82vw, 1600px);
```

- [ ] **Step 5: Start the dev server**

```bash
npm run serve
```

Expected: Eleventy starts and site is accessible at `http://localhost:8080`

- [ ] **Step 6: Visually verify at large viewport**

Open a post page (e.g. `http://localhost:8080/blog/` then click any post).

In browser DevTools, open the responsive design view and test these widths:

| Width | Expected container | Expected post column |
|-------|--------------------|----------------------|
| 375px | unchanged (mobile styles apply) | unchanged |
| 1100px | ~1100px | ~571px |
| 1440px | ~1181px | ~585px |
| 1920px | ~1574px | ~650px |
| 2560px | 1600px (capped) | ~694px |

Check that:
- At 375px the mobile layout (`@media (max-width: 640px)`) still stacks correctly
- At 1920px+ the nav, content, and footer all grow together and stay aligned
- No horizontal scrollbar appears at any size
- Post text is legible and the column feels proportionate to the screen (not a narrow strip)

- [ ] **Step 7: Commit**

```bash
git add css/style.css
git commit -m "improve large-screen readability with fluid clamp() sizing"
```
