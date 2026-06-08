# Umami Cloud Analytics Design

**Date:** 2026-06-08
**Status:** Approved

## Summary

Add Umami Cloud analytics to the site by injecting the tracking script into the shared base template.

## Architecture

One line added to `_includes/base.njk` immediately before `</head>`. The Umami script is loaded with `defer` so it has no impact on render performance. No other files change.

## Change

**File:** `_includes/base.njk`

Add before `</head>`:

```html
<script defer src="https://cloud.umami.is/script.js" data-website-id="a43298d8-e577-4567-bf64-8cf6bf0a620b"></script>
```

- `defer` — loads after HTML parsing, non-blocking
- `data-website-id` — Umami Cloud website identifier (public, non-sensitive)
- Placed in `<head>` per Umami's recommendation
- Applies to all pages (homepage, blog listing, individual posts) via the shared `base.njk` layout

## Out of Scope

- Per-environment IDs
- Disabling analytics in local dev
- Custom event tracking
