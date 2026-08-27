#!/usr/bin/env node
/* ============================================================================
 * build-vm.js — build BadaVM Pro (the quantum hypervisor) as a SINGLE
 * self-contained HTML file.
 *
 * Produces ../dist/bada-vm-pro.html : the Bada language core (bada.js) plus
 * the three Bada runtime libraries are inlined —
 *     bada/vmpro.bada    the BadaVM Pro hypervisor (VMX, BIOS, snapshots)
 *     bada/badax.bada    the BadaX Server (ASTEC-X style X server, QKD +
 *                        JONES-KNOT-COOKIE-1 display cookie)
 *     bada/badabsd.bada  BadaBSD 11.0 (NetBSD-style OS: sysinst installer,
 *                        FFS, boot loader, dmesg, /etc/rc, login, shell,
 *                        remote X clients)
 * — so downloading the one file and opening it in any browser gives a working
 * hypervisor + installable guest OS + external X server, offline, with no
 * server and no dependencies. The same file is staged as app/www/index.html
 * for the Electron (Windows 10/11, Ubuntu) wrapper.
 *
 * Before writing anything the whole guest lifecycle is SELF-CHECKED through
 * the real Bada interpreter: power-on -> sysinst install -> reboot -> login
 * -> shell -> X clients on the BadaX display.
 * ==========================================================================*/
"use strict";
const fs = require("fs");
const path = require("path");

const QVM = path.join(__dirname, "..");
const REPO = path.join(QVM, "..");
const WWW = path.join(REPO, "bada_gui_ide", "www");
const DIST = path.join(QVM, "dist");
fs.mkdirSync(DIST, { recursive: true });

const badaCore = fs.readFileSync(path.join(WWW, "bada.js"), "utf8");
const libs =
  fs.readFileSync(path.join(QVM, "bada", "vmpro.bada"), "utf8") + "\n" +
  fs.readFileSync(path.join(QVM, "bada", "badax.bada"), "utf8") + "\n" +
  fs.readFileSync(path.join(QVM, "bada", "badabsd.bada"), "utf8");
const Bada = require(path.join(WWW, "bada.js"));

/* ---- self-check: the full guest lifecycle must run through Bada ---------- */
function run(events) {
  let prog = 'NOW := "Thu Aug 27 22:14:03 JST 2026"\n' + libs + "\n";
  prog += 'VM := vm_create("BadaBSD 11.0 (quantum)", 2, 4096, 20480)\n';
  prog += "EVENTS := " + JSON.stringify(events) + "\n";
  prog += "os_run(VM, EVENTS)\n";
  return Bada.run(prog, { maxSteps: 80000000 });
}

(function selfCheck() {
  const tape = [
    ["power", "on"],            // BIOS POST -> ISO boot -> sysinst welcome
    ["key", "a"],               // language
    ["key", "a"],               // Install BadaBSD to hard disk
    ["key", "a"],               // disk wd0
    ["key", "a"],               // GPT
    ["key", "a"],               // last chance -> newfs + set extraction
    ["line", "swordfish"],      // root password
    ["line", "swordfish"],      // repeat
    ["line", "quantum"],        // hostname
    ["key", " "],               // reboot from hard disk
    ["line", "root"],           // login
    ["line", "swordfish"],      // password
    ["line", "uname -a"],
    ["line", "xclock &"],       // -> BadaX Server on the Windows host
    ["line", "xeyes &"],
    ["line", "xdpyinfo"],
    ["line", "qstat"],
  ];
  const r = run(tape);
  if (!r.ok) {
    console.error("self-check FAILED:\n" + (r.error || r.parseErrors.join("\n")));
    console.error(r.output.split("\n").slice(-30).join("\n"));
    process.exit(1);
  }
  // separately verify each milestone (each run emits only its last event)
  const milestones = [
    [1,  "sysinst"],                       // installer reached
    [6,  "newfs -O 2"],                    // disk formatted
    [10, "login:"],                        // boots from disk
    [12, "@@PROMPT quantum# "],            // shell prompt
    [14, "@@X WIN 1|xclock"],              // window on the BadaX display
    [16, "JONES-KNOT-COOKIE-1"],           // X auth cookie verified
    [17, "zero-preservation"],             // quantum tamper evidence
  ];
  for (const [n, marker] of milestones) {
    const rr = run(tape.slice(0, n));
    if (!rr.ok || rr.output.indexOf(marker) < 0) {
      console.error("self-check FAILED at event " + n + ": missing " + JSON.stringify(marker));
      console.error((rr.output || "").split("\n").slice(-20).join("\n"));
      process.exit(1);
    }
  }
  console.log("self-check OK: install -> boot -> login -> shell -> X on BadaX (" +
    tape.length + " ledger events)");
})();

/* ---- assemble the single-file app ---------------------------------------- */
const template = fs.readFileSync(path.join(QVM, "tools", "template.html"), "utf8");
const html = template
  .replace("__BADA_CORE__", () => badaCore)
  .replace("__VM_LIBS_JSON__", () => JSON.stringify(libs));

const out = path.join(DIST, "bada-vm-pro.html");
fs.writeFileSync(out, html);
console.log("built dist/bada-vm-pro.html (" + fs.statSync(out).size + " bytes)");

/* also stage it as the Electron app's www/index.html */
const APPWWW = path.join(QVM, "app", "www");
fs.mkdirSync(APPWWW, { recursive: true });
fs.writeFileSync(path.join(APPWWW, "index.html"), html);
console.log("staged app/www/index.html");
