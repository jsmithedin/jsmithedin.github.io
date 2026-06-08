const fs = require("fs");
const path = require("path");
const markdownIt = require("markdown-it");
const hljs = require("highlight.js");

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
  eleventyConfig.addPassthroughCopy("images");

  // Inline file contents into <style> and <script> tags
  eleventyConfig.addShortcode("inlineCSS", () => fs.readFileSync(path.join(__dirname, "css/style.css"), "utf8"));
  eleventyConfig.addShortcode("inlineJS", () => fs.readFileSync(path.join(__dirname, "js/main.js"), "utf8"));

  // Filters
  eleventyConfig.addFilter("limit", (arr, n) => (arr || []).slice(0, n));
  eleventyConfig.addFilter("isoDate", (date) => date ? new Date(date).toISOString() : "");
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
    const escapedLang = lang.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    const langLabel = lang ? `<span class="code-lang">${escapedLang}</span>` : "";
    let highlighted;
    if (lang && hljs.getLanguage(lang)) {
      highlighted = hljs.highlight(tokens[idx].content, { language: lang, ignoreIllegals: true }).value;
    } else {
      highlighted = tokens[idx].content
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    }
    return `<div class="code-block">${langLabel}<pre><code class="hljs">${highlighted}</code></pre></div>\n`;
  };

  md.renderer.rules.code_inline = (tokens, idx) => {
    const escaped = tokens[idx].content
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
    return `<code class="inline-code">${escaped}</code>`;
  };

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
