require('dotenv').config(); // .envファイルを読み込む
const express = require('express');
const app = express();

app.get('/api-key', (req, res) => {
  res.json({ apiKey: process.env.API_KEY });
});

app.use(express.static('public'));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});