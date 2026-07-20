---
name: large-screen-readability
description: Improve blog post readability on large/high-res screens using fluid clamp() sizing
metadata:
  type: project
---

# Large-Screen Readability Design

## Problem

On large and high-resolution monitors (1440px+, 4K), the blog post reading experience feels narrow and compacted. The content sits in a small strip at the centre of the screen because:

- The outer container is hard-capped at `max-width: 1100px` with no large-screen scaling
- The post content column is hard-capped at `max-width: 68ch` (~571px at 14px font)
- The base font is a fixed `14px` — small on a high-DPI display
- There are no responsive breakpoints above 640px (only a mobile breakpoint exists)

## Goal

The post reading experience should scale proportionally on large screens — wider container, physically larger text column — without breaking the mobile layout, altering line-length readability, or requiring explicit breakpoints for every screen size.

## Scope

Primary: individual post pages (`_includes/post.njk`, `css/style.css`)
Secondary: the `/blog/` listing page benefits from the same outer container change

Out of scope: font size changes for non-post elements (nav, cards, badges), sidebar/TOC additions, layout restructuring

## Design

Three `clamp()` changes to `css/style.css`. No template changes needed.

### 1. Outer container width

All three layout-level containers share the same `1100px` cap:

```css
/* Before */
.nav-inner    { max-width: 1100px; }
.site-main    { max-width: 1100px; }
.site-footer  { max-width: 1100px; }

/* After */
.nav-inner    { max-width: clamp(1100px, 82vw, 1600px); }
.site-main    { max-width: clamp(1100px, 82vw, 1600px); }
.site-footer  { max-width: clamp(1100px, 82vw, 1600px); }
```

Behaviour:
- ≤1341px viewport: stays at 1100px (unchanged from today)
- 1341px–1951px: scales as 82vw (proportional to screen)
- ≥1951px: caps at 1600px

### 2. Base font size

```css
/* Before */
body { font-size: 14px; }

/* After */
body { font-size: clamp(14px, 1vw, 17px); }
```

Behaviour:
- ≤1400px viewport: stays at 14px (unchanged)
- 1400px–1700px: scales smoothly (e.g. 15.4px at 1540px)
- ≥1700px: caps at 17px (~21% increase)

This is intentionally subtle — it improves physical text size on big screens without making text feel oversized on laptops.

### 3. Post content column

No change to the `ch` values. Since `ch` is relative to the current font size, the post content column widens automatically as the font grows:

```css
/* Unchanged — but benefits from font scaling */
.post-content { max-width: 68ch; }
.post-header  { max-width: 68ch; }
```

Physical effect:
- At 14px font: 68ch ≈ 571px
- At 17px font: 68ch ≈ 694px (~21% wider, matching font growth)

## Expected outcome on large screens

| Screen | Container (before→after) | Post column (before→after) |
|--------|--------------------------|----------------------------|
| 1440px laptop | 1100px → 1181px | 571px → 618px |
| 1920px desktop | 1100px → 1574px | 571px → 680px |
| 2560px 4K | 1100px → 1600px | 571px → 694px |

## Constraints

- Mobile layout (`@media (max-width: 640px)`) is unaffected — `clamp()` minimum matches current values
- Line length in characters stays at 68ch — within the 65–85ch readability sweet spot
- No template changes; all changes are in `css/style.css`
- The existing terminal/hacker aesthetic is preserved
