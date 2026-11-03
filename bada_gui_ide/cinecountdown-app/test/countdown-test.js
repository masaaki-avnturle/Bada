/*
 * countdown-test.js — Bada 映画カウントダウンエンジンの自己検査
 *   node bada_gui_ide/cinecountdown-app/test/countdown-test.js
 */
"use strict";
var path = require("path");
var CD = require(path.join(__dirname, "..", "www", "countdown.js"));

var failed = 0;
function ok(c, l){ console.log((c ? "PASS" : "FAIL") + "  " + l); if (!c) failed++; }
function approx(a, b, e){ return Math.abs(a - b) <= (e || 1e-6); }

/* ── normalize / sequence ── */
var c = CD.normalize({ start: 8, end: 2, stepSeconds: 1, fps: 24 });
ok(c.start === 8 && c.end === 2, "normalize keeps start/end");
ok(JSON.stringify(CD.sequence(c)) === JSON.stringify([8,7,6,5,4,3,2]), "sequence 8..2 descending");
ok(CD.normalize({ start: 3, end: 9 }).end === 3, "end clamped to start when end>start");
ok(CD.normalize({ fps: 999 }).fps === 60 && CD.normalize({ fps: 0 }).fps === 1, "fps clamped to 1..60");

/* ── duration / frames ── */
ok(approx(CD.runDuration(c), 7), "runDuration = 7 numbers * 1s = 7s");
ok(approx(CD.duration(c), 7.5), "duration includes holdAfter 0.5 -> 7.5s");
ok(CD.totalFrames(c) === Math.round(7.5 * 24), "totalFrames = duration*fps");

/* ── stateAtTime: 数字の推移 ── */
ok(CD.stateAtTime(c, 0).number === 8, "t=0 shows 8");
ok(CD.stateAtTime(c, 1).number === 7, "t=1 shows 7");
ok(CD.stateAtTime(c, 6.5).number === 2, "t=6.5 shows 2 (last number)");
ok(CD.stateAtTime(c, 0.999).number === 8, "t just before 1s still 8");
ok(CD.stateAtTime(c, -5).number === 8, "negative time clamps to start (8)");

/* ── done フェーズ ── */
var d = CD.stateAtTime(c, 7.2);
ok(d.phase === "done" && d.finished === true, "after run -> done/finished");
ok(CD.stateAtTime(c, 7.0).phase === "done", "exactly at runDuration -> done");

/* ── 掃引角度: 1 秒で 1 回転 ── */
ok(approx(CD.stateAtTime(c, 0).angle, 0), "angle 0 at integer boundary");
ok(approx(CD.stateAtTime(c, 0.5).angle, Math.PI, 1e-3), "angle = pi at half second");
ok(approx(CD.stateAtTime(c, 0.25).angle, Math.PI/2, 1e-3), "angle = pi/2 at quarter second");
var half = CD.normalize({ start:5, end:4, stepSeconds:2 });
ok(approx(CD.stateAtTime(half, 1).angle, Math.PI, 1e-3), "2s/step: angle=pi at t=1 (half of step)");

/* ── フラッシュ: 整数切替直後だけ ── */
ok(CD.stateAtTime(c, 0).flash > 0, "flash present right at a new integer");
ok(CD.stateAtTime(c, 0.5).flash === 0, "no flash mid-step");
ok(CD.stateAtTime(CD.normalize({flash:false}), 0).flash === 0, "flash=false disables flash");

/* ── ビープ時刻 ── */
ok(CD.beepTimes(c).length === 1 && approx(CD.beepTimes(c)[0], 6), "single beep at '2' (7th number) -> t=6s");
var be = CD.beepTimes(CD.normalize({ beepEach: true }));
ok(be.length === 7 && approx(be[0],0) && approx(be[6],6), "beepEach: a beep at every integer (7 beeps)");
ok(CD.beepTimes(CD.normalize({ beep:false })).length === 0, "beep=false -> no beeps");
ok(approx(CD.beepTimes(CD.normalize({ beepAt:5 }))[0], 3), "beepAt=5 -> t=3s (8,7,6,5 -> index 3)");

/* ── render がフォールバックで落ちない (fake ctx) ── */
var calls = { fillRect:0, arc:0, fillText:0 };
var fake = {
  save:function(){}, restore:function(){}, beginPath:function(){}, closePath:function(){},
  moveTo:function(){}, lineTo:function(){}, stroke:function(){}, fill:function(){},
  arc:function(){ calls.arc++; }, fillRect:function(){ calls.fillRect++; }, fillText:function(){ calls.fillText++; },
  createRadialGradient:function(){ return { addColorStop:function(){} }; },
  set fillStyle(v){}, set strokeStyle(v){}, set lineWidth(v){}, set globalAlpha(v){},
  set font(v){}, set textAlign(v){}, set textBaseline(v){}
};
CD.render(fake, 1280, 720, CD.stateAtTime(c, 0), c);
ok(calls.fillRect > 0 && calls.arc > 0 && calls.fillText > 0, "render draws bg/rings/number without throwing");
CD.render(fake, 1280, 720, CD.stateAtTime(c, 7.4), c);
ok(true, "render handles the done phase without throwing");

console.log(failed === 0 ? "\nALL COUNTDOWN TESTS PASSED" : "\n" + failed + " TEST(S) FAILED");
process.exit(failed === 0 ? 0 : 1);
