const axios = require('axios');

const C = {
  bg:      '#1a1b2e',
  border:  '#414868',
  title:   '#bb9af7',
  name:    '#c0caf5',
  commits: '#7aa2f7',
  header:  '#73daca',
  dim:     '#565f89',
};

const WIDTH    = 440;
const PAD      = 22;
const ROW_H    = 34;
const AVATAR_R = 10;
const HEADER_Y = 52;
const FONT     = "'Segoe UI', 'Helvetica Neue', sans-serif";
const MAX_NAME = 30;
const COUNT_X  = WIDTH - PAD;

async function getBase64(url) {
  try {
    const res = await axios.get(`${url}&s=40`, { responseType: 'arraybuffer', timeout: 5000 });
    const b64 = Buffer.from(res.data).toString('base64');
    const ct  = res.headers['content-type'] || 'image/png';
    return `data:${ct};base64,${b64}`;
  } catch {
    return '';
  }
}

function trunc(str, max) {
  return str.length > max ? str.slice(0, max - 1) + '…' : str;
}

async function renderCard(username, stats) {
  const { name, repos } = stats;
  const title  = `${name || username}'s Top Repos`;
  const height = HEADER_Y + repos.length * ROW_H + PAD;

  const avatars = await Promise.all(repos.map((r) => getBase64(r.avatarUrl)));

  const rows = repos.map((repo, i) => {
    const cy  = HEADER_Y + i * ROW_H + ROW_H / 2;
    const img = avatars[i];
    return `
  <clipPath id="av${i}"><circle cx="${PAD + AVATAR_R}" cy="${cy}" r="${AVATAR_R}"/></clipPath>
  <image href="${img}" x="${PAD}" y="${cy - AVATAR_R}" width="${AVATAR_R * 2}" height="${AVATAR_R * 2}" clip-path="url(#av${i})"/>
  <text x="${PAD + AVATAR_R * 2 + 8}" y="${cy + 5}" fill="${C.name}" font-size="13" font-family="${FONT}">${trunc(repo.name, MAX_NAME)}</text>
  <text x="${COUNT_X}" y="${cy + 5}" fill="${C.commits}" font-size="13" font-family="${FONT}" text-anchor="end" font-weight="600">${repo.count}</text>`;
  }).join('\n');

  return `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="${WIDTH}" height="${height}">
  <rect width="${WIDTH}" height="${height}" rx="12" fill="${C.bg}" stroke="${C.border}" stroke-width="1"/>
  <text x="${WIDTH / 2}" y="30" fill="${C.title}" font-size="15" font-family="${FONT}" font-weight="bold" text-anchor="middle">${title}</text>
  <text x="${PAD + AVATAR_R * 2 + 8}" y="${HEADER_Y - 6}" fill="${C.header}" font-size="11" font-family="${FONT}" font-weight="600">Repository</text>
  <text x="${COUNT_X}" y="${HEADER_Y - 6}" fill="${C.header}" font-size="11" font-family="${FONT}" text-anchor="end" font-weight="600">Commits</text>
  <line x1="${PAD}" y1="${HEADER_Y - 1}" x2="${WIDTH - PAD}" y2="${HEADER_Y - 1}" stroke="${C.border}" stroke-width="1"/>
  ${rows}
</svg>`;
}

module.exports = { renderCard };
