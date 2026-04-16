require('dotenv').config();
const axios = require('axios');

const MAX_REPOS = 100;

async function fetchYearContributions(username, token, year) {
  const from = `${year}-01-01T00:00:00Z`;
  const to   = `${year}-12-31T23:59:59Z`;

  const { data } = await axios.post(
    'https://api.github.com/graphql',
    {
      query: `query {
        user(login: ${JSON.stringify(username)}) {
          contributionsCollection(from: "${from}", to: "${to}") {
            commitContributionsByRepository(maxRepositories: ${MAX_REPOS}) {
              contributions { totalCount }
              repository {
                name
                nameWithOwner
                owner { avatarUrl }
              }
            }
          }
        }
      }`,
    },
    { headers: { Authorization: `token ${token}` } },
  );

  const list =
    data.data.user.contributionsCollection.commitContributionsByRepository;

  return list.map(({ contributions, repository }) => ({
    nameWithOwner: repository.nameWithOwner,
    name:          repository.name,
    avatarUrl:     repository.owner.avatarUrl,
    count:         contributions.totalCount,
  }));
}

async function fetchStats(username, limit = 10) {
  const token = process.env.GITHUB_PERSONAL_ACCESS_TOKEN;

  const { data } = await axios.post(
    'https://api.github.com/graphql',
    {
      query: `query {
        user(login: "${username}") {
          name
          contributionsCollection { contributionYears }
        }
      }`,
    },
    { headers: { Authorization: `token ${token}` } },
  );

  const { name, contributionsCollection: { contributionYears } } = data.data.user;

  const allYears = await Promise.all(
    contributionYears.map((year) => fetchYearContributions(username, token, year)),
  );

  const byRepo = {};
  for (const year of allYears) {
    for (const repo of year) {
      if (byRepo[repo.nameWithOwner]) {
        byRepo[repo.nameWithOwner].count += repo.count;
      } else {
        byRepo[repo.nameWithOwner] = { ...repo };
      }
    }
  }

  return {
    name,
    repos: Object.values(byRepo)
      .sort((a, b) => b.count - a.count)
      .slice(0, limit),
  };
}

module.exports = { fetchStats };
