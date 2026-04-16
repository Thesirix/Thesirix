require('dotenv').config();
const express = require('express');
const { fetchStats } = require('./fetchStats');
const { renderCard } = require('./renderCard');

const app  = express();
const PORT = 9999;

app.get('/api', async (req, res) => {
  const username = req.query.username;
  const limit    = parseInt(req.query.limit || '10', 10);

  if (!username) return res.status(400).send('username is required');

  try {
    const stats = await fetchStats(username, limit);
    const svg   = await renderCard(username, stats);
    res.set('Content-Type', 'image/svg+xml');
    res.set('Cache-Control', 'public, max-age=14400');
    res.send(svg);
  } catch (err) {
    console.error(err);
    res.status(500).send(`Error: ${err.message}`);
  }
});

app.listen(PORT, () => console.log(`Running → http://localhost:${PORT}/api?username=thesirix`));
