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
