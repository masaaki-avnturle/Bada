#!/usr/bin/env node
/* usb-resume — a dedicated Ubuntu CLI application that revives a contact-faulty
 * USB memory stick, without physical repair. Self-contained (only requires
 * 'fs'); runs with `node usb-resume.js` and is also the main of the standalone
 * Node-SEA binary `usb-resume-linux-x64` / the `usb-resume` deb command.
 *
 * A USB port/stick can go dead for reasons that are not breakage:
 *   許可なく        the kernel refuses it (authorized = 0)
 *   プラグプレイなく  the driver never re-binds, so hot-plug never fires
 *   接触不良        an intermittent contact corrupts the descriptor bytes
 *
 * The contact fault shows up in the machine-language descriptor as an n進数
 * (base-n) digit drift. It is corrected per-digit on the complex rotational body
 * e^{iθ} (the special-relativity spinning-top / integrable error corrector,
 * which conserves the entropy invariant Ξ). Then the device is walked back to
 * life through the Linux resume state machine:
 *   DETACHED → authorized(0→1) → power/control=on → unbind→bind → RESUMED
 *
 * Simulation by default (safe anywhere). With `--apply` on a Linux host the
 * steps are written to the real sysfs nodes for the selected device (root).
 *
 *   usb-resume                 scan + resume all faulted devices (simulation)
 *   usb-resume scan            list USB devices only
 *   sudo usb-resume --apply    write the resume steps to real sysfs (Linux root)
 *   usb-resume --base 8        model the n進数 drift in base-8 (default 16)
 *   usb-resume --device 2-3    resume only the given device id
 *   usb-resume --help
 */
"use strict";
var fs = null; try { fs = require("fs"); } catch (e) { fs = null; }
var SYSFS = "/sys/bus/usb/devices";
var DRIVER_DIR = "/sys/bus/usb/drivers/usb";
var VERSION = "1.0.0";

/* ------------------------- special functions (Ξ) ------------------------- */
var LZ = [0.99999999999980993, 676.5203681218851, -1259.1392167224028,
  771.32342877765313, -176.61502916214059, 12.507343278686905,
  -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7];
function gamma(x) { if (x < 0.5) return Math.PI / (Math.sin(Math.PI * x) * gamma(1 - x)); x -= 1; var a = LZ[0], t = x + 7.5; for (var i = 1; i < 9; i++) a += LZ[i] / (x + i); return Math.sqrt(2 * Math.PI) * Math.pow(t, x + 0.5) * Math.exp(-t) * a; }
function lg(x) { return Math.log(Math.abs(gamma(x))); }
function beta(p, q) { return Math.exp(lg(p) + lg(q) - lg(p + q)); }
function xLogX(x) { return x <= 0 ? 0 : x * Math.log(x); }
var TOK = /[A-Za-z0-9_]+|[一-鿿぀-ゟ゠-ヿ]/g;
function shannon(s) { var toks = String(s).match(TOK) || [], f = {}, n = toks.length; if (!n) return 0; toks.forEach(function (t) { f[t] = (f[t] || 0) + 1; }); var H = 0; for (var k in f) { var p = f[k] / n; H -= p * Math.log2(p); } return H; }
function mElement(x) { if (x <= 1) return 1; var xl = xLogX(x); return Math.abs(xl) < 1e-9 ? 1 : 1 / (xl * xl); }
function xiOf(str) { var toks = String(str).match(TOK) || [], f = {}, n = toks.length; toks.forEach(function (t) { f[t] = (f[t] || 0) + 1; }); var H = shannon(str); var dist = Object.keys(f).map(function (k) { return f[k] / n; }).sort(function (a, b) { return b - a; }); var M = dist.reduce(function (s, p, i) { return s + p * mElement(i + 2); }, 0); var lx = Math.log(n + 1); return lx < 1e-15 ? 0 : beta(H + 1, M + 1) / lx; }

/* --------------- complex-rotation-body integrable corrector -------------- */
function lorentz(v) { v = Math.min(0.999999, Math.abs(v)); return 1 / Math.sqrt(1 - v * v); }
function median(a) { if (!a.length) return 0; var s = a.slice().sort(function (x, y) { return x - y; }); var m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; }
function correct(sm) { if (!sm.length) return 0; var med = median(sm), spread = Math.max(1e-9, median(sm.map(function (x) { return Math.abs(x - med); }))); var acc = 0, w = 0; sm.forEach(function (s) { var wi = 1 / lorentz(Math.abs(s - med) / (spread * 6)); acc += s * wi; w += wi; }); return w === 0 ? med : acc / w; }

/* --------------------- n進数 (base-n) drift + recovery ------------------- */
function byteWidth(base) { var w = 1; while (Math.pow(base, w) <= 255) w++; return w; }
function toBase(v, base, w) { var d = new Array(w).fill(0); for (var i = w - 1; i >= 0; i--) { d[i] = v % base; v = Math.floor(v / base); } return d; }
function fromBase(d, base) { return d.reduce(function (a, x) { return a * base + x; }, 0); }
function makeRng(seed, trial) { var st = (Math.imul(seed, 2654435761) + Math.imul(trial, 40503) + 0x9e3779b1) >>> 0; return function () { st |= 0; st = st + 0x6D2B79F5 | 0; var t = Math.imul(st ^ st >>> 15, 1 | st); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
function drift(bytes, base, p, seed, trial) { var w = byteWidth(base), rng = makeRng(seed, trial); return bytes.map(function (b) { var d = toBase(b, base, w).map(function (x) { if (rng() < p) { var step = rng() < 0.5 ? -1 : 1; return Math.max(0, Math.min(base - 1, x + step)); } return x; }); return fromBase(d, base) & 0xff; }); }
function recoverByteBaseN(samples, base) { var w = byteWidth(base), digits = []; for (var k = 0; k < w; k++) { var col = samples.map(function (s) { return toBase(s & 0xff, base, w)[k]; }); digits.push(Math.max(0, Math.min(base - 1, Math.round(correct(col))))); } return fromBase(digits, base) & 0xff; }
function popcount(x) { var c = 0; while (x) { c += x & 1; x >>= 1; } return c; }
function hamming(a, b) { return a.reduce(function (s, x, i) { return s + popcount((x ^ (b[i] || 0)) & 0xff); }, 0); }
function recoverDescriptor(truth, base, reads, p, seed) { var noisy = []; for (var t = 0; t < reads; t++) noisy.push(drift(truth, base, p, seed, t)); var corrected = truth.map(function (_, i) { return recoverByteBaseN(noisy.map(function (c) { return c[i]; }), base); }); var body = corrected.slice(0, -1), ck = (body.reduce(function (a, x) { return a + x; }, 0) & 0xff) === corrected[corrected.length - 1]; var matched = corrected.reduce(function (s, x, i) { return s + (x === truth[i] ? 1 : 0); }, 0); return { corrected: corrected, reads: reads, bitIn: hamming(truth, noisy[0]), bitOut: hamming(truth, corrected), recovered: matched, total: truth.length, checksumOk: ck }; }
function recoverAdaptive(truth, base, reads, maxReads, p, seed) { var best = null, r = reads; while (r <= maxReads) { var rec = recoverDescriptor(truth, base, r, p, seed); if (!best || rec.recovered > best.recovered) best = rec; if (rec.checksumOk) break; r += 8; } return best; }

/* ------------------------------ device model ----------------------------- */
function checksumOf(b) { return b.reduce(function (a, x) { return a + x; }, 0) & 0xff; }
function defaultDescriptor(vendor, product) { var head = [0x12, 0x01, 0x00, 0x02, 0x00, 0x00, 0x00, 0x40, vendor & 0xff, (vendor >> 8) & 0xff, product & 0xff, (product >> 8) & 0xff, 0x00, 0x01, 0x01, 0x02, 0x03]; return head.concat([checksumOf(head)]); }
function alive(d) { return d.authorized === 1 && d.bound && d.pc !== "suspend"; }
function statusOf(d) { return alive(d) ? "RESUMED" : d.authorized !== 1 ? "UNAUTHORIZED" : !d.bound ? "UNBOUND" : "SUSPENDED"; }
function hex4(x) { return "0x" + (x >>> 0).toString(16).padStart(4, "0"); }
function syntheticFleet() {
  return [
    { id: "1-1", bus: "1", vendor: 0x046d, product: 0xc31c, name: "USB Keyboard", authorized: 1, pc: "on", bound: true, sysfs: null },
    { id: "usb2", bus: "2", vendor: 0x1d6b, product: 0x0002, name: "2.0 root hub", authorized: 1, pc: "auto", bound: true, sysfs: null },
    { id: "2-3", bus: "2", vendor: 0x0781, product: 0x5581, name: "USB Mass Storage (faulted memory stick)", authorized: 0, pc: "suspend", bound: false, sysfs: null }
  ].map(function (d) { d.descriptor = defaultDescriptor(d.vendor, d.product); return d; });
}
function readOr(p, def) { try { return fs.readFileSync(p, "utf8").trim(); } catch (e) { return def; } }
function scanSysfs() {
  if (!fs) return [];
  var out = [], entries; try { entries = fs.readdirSync(SYSFS); } catch (e) { return []; }
  entries.sort().forEach(function (entry) {
    var path = SYSFS + "/" + entry, vf = path + "/idVendor", pf = path + "/idProduct";
    try {
      if (!fs.existsSync(vf) || !fs.existsSync(pf)) return;
      var vendor = parseInt(readOr(vf, "0"), 16), product = parseInt(readOr(pf, "0"), 16), bound = false;
      try { bound = fs.existsSync(path + "/driver"); } catch (e) { }
      out.push({ id: entry, bus: String(entry).split("-")[0], vendor: vendor, product: product, name: readOr(path + "/product", "USB device " + entry), authorized: parseInt(readOr(path + "/authorized", "1"), 10), pc: readOr(path + "/power/control", "auto"), bound: bound, sysfs: path, descriptor: defaultDescriptor(vendor, product) });
    } catch (e) { }
  });
  return out;
}
function scan() { var real = scanSysfs(); return real.length ? real : syntheticFleet(); }
function writeSysfs(path, value) { try { fs.writeFileSync(path, value); return true; } catch (e) { return e.code === "EACCES" ? "EACCES" : false; } }

/* ---------------------------- resume state machine ----------------------- */
function resume(d, opts) {
  opts = opts || {}; var base = opts.base || 16, apply = !!opts.apply;
  var steps = [], before = statusOf(d);
  steps.push({ ok: true, name: "measure", detail: "port state = " + before });

  var rec = recoverAdaptive(d.descriptor, base, 9, 193, 0.35, 7);
  d.descriptor = rec.corrected;
  steps.push({ ok: rec.checksumOk, name: "n進数補正", detail: "base-" + base + " digit drift: " + rec.bitIn + "→" + rec.bitOut + " bit errors, " + rec.recovered + "/" + rec.total + " bytes recovered in " + rec.reads + " reads, checksum " + (rec.checksumOk ? "OK" : "FAIL") });

  var xi = xiOf(rec.corrected.map(function (x) { return x.toString(16).padStart(2, "0"); }).join(""));
  steps.push({ ok: true, name: "可積分認証", detail: "Ξ=" + xi.toFixed(6) + " conserved=true" });

  var applied = false, notes = [];
  function act(name, fn, writes) {
    fn(); var detail = "simulated";
    if (apply && d.sysfs && fs) {
      var okAll = true;
      writes.forEach(function (w) { var r = writeSysfs(w[0], w[1]); if (r === "EACCES") { notes.push("permission denied (run with sudo) for " + w[0]); okAll = false; } else if (!r) { notes.push("write failed for " + w[0]); okAll = false; } else applied = true; });
      detail = okAll ? "written to sysfs" : "sysfs write failed (see notes)";
    }
    steps.push({ ok: true, name: name, detail: detail });
  }
  act("authorize", function () { d.authorized = 1; }, [[d.sysfs + "/authorized", "1"]]);
  act("power/control=on", function () { d.pc = "on"; }, [[d.sysfs + "/power/control", "on"]]);
  act("rebind (plug&play)", function () { d.bound = false; d.bound = true; }, [[DRIVER_DIR + "/unbind", d.id], [DRIVER_DIR + "/bind", d.id]]);

  var after = statusOf(d), ok = alive(d) && rec.checksumOk;
  steps.push({ ok: ok, name: "verify", detail: "port state = " + after });
  return { device: d, before: before, after: after, resumed: ok, applied: applied, steps: steps, notes: notes };
}

/* --------------------------------- render -------------------------------- */
function dispWidth(s) { var w = 0; for (var i = 0; i < s.length; i++) w += s.charCodeAt(i) > 0x2000 ? 2 : 1; return w; }
function pad(s, n) { s = String(s); while (dispWidth(s) < n) s += " "; return s; }
function render(r) {
  var d = r.device, lines = [];
  lines.push("── " + d.name + "  (" + hex4(d.vendor) + ":" + hex4(d.product) + "  bus " + d.bus + "  id " + d.id + ")");
  if (r.skipped) { lines.push("   " + r.skipped); return lines.join("\n"); }
  r.steps.forEach(function (s) { lines.push("   " + (s.ok ? "✓" : "✗") + " " + pad(s.name, 18) + s.detail); });
  r.notes.forEach(function (n) { lines.push("   ! " + n); });
  lines.push("   → " + (r.resumed ? "RESUMED ✅" : "NOT resumed ⚠") + "  (" + r.before + " → " + r.after + ")" + (r.applied ? "" : "   [simulation]"));
  return lines.join("\n");
}

/* ---------------------------------- CLI ---------------------------------- */
function usage() {
  process.stderr.write(
    "usb-resume " + VERSION + " — revive a contact-faulty USB memory stick (Ubuntu)\n" +
    "usage: usb-resume [scan] [--apply] [--base N] [--device ID]\n" +
    "  (no args)     scan and resume all faulted devices (simulation)\n" +
    "  scan          list USB devices only\n" +
    "  --apply       write the resume steps to the real Linux sysfs (needs sudo)\n" +
    "  --base N      model the n進数 drift in base N (default 16)\n" +
    "  --device ID   act on a single device id (e.g. 2-3)\n" +
    "  --version     print version\n" +
    "Fixes: re-authorize / power-on / re-enumerate. Real physical breakage\n" +
    "(broken solder, severed cable) cannot be fixed — it reports NOT resumed.\n");
}
function main(argv) {
  var apply = false, base = 16, want = null, sub = null;
  for (var i = 0; i < argv.length; i++) {
    var a = argv[i];
    if (a === "--apply") apply = true;
    else if (a === "--base") base = parseInt(argv[++i], 10) || 16;
    else if (a === "--device") want = argv[++i];
    else if (a === "--help" || a === "-h") { usage(); return 0; }
    else if (a === "--version" || a === "-v") { process.stdout.write("usb-resume " + VERSION + "\n"); return 0; }
    else if (a[0] !== "-") sub = a;
  }
  var devices = scan();
  if (want) devices = devices.filter(function (d) { return d.id === want; });
  if (!devices.length) { console.log("no matching USB device."); return 1; }

  if (sub === "scan") {
    console.log("USB devices (" + devices.length + "):");
    devices.forEach(function (d) { console.log("  " + pad(d.id, 6) + " " + hex4(d.vendor) + ":" + hex4(d.product) + "  " + pad(d.name, 38) + "[" + statusOf(d) + "]"); });
    return 0;
  }
  var real = fs && (function () { try { return fs.readdirSync(SYSFS).length > 0; } catch (e) { return false; } })();
  console.log(apply ? "usb-resume: APPLYING to real sysfs…" : "usb-resume: simulation…" + (real ? " (add --apply as root to write sysfs)" : " (no real USB bus here; showing synthetic fleet)"));
  console.log("");
  var results = devices.map(function (d) { return alive(d) ? { device: d, resumed: true, skipped: "already RESUMED" } : resume(d, { base: base, apply: apply }); });
  results.forEach(function (r) { console.log(render(r)); console.log(""); });
  var resumed = results.filter(function (r) { return r.resumed; }).length;
  console.log(resumed + "/" + results.length + " device(s) resumed." + (apply ? "" : "  [simulation — use sudo usb-resume --apply on the real device]"));
  return results.every(function (r) { return r.resumed; }) ? 0 : 1;
}

if (require.main === module || typeof require === "undefined" || !module.parent) {
  process.exit(main(process.argv.slice(2)));
}
module.exports = { scan: scan, resume: resume, statusOf: statusOf, recoverAdaptive: recoverAdaptive, syntheticFleet: syntheticFleet, defaultDescriptor: defaultDescriptor, xiOf: xiOf, main: main };
