// @ts-check
/**
 * Generate Wakatime SVG card locally — replaces github-readme-stats.vercel.app.
 *
 * Vendors github-readme-stats wakatime renderer. Uses authenticated Wakatime
 * API endpoint via WAKATIME_API_KEY (falls back to public stats if absent).
 */

import fs from "fs";
import { renderWakatimeCard } from "./src/cards/wakatime.js";

const username = process.env.WAKATIME_USERNAME || "thesirix";
const apiKey = process.env.WAKATIME_API_KEY;

const url = `https://wakatime.com/api/v1/users/${username}/stats?is_including_today=true`;
const headers = apiKey
  ? { Authorization: `Basic ${Buffer.from(apiKey).toString("base64")}` }
  : {};

const res = await fetch(url, { headers });
if (!res.ok) {
  console.error(`Wakatime API ${res.status} ${res.statusText}`);
  process.exit(1);
}
const json = await res.json();
const stats = json.data;

const svg = renderWakatimeCard(stats, {
  theme: "tokyonight",
  title_color: "5acbe9",
  text_color: "DEDEDE",
  hide_border: true,
  layout: "compact",
});

fs.writeFileSync("waka-card.svg", svg);
console.log("waka-card.svg generated ✓");
