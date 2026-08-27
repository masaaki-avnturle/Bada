#!/usr/bin/env node
/* ============================================================================
 * build-all-apps.js — regenerate every self-contained ultra-network app into
 * ../dist, and write dist/apps-README.txt. One command for the whole suite.
 * ==========================================================================*/
"use strict";
const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const TOOLS = __dirname;
const DIST = path.join(TOOLS, "..", "dist");

const builds = [
  "build-zone-browser.js",   // dist/zone-browser.html  (+ zonebrowser-app/www)
  "build-zone-dist.js",      // dist/bada-zone.html     (zone.bada runner)
  "build-ultraweb-example.js",
  "build-modemvault.js",     // dist/modem-vault.html
  "build-quantum-shark.js",  // dist/quantum-shark.html
  "build-zoneimport.js",     // dist/lan-to-zone.html
  "build-ngn-example.js",    // examples/ngn-quantum.bada
  "build-ngngrid.js",        // dist/ngn-quantum.html
  "build-zone-studio.js",    // dist/zone-studio.html
  "build-safepower.js",      // dist/safepower.html
  "build-instanton.js",      // dist/instanton.html
  "build-migemo.js",         // dist/migemo.html
  "build-migemo-media.js",   // dist/migemo-media.html
  "build-madokey.js"         // dist/madokey.html
];
for (const b of builds) {
  process.stdout.write("• " + b + "  ");
  execSync("node " + JSON.stringify(path.join(TOOLS, b)), { stdio: "inherit" });
}

const readme = `Ultra Network apps — Bada quantum programming language
======================================================

Each file below is a SINGLE self-contained HTML app. Download one and open
it in any browser — no install, no dependencies, works offline.

  zone-browser.html   ZoneBrowser — the dedicated ultra-network browser for
                      the zone:// WWW (P2P DHT + Jones quantum cipher + the
                      evolved UltraDatabase quorum + cognitive_system search).
  ngn-quantum.html    NGN Quantum Grid — zone://url.or.jp projected onto the
                      NTT NGN line: regional backbone ring, home/office PCs as
                      HDD pseudo-quantum registers, entanglement over NTT lines.
  zone-studio.html    Zone Studio — author YOUR OWN WWW addressed by zone://
                      URIs and publish it into the ultra-network over NTT NGN
                      (UltraDB quorum + Jones cipher); export/import .zonesite.
  safepower.html      SafePower — safe instant power-off (sync + hibernate) and
                      a rehalt-style soft reboot. Real actions run in the
                      SafePower desktop app / CLI; this page shows the commands.
  instanton.html      InstantOn — power off saves state to disk so the next
                      power-on skips the boot and resumes instantly (hibernate
                      / Windows fast startup). Real actions in the desktop app / CLI.
  migemo.html         Migemogram — an Instagram-like photo feed with migemo-style
                      romaji -> Japanese incremental search (type "sora" to find
                      そら/ソラ captions). Posts/likes/comments in localStorage.
  migemo-media.html   Migemogram Media — gallery of your own photos/videos (from
                      your PC via a picker, from your cloud via a media URL):
                      hover to pop out big, hover a video for a muted CM preview,
                      click for a full lightbox with sound, migemo search, and
                      "import to zone://url.or.jp" (UltraDB quorum + Jones cipher).
  lan-to-zone.html    LAN -> zone:// — import your own PC/LAN IP addresses into
                      zone://url.or.jp/lan/ (encrypted, quorum-replicated).
  modem-vault.html    Modem Vault — a Jones-quantum-cipher password vault for
                      YOUR OWN modem/router credentials, plus LAN detection.
  quantum-shark.html  QuantumShark — a Wireshark-style packet analyzer whose
                      capture files (.qcap) are encrypted with the Jones cipher
                      (demo master: "demo").
  madokey.html        MadoKey (窓使いのキー) — an homage to 窓使いの憂鬱: a
                      keybinding config editor for Word/Excel/LibreOffice.
                      Edit key -> action bindings (ruby, sum, copy, custom),
                      try them live in-page, and export madokey.mayu (the
                      madokey.py daemon config) and madokey.ahk (AutoHotkey v1).
  bada-zone.html      zone.bada runner — runs the zone:// reference program.

Command-line tools (need the repo checkout; run with Node.js):
  cli/bada-cli.js                       run/build .bada programs
  zoneimport/cli/lan-to-zone.js         import your LAN IPs into zone:// (real)
  modemvault/cli/modem-scan.js          detect your LAN modem/gateway (no passwords)
  netcapture/cli/qshark-capture.js      capture your own traffic -> encrypted .qcap
  madokey-app/madokey.py                MadoKey keybinding daemon (Word/Excel/LO)

Scope: every app is for YOUR OWN machine / network. None derives or reveals
anyone else's credentials.

(c) Masaaki Yamaguchi — Bada / Ultra Network
`;
fs.writeFileSync(path.join(DIST, "apps-README.txt"), readme);
console.log("\nwrote dist/apps-README.txt");
console.log("apps in dist/:");
for (const f of fs.readdirSync(DIST)) if (/\.html$/.test(f)) console.log("  " + f);
