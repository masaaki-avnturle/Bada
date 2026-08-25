#!/usr/bin/env node
/* ============================================================================
 * modem-scan.js — detect the modem / router (default gateway) on YOUR OWN LAN.
 *
 * Reports only what the OS already knows about your own machine and its
 * gateway: your LAN IP/subnet, the default-gateway IP, the gateway's MAC
 * (from the ARP/neighbor table), the MAC vendor (OUI lookup), and the likely
 * admin-page URL. It never reads, derives, or displays any password — routers
 * do not serve their passwords over the LAN, and this tool does not try.
 *
 * Cross-platform: Linux / macOS / Windows.
 *   node modem-scan.js
 * ==========================================================================*/
"use strict";
const os = require("os");
const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

function sh(cmd) {
  try { return execSync(cmd, { encoding: "utf8", timeout: 8000, stdio: ["ignore", "pipe", "ignore"] }); }
  catch (e) { return ""; }
}

function loadOui() {
  try {
    const j = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "oui.json"), "utf8"));
    return j.prefixes || {};
  } catch (e) { return {}; }
}
function vendorOf(mac, oui) {
  if (!mac) return "";
  const p = mac.toUpperCase().replace(/-/g, ":").split(":").slice(0, 3).join(":");
  return oui[p] || "";
}

/* your own LAN IPv4 interfaces */
function localIfaces() {
  const out = [];
  const ifs = os.networkInterfaces();
  for (const name of Object.keys(ifs)) {
    for (const a of ifs[name] || []) {
      if (a.family === "IPv4" && !a.internal) out.push({ name, ip: a.address, mac: a.mac, cidr: a.cidr });
    }
  }
  return out;
}

/* default gateway IP, cross-platform */
function defaultGateway() {
  const plat = process.platform;
  if (plat === "linux") {
    let o = sh("ip route show default");
    let m = /default via (\d+\.\d+\.\d+\.\d+)/.exec(o);
    if (m) return m[1];
    o = sh("route -n");
    m = /^0\.0\.0\.0\s+(\d+\.\d+\.\d+\.\d+)/m.exec(o);
    if (m) return m[1];
  } else if (plat === "darwin") {
    const o = sh("route -n get default");
    const m = /gateway:\s*(\d+\.\d+\.\d+\.\d+)/.exec(o);
    if (m) return m[1];
  } else if (plat === "win32") {
    const o = sh("chcp 65001>nul & route print 0.0.0.0");
    const m = /0\.0\.0\.0\s+0\.0\.0\.0\s+(\d+\.\d+\.\d+\.\d+)/.exec(o);
    if (m) return m[1];
  }
  /* fallback: guess x.x.x.1 from the first LAN interface */
  const ifc = localIfaces()[0];
  if (ifc) { const p = ifc.ip.split("."); p[3] = "1"; return p.join("."); }
  return "";
}

/* MAC of an IP from the ARP / neighbor table */
function macOf(ip) {
  if (!ip) return "";
  const plat = process.platform;
  let o = "";
  if (plat === "linux") { o = sh("ip neigh show " + ip) || sh("arp -n " + ip); }
  else if (plat === "darwin") { o = sh("arp -n " + ip); }
  else if (plat === "win32") { o = sh("arp -a " + ip); }
  const m = /([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}/.exec(o);
  return m ? m[0].replace(/-/g, ":").toUpperCase() : "";
}

function main() {
  const oui = loadOui();
  const ifaces = localIfaces();
  const gw = defaultGateway();
  /* prime the ARP entry, then read it */
  if (gw && process.platform !== "win32") sh((process.platform === "darwin" ? "ping -c1 -t1 " : "ping -c1 -W1 ") + gw);
  if (gw && process.platform === "win32") sh("ping -n 1 -w 1000 " + gw);
  const gwMac = macOf(gw);
  const vendor = vendorOf(gwMac, oui);

  console.log("============================================================");
  console.log(" LAN modem / router detection  (your own network only)");
  console.log("============================================================");
  console.log("");
  console.log("your PC interfaces:");
  if (!ifaces.length) console.log("  (none found)");
  for (const f of ifaces) console.log("  " + f.name + "  ip " + f.ip + "  (" + (f.cidr || "") + ")  mac " + (f.mac || ""));
  console.log("");
  console.log("default gateway (your modem/router):");
  console.log("  IP        : " + (gw || "(not found)"));
  console.log("  MAC       : " + (gwMac || "(not in ARP table)"));
  console.log("  vendor    : " + (vendor || "(unknown OUI)"));
  if (gw) {
    console.log("  admin page: http://" + gw + "/   (https://" + gw + "/ )");
  }
  console.log("");
  console.log("note: passwords are never shown. To sign in, open the admin page");
  console.log("      above and use the credentials on your device's label, or the");
  console.log("      ones you saved in the Modem Vault (quantum-cipher vault).");
  console.log("============================================================");
}

main();
