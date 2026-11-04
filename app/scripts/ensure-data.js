// Copies the synthetic sample into place when no exported summaries exist yet,
// so the app bundles on a fresh checkout.
const fs = require('fs');
const path = require('path');

const dir = path.join(__dirname, '..', 'src', 'data');
const target = path.join(dir, 'summaries.json');

if (!fs.existsSync(target)) {
  fs.copyFileSync(path.join(dir, 'sample.json'), target);
  console.log('No exported summaries; using sample data. Run `python -m harness.hamar_news.export` for real ones.');
}
