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

/* the zone:// ultra-network runtime + well-known site, bundled INTO the
 * guest OS (the same zone-lib.bada that powers the ZoneBrowser app) */
const BR = path.join(REPO, "bada_gui_ide", "browser");
const zoneLib = fs.readFileSync(path.join(BR, "zone-lib.bada"), "utf8");
const zoneSite = JSON.parse(fs.readFileSync(path.join(BR, "zone-site.json"), "utf8"));
const zoneSiteBada =
  "# ---- the well-known zone:// site (generated from zone-site.json) ----\n" +
  "def zone_site() {\n    return [\n" +
  Object.entries(zoneSite)
    .map(([u, c]) => "        [" + JSON.stringify(u) + ", " + JSON.stringify(c) + "]")
    .join(",\n") +
  "\n    ]\n}\n";

const libs =
  fs.readFileSync(path.join(QVM, "bada", "vmpro.bada"), "utf8") + "\n" +
  fs.readFileSync(path.join(QVM, "bada", "badax.bada"), "utf8") + "\n" +
  zoneLib + "\n" + zoneSiteBada + "\n" +
  fs.readFileSync(path.join(QVM, "bada", "badabsd.bada"), "utf8");
const Bada = require(path.join(WWW, "bada.js"));

/* ---- self-check: the full guest lifecycle must run through Bada ---------- */
function run(events) {
  let prog = 'NOW := "Thu Aug 27 22:14:03 JST 2026"\n' + libs + "\n";
  prog += 'VM := vm_create("BadaOS 12.0 (quantum)", 2, 4096, 20480)\n';
  prog += "EVENTS := " + JSON.stringify(events) + "\n";
  prog += "os_run(VM, EVENTS)\n";
  return Bada.run(prog, { maxSteps: 80000000 });
}

(function selfCheck() {
  const tape = [
    ["power", "on"],            //  1 BIOS POST -> ISO boot -> sysinst welcome
    ["key", "a"],               //  2 language
    ["key", "a"],               //  3 Install BadaOS to hard disk
    ["key", "b"],               //  4 target disk: rd0 (REAL disk, RDM pass-through)
    ["key", "a"],               //  5 GPT
    ["key", "a"],               //  6 boot loader: LILO -> MBR + GRUB menu mode
    ["key", "a"],               //  7 last chance -> newfs + sets (vim/emacs/ssh/xinetd) + lilo -M
    ["line", "swordfish"],      //  8 root password
    ["line", "swordfish"],      //  9 repeat
    ["line", "quantum"],        // 10 hostname -> creates first user 'bada'
    ["key", " "],               // 11 reboot: rc starts the PREINSTALLED sshd + xinetd
    ["line", "root"],           // 12 login
    ["line", "swordfish"],      // 13 password
    ["line", "netstat"],        // 14 sshd/xinetd LISTEN from the very first boot
    ["line", "vim /etc/motd"],  // 15 preinstalled editors
    ["line", "emacs /etc/rc.conf"], // 16
    ["line", "ping www.badaos.or.jp"],          // 17 the internet over the NAT
    ["line", "curl http://www.badaos.or.jp/"],  // 18
    ["line", "wget http://www.badaos.or.jp/"],  // 19
    ["line", "apt update"],     // 20 apt fetches the EXTERNAL mirror over the NAT
    ["line", "apt install zsh bash tcsh"], // 21 shells still via apt
    ["line", "su - bada"],      // 22 root -> ordinary user (no password needed)
    ["line", "whoami"],         // 23
    ["line", "sudo apt update"],// 24 one root command from the user
    ["line", "exit"],           // 25 back to root
    ["line", "su - bada"],      // 26 down again
    ["line", "su"],             // 27 user -> root: asks the password
    ["line", "swordfish"],      // 28 password accepted -> root frame pushed
    ["line", "xterm &"],        // 29 live xterm (inherits the root session)
    ["xline", 1, "whoami"],     // 30 typed INSIDE the xterm
    ["xline", 1, "su - bada"],  // 31 switch user inside the xterm
    ["xline", 1, "exit"],       // 32 pop back to root in the xterm
    ["xline", 1, "exit"],       // 33 shell exits -> the window closes
    ["line", "zone zone://url.or.jp/"],  // 34 the zone:// ultra network, in-guest
    ["line", "zone put zone://url.or.jp/mypage hello ultra network from BadaOS"], // 35
    ["line", "zone zone://url.or.jp/mypage"], // 36 fetch the page we published
    ["line", "zonebrowser &"],  // 37 the ZoneBrowser as an X client (window 2)
    ["xzone", 2, "zone://bada.or.jp/"],       // 38 navigate (another knot key)
    ["xzone", 2, "zone://ghost.or.jp/nowhere"], // 39 404 demo
    ["line", "curl zone://url.or.jp/security"], // 40 curl speaks zone:// too
  ];
  const r = run(tape);
  if (!r.ok) {
    console.error("self-check FAILED:\n" + (r.error || r.parseErrors.join("\n")));
    console.error(r.output.split("\n").slice(-30).join("\n"));
    process.exit(1);
  }
  // separately verify each milestone (each run emits only its last event)
  const milestones = [
    [1,  "sysinst"],                        // installer reached
    [4,  "raw device mapping"],             // real-disk RDM selected
    [7,  "lilo -M /dev/rrd0d mbr"],         // LILO written into the MBR
    [7,  "GRUB 2 menu mode"],               // ... in GRUB menu mode
    [7,  "vim.tgz: 100%"],                  // the Linux suite ships in the sets
    [7,  "emacs.tgz: 100%"],
    [7,  "openssh.tgz: 100%"],
    [7,  "xinetd.tgz: 100%"],
    [10, "Creating first user account 'bada'"],
    [11, "GNU GRUB  version 2.12"],         // boots through the GRUB menu
    [11, "Starting sshd."],                 // preinstalled daemons start at boot
    [11, "Starting xinetd."],
    [11, "login:"],
    [13, "@@PROMPT quantum# "],             // root sh prompt
    [14, "sshd (QKD)"],                     // netstat: *.22 LISTEN at first boot
    [14, "xinetd: echo"],
    [15, "[view -- edit with: echo text > /etc/motd]"],   // vim works
    [16, "-UUU:----F1  /etc/rc.conf"],                    // emacs works
    [17, "0.0% packet loss"],               // ping through the NAT
    [18, "package archive"],                // curl fetched the portal page
    [19, "saved ["],                        // wget saved index.html
    [20, "Get:2 http://archive.badaos.or.jp quantum InRelease"], // apt over NAT
    [21, "Setting up zsh"],
    [22, "@@PROMPT quantum$ "],             // ordinary-user prompt ($)
    [23, "@@TTY bada"],                     // whoami as the user
    [24, "Fetched 16.2 kB"],                // sudo apt update worked
    [25, "@@PROMPT quantum# "],             // exit -> back to root (#)
    [27, "@@PROMPT Password: "],            // su asks the password...
    [27, "@@ECHO off"],                     // ...hidden input
    [28, "@@PROMPT quantum# "],             // and lands in a root frame
    [29, "@@X WIN 1|xterm"],
    [30, "@@XTTY 1 root"],                  // whoami inside the xterm
    [31, "@@XPROMPT 1 quantum$ "],          // su - bada inside the xterm
    [32, "@@XPROMPT 1 quantum# "],
    [33, "@@X UNMAP 1"],                    // exit at the bottom closes the window
    [34, "status 200 zone-delivered"],      // zone:// resolved on the P2P ring
    [34, "Ultra Network"],                  // ... and decrypted the home page
    [36, "hello ultra network from BadaOS"],// our own zone put page round-trips
    [37, "@@X WIN 2|zonebrowser"],          // ZoneBrowser mapped on BadaX
    [37, "@@ZPAGE 2|200|zone://url.or.jp/|"],
    [38, "@@ZPAGE 2|200|zone://bada.or.jp/|"], // navigation (different knot)
    [39, "@@ZPAGE 2|404|"],                 // unknown zone -> 404
    [40, "Jones 多項式量子暗号"],           // curl zone://.../security
  ];
  for (const [n, marker] of milestones) {
    const rr = run(tape.slice(0, n));
    if (!rr.ok || rr.output.indexOf(marker) < 0) {
      console.error("self-check FAILED at event " + n + ": missing " + JSON.stringify(marker));
      console.error((rr.output || "").split("\n").slice(-25).join("\n"));
      process.exit(1);
    }
  }
  console.log("self-check OK: install(rd0, LILO->MBR/GRUB, preinstalled vim/emacs/sshd/xinetd)" +
    " -> boot -> internet over NAT (ping/curl/wget, apt mirror) -> su/sudo user switching" +
    " -> live xterm -> zone:// ultra network (" + tape.length + " ledger events)");
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
