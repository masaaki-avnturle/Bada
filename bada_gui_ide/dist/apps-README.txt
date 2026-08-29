Ultra Network apps — Bada quantum programming language
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
  earth-view.html     Orbita — 衛星から見る地球: LIVE views of Earth from
                      free public satellites (Himawari-9, GOES-19/18, Meteosat,
                      NASA DSCOVR/EPIC) animated into video, plus a real SGP4
                      pass predictor (inlined satellite.js) for the NOAA/ISS
                      satellites you can receive yourself. Needs internet.
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
