// record_video.js — step the blueprint player's render(t) frame by frame in
// headless Chromium and pipe the canvas PNGs into ffmpeg -> H.264 MP4.
//   node record_video.js <player.html> <out.mp4> <ffmpeg> [fps]
const { chromium } = require('playwright');
const { spawn } = require('child_process');

(async () => {
  const [html, out, ffmpeg, fpsArg] = process.argv.slice(2);
  const fps = parseInt(fpsArg || '30', 10);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  await page.goto('file://' + html + '#record');
  const duration = await page.evaluate(() => window.DURATION);
  const n = Math.ceil(duration * fps);

  const ff = spawn(ffmpeg, ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps),
    '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-movflags', '+faststart', out],
    { stdio: ['pipe', 'inherit', 'inherit'] });

  for (let i = 0; i < n; i++) {
    const b64 = await page.evaluate(t => { window.render(t); return document.getElementById('c').toDataURL('image/png').slice(22); }, i / fps);
    if (!ff.stdin.write(Buffer.from(b64, 'base64'))) await new Promise(r => ff.stdin.once('drain', r));
    if (i % (fps * 5) === 0) process.stdout.write(`frame ${i}/${n}\n`);
  }
  ff.stdin.end();
  await new Promise((res, rej) => ff.on('close', c => (c === 0 ? res() : rej(new Error('ffmpeg exit ' + c)))));
  await browser.close();
  process.stdout.write(`wrote ${out} (${n} frames @ ${fps} fps)\n`);
})().catch(e => { console.error(e); process.exit(1); });
