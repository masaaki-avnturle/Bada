/*
 * render.js — Bada Contrapunctus をヘッドレス Chromium で駆動し、動画ファイルを書き出す
 *
 *   node bach_monet_film/tools/render.js <入力音声> <出力.mp4> [オプション]
 *
 *   --w 1920 --h 1080     解像度(既定 1280×720)
 *   --fps 30              フレームレート
 *   --title "曲名"        画面に表示する曲名(既定: 入力ファイル名)
 *   --audio-out x.m4a     編曲後の音声だけを AAC で別保存
 *   --no-transpose        移調しない
 *   --voice 0.55 --reverb 0.5 --tempo 72 --finished   編曲パラメータ
 *   --seed 5              筆致の乱数種
 *   --crf 20              H.264 品質
 *   --ffmpeg PATH         ffmpeg の場所(既定: 環境変数 FFMPEG または PATH 上の ffmpeg)
 *   --chromium PATH       Chromium の場所(既定: playwright-core の既定)
 *
 * 必要なもの: Node.js, playwright-core (npm i playwright-core), ffmpeg (libx264 / aac)。
 * ブラウザ版 index.html はリアルタイム録画ですが、こちらは 1 フレームずつ描いて
 * ffmpeg に流し込むため、曲の長さに関係なく決定的に(同じ入力 → 同じ動画)書き出せます。
 * 入力は ffmpeg で一度 WAV に変換するので、Chromium が AAC を復号できなくても構いません。
 */
"use strict";
const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawn, spawnSync } = require("child_process");

function parseArgs(argv){
  const o = { w:1280, h:720, fps:30, seed:5, crf:20, transpose:true, unfinished:true, voice:0.55, reverb:0.5, tempo:72, pos:[] };
  for (let i = 0; i < argv.length; i++){
    const a = argv[i], next = () => argv[++i];
    if (a === "--w") o.w = parseInt(next(), 10);
    else if (a === "--h") o.h = parseInt(next(), 10);
    else if (a === "--fps") o.fps = parseInt(next(), 10);
    else if (a === "--title") o.title = next();
    else if (a === "--audio-out") o.audioOut = next();
    else if (a === "--no-transpose") o.transpose = false;
    else if (a === "--finished") o.unfinished = false;
    else if (a === "--voice") o.voice = parseFloat(next());
    else if (a === "--reverb") o.reverb = parseFloat(next());
    else if (a === "--tempo") o.tempo = parseInt(next(), 10);
    else if (a === "--seed") o.seed = parseInt(next(), 10);
    else if (a === "--crf") o.crf = parseInt(next(), 10);
    else if (a === "--ffmpeg") o.ffmpeg = next();
    else if (a === "--chromium") o.chromium = next();
    else if (a === "--max-seconds") o.maxSeconds = parseFloat(next());   /* デバッグ用: 先頭だけ */
    else o.pos.push(a);
  }
  return o;
}

async function main(){
  const o = parseArgs(process.argv.slice(2));
  if (o.pos.length < 2){ console.error("usage: node render.js <input audio> <output.mp4> [--w --h --fps --title ...]"); process.exit(2); }
  const input = path.resolve(o.pos[0]), output = path.resolve(o.pos[1]);
  const ffmpeg = o.ffmpeg || process.env.FFMPEG || "ffmpeg";
  const title = o.title || path.basename(input).replace(/\.[^.]+$/, "");
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "bada-fuga-"));
  const srcWav = path.join(tmp, "source.wav"), arrWav = path.join(tmp, "arranged.wav");

  /* 1. 入力 → WAV(44.1 kHz) */
  let r = spawnSync(ffmpeg, ["-hide_banner", "-loglevel", "error", "-y", "-i", input, "-ar", "44100", "-c:a", "pcm_s16le", srcWav], { stdio:"inherit" });
  if (r.status !== 0) throw new Error("ffmpeg decode failed");

  /* 2. Chromium でページを開き、解析 → 編曲 */
  const { chromium } = require("playwright-core");
  const browser = await chromium.launch({ executablePath: o.chromium || process.env.CHROMIUM || undefined, args:["--autoplay-policy=no-user-gesture-required"] });
  const page = await browser.newPage({ viewport:{ width:1300, height:800 } });
  page.on("pageerror", e => console.error("[page error]", e.message));
  const html = "file://" + path.resolve(__dirname, "..", "index.html") + "?headless=1";
  await page.goto(html);
  const b64 = fs.readFileSync(srcWav).toString("base64");
  const info = await page.evaluate(async (args) => {
    const bin = atob(args.b64), u8 = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
    const loaded = await window.__fuga.load(u8.buffer, args.title + ".wav");
    const arranged = await window.__fuga.arrange({ transpose:args.transpose, voiceLevel:args.voice, reverb:args.reverb, tempo:args.tempo, unfinished:args.unfinished });
    const setup = window.__fuga.setup(args.w, args.h, args.fps, args.seed);
    return { loaded, arranged, setup };
  }, { b64, title, transpose:o.transpose, voice:o.voice, reverb:o.reverb, tempo:o.tempo, unfinished:o.unfinished, w:o.w, h:o.h, fps:o.fps, seed:o.seed });
  console.log(`key: ${info.loaded.key} (${info.loaded.keyJa})  transpose: ${info.arranged.semitones} semitones  tempo: ${info.arranged.tempo}  voices: ${info.arranged.notes} notes / ${info.arranged.entries.length} entries  cutoff: ${info.arranged.cutoff.toFixed(1)} s  total: ${info.arranged.total.toFixed(1)} s`);
  info.arranged.entries.forEach(e => console.log(`  entry ${e.t.toFixed(1).padStart(6)} s  ${e.name} — ${e.voice}`));

  /* 3. 編曲後の音声を WAV に */
  const wavB64 = await page.evaluate(() => window.__fuga.wavBase64());
  fs.writeFileSync(arrWav, Buffer.from(wavB64, "base64"));
  if (o.audioOut){
    r = spawnSync(ffmpeg, ["-hide_banner", "-loglevel", "error", "-y", "-i", arrWav, "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", path.resolve(o.audioOut)], { stdio:"inherit" });
    if (r.status !== 0) throw new Error("ffmpeg audio encode failed");
    console.log("audio:", o.audioOut);
  }

  /* 4. フレームを 1 枚ずつ描いて ffmpeg へ */
  let frames = info.setup.frames;
  if (o.maxSeconds) frames = Math.min(frames, Math.ceil(o.maxSeconds * o.fps));
  const enc = spawn(ffmpeg, ["-hide_banner", "-loglevel", "error", "-y",
    "-f", "image2pipe", "-framerate", String(o.fps), "-c:v", "mjpeg", "-i", "pipe:0",
    "-i", arrWav,
    "-c:v", "libx264", "-preset", "medium", "-crf", String(o.crf), "-pix_fmt", "yuv420p", "-r", String(o.fps),
    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", output], { stdio:["pipe", "inherit", "inherit"] });
  const encDone = new Promise((res, rej) => { enc.on("close", code => code === 0 ? res() : rej(new Error("ffmpeg exit " + code))); });
  const t0 = Date.now();
  for (let i = 0; i < frames; i++){
    const dataUrl = await page.evaluate(i => window.__fuga.frame(i, true, 0.93), i);
    const buf = Buffer.from(dataUrl.slice(dataUrl.indexOf(",") + 1), "base64");
    if (!enc.stdin.write(buf)) await new Promise(res => enc.stdin.once("drain", res));
    if (i % (o.fps * 10) === 0) console.log(`frame ${i}/${frames}  ${((Date.now() - t0) / 1000).toFixed(0)} s`);
  }
  enc.stdin.end();
  await encDone;
  await browser.close();
  fs.rmSync(tmp, { recursive:true, force:true });
  console.log("done:", output, `(${frames} frames, ${((Date.now() - t0) / 1000).toFixed(0)} s)`);
}
main().catch(e => { console.error(e); process.exit(1); });
