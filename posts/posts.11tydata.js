module.exports = {
  layout: "post.njk",
  tags: "post",
  eleventyComputed: {
    permalink: (data) =>
      `/blog/${data.page.fileSlug.replace(/^\d{4}-\d{2}-\d{2}-/, "")}/`,
    slug: (data) => data.page.fileSlug.replace(/^\d{4}-\d{2}-\d{2}-/, ""),
  },
};
