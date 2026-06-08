# Syntax Highlighting for Code Blocks

**Date:** 2026-06-08
**Status:** Approved

## Summary

Add language-specific syntax highlighting to fenced code blocks in posts. Use the GitHub Dark theme from highlight.js, rendered at build time. No runtime JavaScript. Inline code blocks are unchanged.

## Architecture

`highlight.js` is called directly inside the existing custom `fence` renderer in `.eleventy.js`. This keeps the existing `div.code-block` wrapper and `span.code-lang` label structure intact while replacing the current plain HTML-escaped code content with hljs-tokenised HTML.

Three files change:

| File | Change |
|------|--------|
| `package.json` | Add `highlight.js` dependency |
| `.eleventy.js` | Update `fence` renderer to call `hljs.highlight()` / `hljs.highlightAuto()` |
| `css/style.css` | Remove hardcoded `color: #c8f0c8` from `.code-block code`; append github-dark theme CSS; add background override |

No template changes. No new shortcodes. No CDN dependencies.

## Components

### `.eleventy.js` — fence renderer

Replace the current renderer (which only HTML-escapes content) with one that calls `hljs.highlight()`:

```js
const hljs = require("highlight.js");

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

- `hljs.highlight()` is used when the fenced block declares a language that hljs recognises.
- `hljs.highlightAuto()` is the fallback for unknown or unspecified languages — returns plain text cleanly.
- The `hljs` class on `<code>` is required for the theme's base styles to apply.

### `css/style.css` — theme integration

Two targeted changes to the existing code block styles:

1. Remove `color: #c8f0c8` from `.code-block code` — hljs token classes control colors.
2. Add `.code-block code.hljs { background: var(--bg-surface); }` — keeps the block background at `#141414` (site's surface color) rather than hljs's default `#0d1117`.

Append the full `highlight.js` github-dark theme CSS under a comment block at the end of the file. This keeps the site's inline-everything approach (CSS is inlined at build time via the `inlineCSS` shortcode).

## Data Flow

```
markdown-it parses fenced block
  → fence renderer extracts language hint
  → hljs.highlight(content, { language }) OR hljs.highlightAuto(content)
  → returns HTML string with <span class="hljs-*"> tokens
  → renderer wraps in <div class="code-block"> + <span class="code-lang">
  → static HTML written to _site/
  → github-dark CSS (inlined) colours the tokens in the browser
```

## Theming

- **Theme:** highlight.js `github-dark` — the standard theme from the `highlight.js` npm package, located at `node_modules/highlight.js/styles/github-dark.css`.
- **Token colours (key):** keywords `#ff7b72`, strings `#a5d6ff`, types/builtins `#79c0ff`, function names `#d2a8ff`, numbers `#79c0ff`, comments `#8b949e`.
- **Background override:** `.code-block code.hljs { background: var(--bg-surface); }` — overrides the theme's `#0d1117` to match the site's `#141414`.
- **Inline code** (`.inline-code`): unchanged.

## Out of Scope

- Line numbers
- Copy-to-clipboard button
- Diff highlighting
- Light theme / theme toggle
