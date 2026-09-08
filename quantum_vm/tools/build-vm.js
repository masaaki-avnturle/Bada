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
  fs.readFileSync(path.join(QVM, "bada", "badapache.bada"), "utf8") + "\n" +
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
    ["line", "migemoinsta sakura"],       // 41 migemo: romaji hits さくら/桜
    ["line", "migemoinsta post BadaOS saikou desu"], // 42 post to the ring
    ["line", "migemoinsta saikou"],       // 43 finds our own post
    ["line", "migemoinsta &"],            // 44 the X client (window 3)
    ["xinsta", 3, "neko"],                // 45 incremental search in the window
    ["xilike", 3, 4],                     // 46 like the neko post
    ["xzone", 2, "zone://insta.or.jp/"],  // 47 the feed is a zone site too
    ["line", "apt install gcc python3 cowsay"], // 48 Ubuntu-sized archive: ANY package
    ["line", "cowsay moo"],               // 49 ... and it runs
    ["line", "which cowsay"],             // 50
    ["line", "apt search firefox"],       // 51
    ["line", "apt remove cowsay"],        // 52
    ["line", "which grub-install"],       // 53 boot-loader tools preinstalled
    ["line", "grub-install /dev/rrd0d"],  // 54 GRUB into the MBR (table kept)
    ["line", "update-grub"],              // 55 re-register the OS in the menu
    ["line", "lsusb"],                    // 56 USB connectors recognized
    ["line", "bluetoothctl"],             // 57 Bluetooth recognized (bluez)
    ["line", "w9wm &"],                   // 58 Plan 9 style WM takes over BadaX
    ["line", "twm &"],                    // 59 ... and the default look returns
    ["line", "mlterm &"],                 // 60 Japanese-capable terminal on BadaX
    ["xline", 4, "echo 日本語のmlterm"],  // 61 UTF-8 shell inside the mlterm
    ["line", "fcitx"],                    // 62 fcitx-mozc input method
    ["line", "fcitx-configtool"],         // 63 ... and its config tool
    ["line", "platex report.tex"],        // 64 TeX Live (Japanese pLaTeX)
    ["line", "afterstep &"],              // 65 NeXTSTEP style WM + Wharf
    ["line", "twm &"],                    // 66 back to the default
    ["line", "wmaker &"],                 // 67 Window Maker workspace + Dock
    ["line", "twm &"],                    // 68 ... and back again
    ["line", "xcalc &"],                  // 69 x11-apps calculator on BadaX
    ["line", "udisksctl"],                // 70 USB stick recognized (udisks2)
    ["line", "udisksctl mount -b /dev/sd0i"], // 71 ... and mounts
    ["line", "apt install nautilus"],     // 72 nautilus installs over the NAT
    ["line", "nmcli"],                    // 73 NetworkManager: NAT auto-connect
    ["line", "git --version"],            // 74 git preinstalled
    ["line", "xcode-select --install"],   // 75 Xcode CLT == Debian toolchain
    ["line", "brew install wget"],        // 76 Homebrew / Linuxbrew
    ["line", "apachectl start"],          // 77 BadaApache -> publishes to zone://url.or.jp
    ["line", "zone zone://url.or.jp/apache"], // 78 the ring now serves Apache's page
    ["line", "apachectl status"],         // 79 running, pages published
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
    [11, "BadaOS Commander -- OS Selection"], // System Commander-style chooser
    [11, "Ubuntu 24.04 LTS"],               // ... listing the other OSes too
    [11, "Windows 10"],
    [11, "Windows 11"],
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
    [24, "Fetched 18.7 MB"],                // sudo apt update worked
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
    [41, "@sakura_chan"],                   // migemo: "sakura" -> さくら
    [41, "さくら / サクラ"],
    [42, "zone://insta.or.jp/p/100"],       // our post got a zone page
    [43, "BadaOS saikou desu"],             // ... and migemo finds it
    [44, "@@X WIN 3|migemoinsta"],          // MigemoInsta mapped on BadaX
    [44, "@@IPOST 3|1|sakura_chan"],        // feed rendered
    [45, "@@IPAGE 3|neko|1|"],              // incremental search: 1 hit
    [45, "@@IPOST 3|4|neko_master"],
    [46, "@@ILIKE 3|4|1"],                  // like committed to the ledger
    [47, "@@ZPAGE 2|200|zone://insta.or.jp/|"], // the feed in the ZoneBrowser
    [47, "MigemoInsta"],
    [48, "Setting up gcc"],                 // Ubuntu-compatible universe installs
    [48, "Setting up cowsay"],
    [49, "cowsay: moo -- OK"],              // installed applications execute
    [50, "@@TTY /usr/bin/cowsay"],
    [51, "74362 indexed packages"],         // apt search over the Ubuntu-sized index
    [52, "Removing cowsay"],
    [53, "@@TTY /usr/sbin/grub-install"],   // grub-install/update-grub preinstalled
    [54, "Installation finished. No error reported."],
    [55, "Found BadaOS GNU/Quantum 12.0 on /dev/rd0a"],
    [55, "Found Ubuntu 24.04 LTS on /dev/rd0e"],          // os-prober lists the
    [55, "Found Windows Boot Manager (Windows 10)"],      // machine's other OSes
    [55, "Found Windows Boot Manager (Windows 11)"],
    [56, "Quantum USB stick"],              // usb connectors recognized (lsusb)
    [56, "Quantum Bluetooth 5.3 adapter"],
    [57, "quantum-earbuds (connected, A2DP)"], // bluetoothctl works (bluez)
    [58, "Plan 9 style window manager"],    // w9wm manages the BadaX display
    [58, "@@X WM w9wm"],
    [59, "@@X WM twm"],                     // twm restores the default look
    [60, "@@X WIN 4|mlterm"],               // mlterm maps as a live terminal
    [60, "日本語対応マルチリンガルターミナル"],
    [61, "@@XTTY 4 日本語のmlterm"],        // UTF-8 shell inside the mlterm
    [62, "Mozc (日本語)"],                  // fcitx-mozc runs
    [63, "Noto Sans CJK JP"],               // fcitx-configtool runs
    [64, "quantum TeX Live 2024"],          // pLaTeX (texlive-full) runs
    [65, "@@X WM afterstep"],               // AfterStep manages BadaX
    [65, "NeXTSTEP style window manager"],
    [66, "@@X WM twm"],
    [67, "@@X WM wmaker"],                  // Window Maker manages BadaX
    [67, "Window Maker 0.96.0"],
    [68, "@@X WM twm"],
    [69, "|Calculator"],                    // xcalc (x11-apps) maps on BadaX
    [70, "Quantum USB stick 8GB"],          // USB storage recognized (udisks2)
    [71, "/media/root/QUANTUM-USB"],        // ... and mounted
    [72, "Setting up nautilus"],            // nautilus installs over the NAT
    [73, "BadaOS Wired (auto)"],            // NetworkManager NAT auto-connect
    [73, "autoconnect: yes"],
    [74, "git version 2.43.0"],             // git preinstalled
    [75, "git / gcc / g++ / clang / make"], // Xcode CLT == Debian toolchain
    [76, "Homebrew"],                       // brew installs over the NAT
    [77, "BadaApache/2.4.58"],              // Apache-in-Bada starts
    [77, "served on zone://url.or.jp"],     // ... and publishes to the ring
    [78, "BadaApache"],                     // the ring now serves Apache's page
    [78, "status 200 zone-delivered"],
    [79, "pages published to the ring"],    // apachectl status
  ];
  for (const [n, marker] of milestones) {
    const rr = run(tape.slice(0, n));
    if (!rr.ok || rr.output.indexOf(marker) < 0) {
      console.error("self-check FAILED at event " + n + ": missing " + JSON.stringify(marker));
      console.error((rr.output || "").split("\n").slice(-25).join("\n"));
      process.exit(1);
    }
  }
  // the Japanese install path: picking "j" localizes the sysinst screens
  const jpTape = [["power", "on"], ["key", "j"], ["key", "a"], ["key", "b"]];
  for (const [n, marker] of [[2, "インストールシステム"],
                             [3, "インストール先ディスク"],
                             [4, "パーティション方式"]]) {
    const jp = run(jpTape.slice(0, n));
    if (!jp.ok || jp.output.indexOf(marker) < 0) {
      console.error("self-check FAILED (japanese sysinst) at event " + n + ": missing " + JSON.stringify(marker));
      console.error((jp.output || jp.error || "").split("\n").slice(-20).join("\n"));
      process.exit(1);
    }
  }
  console.log("self-check OK: install(rd0, LILO->MBR/GRUB, preinstalled vim/emacs/sshd/xinetd)" +
    " -> boot -> internet over NAT (ping/curl/wget, apt mirror) -> su/sudo user switching" +
    " -> live xterm -> zone:// ultra network -> MigemoInsta -> Ubuntu-sized apt" +
    " -> grub-install/update-grub + os-prober (Ubuntu/Win10/Win11) -> lsusb/bluetoothctl" +
    " -> w9wm/afterstep/wmaker/twm -> mlterm/fcitx-mozc/pLaTeX (日本語) -> xcalc -> udisksctl USB mount -> apt nautilus -> nmcli NAT auto-connect -> git/xcode-select/brew -> BadaApache on zone://url.or.jp (" + tape.length + " ledger events)");
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
