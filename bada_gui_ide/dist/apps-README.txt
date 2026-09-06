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
  earth-twin.html     GammaTwin — 地球型惑星ファインダー: ranks planets whose
                      conditions are isomorphic to Earth using the free NASA
                      Exoplanet Archive (Kepler/TESS space-telescope catalog)
                      + CDS sky-survey imagery. ESI scoring gamma-normalized
                      via Γ(z+1)=zΓ(z); trefoil Jones polynomial |V(e^iθ)|
                      drives the heat palette. Offline snapshot included.
  planet-cinema.html  PlanetCinema — 見つかった惑星の動画館: parameter-driven
                      animated video of the planets GammaTwin finds (same NASA
                      space-telescope catalog). Complex rotation z=e^{iωt},
                      real special relativity (Lorentz γ, Doppler D, light
                      aberration on the starfield), Jones-heat surface classes,
                      Kepler orbit estimates, and MediaRecorder .webm export.
  geo-signal.html     GeoSignal — 地球の伝達使用地点シアター: the real places
                      on Earth (and the ISS overhead) where the EM/gravity
                      channels are actually in use — deep-space transmitters,
                      radio telescopes, GW detectors (KAGRA/LIGO/Virgo) —
                      each viewable as a looping space-to-ground zoom movie
                      from public map tiles, recordable to .webm. Honest note:
                      no anti-gravity facility exists.
  anomaly-map.html    AnomalyMap — 宇宙人らしき信号の場所特定アトラス: the real
                      signals history seriously considered as possibly alien
                      (Wow!, BLC1, LGM-1, Parkes perytons, 'Oumuamua, Tabby's
                      star, FRBs…) with their real coordinates and how each
                      source was pinpointed (human / natural / still open —
                      only Wow! remains unresolved). DSS2 sky cutouts + ground
                      tile views. Honest banner: zero confirmed alien sites.
  heat-sense.html     HeatSense — 未知の伝達チャネル模索シアター: the real
                      searches for channels beyond EM/gravity — thermal
                      (Dyson waste-heat IR, Wien's law computed live with the
                      Jones heat palette), neutrinos (human comms DEMONSTRATED
                      at Fermilab 2012; Super-K / IceCube listening), axions
                      (ADMX), cosmic rays — and entanglement honestly excluded
                      (no-communication theorem). Ground zoom movies + sky
                      fov-zoom movies (DSS2), .webm recording. Zero detections
                      to date, stated up front.
  bio-therm.html      BioThermNet — 知的生命体 熱感知ネットワーク: a wit
                      network of the discovered exoplanets. The Γ global
                      integration manifold totals the network's sensed
                      thermal budget (大域積分 Q = Σ P_bio); the global
                      differential manifold gives each node's heat gradient
                      d|V|/dθ on the trefoil Jones curve. Each planet's REAL
                      measured physics (Kleiber's law P=3.4W·M^0.75 —
                      validated 70kg→82W —, Stefan-Boltzmann radiator area,
                      Allen's rule, g=R^1.58·g⊕, star color) deterministically
                      shapes a procedural intelligent-lifeform illustration,
                      each feature annotated with its formula; PNG download +
                      .webm network recording. Honest banner: ZERO detections
                      of intelligent life as of 2026 — these are
                      physics-consistent illustrations, not observations.
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
