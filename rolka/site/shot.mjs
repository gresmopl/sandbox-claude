import { chromium } from 'playwright';
import fs from 'fs';
const url = 'https://d.polnazdrojdomki.workers.dev/';
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 430, height: 932 }, deviceScaleFactor: 2 });
const fonts = new Set();
p.on('response', async r => { const u = r.url(); if (/\.(woff2?|ttf|otf)(\?|$)/.test(u)) { try { const buf = await r.body(); fs.writeFileSync('rolka/site/' + u.split('/').pop().split('?')[0], buf); fonts.add(u); } catch {} } });
await p.goto(url, { waitUntil: 'networkidle' });
await p.waitForTimeout(1500);
const info = await p.evaluate(() => {
  const fam = {}; document.querySelectorAll('body *').forEach(e => { const s = getComputedStyle(e); if (e.childElementCount === 0 && e.textContent.trim()) { const k = s.fontFamily.split(',')[0]; (fam[k] ||= []).length < 3 && fam[k].push(e.tagName + '.' + e.className + ': ' + e.textContent.trim().slice(0, 50) + ' | ' + s.color + ' ' + s.fontSize); } });
  return fam; });
fs.writeFileSync('rolka/site/info.json', JSON.stringify({ fonts: [...fonts], families: info }, null, 1));
const H = await p.evaluate(() => document.body.scrollHeight);
for (let i = 0, y = 0; y < Math.min(H, 932 * 8); i++, y += 932) { await p.evaluate(y => window.scrollTo(0, y), y); await p.waitForTimeout(900); await p.screenshot({ path: `rolka/site/s${i}.png` }); }
await b.close();
