require('dotenv').config();
const fs   = require('fs');
const path = require('path');
const { fetchStats } = require('./fetchStats');
const { renderCard } = require('./renderCard');

const USERNAME = process.env.GITHUB_USERNAME || 'thesirix';
const LIMIT    = parseInt(process.env.LIMIT || '10', 10);
const OUT      = path.join(__dirname, 'contrib-card.svg');

(async () => {
  console.log(`Fetching stats for ${USERNAME}...`);
  const stats = await fetchStats(USERNAME, LIMIT);
  const svg   = await renderCard(USERNAME, stats);
  fs.writeFileSync(OUT, svg, 'utf8');
  console.log(`SVG written → ${OUT}`);
})().catch((err) => {
  console.error(err.message);
  process.exit(1);
});
