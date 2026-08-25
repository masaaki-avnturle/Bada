#!/usr/bin/env node
/* ============================================================================
 * ngn-project.js — project THIS machine onto the NGN Quantum Grid: detect its
 * own LAN IP(s), register them into the NGN-replicated zone table
 * (zone://url.or.jp/lan/<ip>), entangle this PC with the regional NGN nodes
 * (Bell pairs over "NTT lines"), and browse zone://url.or.jp over the NGN.
 *
 * Simulation over the existing zone runtime (browser/zone-lib.bada) +
 * ngngrid/ngn-extra.bada. Reads only your own machine's addresses.
 *   node ngn-project.js
 * ==========================================================================*/
"use strict";
const os = require("os");
const fs = require("fs");
const path = require("path");

const IDE = path.join(__dirname, "..", "..");
const Bada = require(path.join(IDE, "www", "bada.js"));
const lib = fs.readFileSync(path.join(IDE, "browser", "zone-lib.bada"), "utf8") + "\n" +
            fs.readFileSync(path.join(IDE, "ngngrid", "ngn-extra.bada"), "utf8");

function localIps(){
  const out=[]; const ifs=os.networkInterfaces();
  for(const name of Object.keys(ifs))
    for(const a of ifs[name]||[])
      if(a.family==="IPv4" && !a.internal) out.push({name,ip:a.address});
  return out;
}
function J(s){ return JSON.stringify(String(s)); }

function main(){
  const ips=localIps();
  if(!ips.length){ console.error("no LAN IPv4 found"); process.exit(1); }

  let prog=lib+"\nNET := zone_boot()\n";
  /* entangle this PC with each regional NGN node */
  prog+='print("NTT NGN backbone (regional offices):")\n';
  prog+='for pr in NET { print("  NGN-" + pr[0] + "  id " + pr[1]) }\n';
  prog+='print("")\nprint("entangle this PC with the NGN nodes (Bell over NTT):")\n';
  ips.forEach(f=>{ prog+='entangle_show('+J("this-PC@"+f.ip)+', '+J("NGN-backbone")+')\n'; });
  /* register + fetch */
  ips.forEach(f=>{ prog+='ngn_register(NET, '+J(f.ip)+', 0)\n'; });
  prog+='zone_publish(NET, "zone://url.or.jp/", "# Ultra Network over NTT NGN")\n';
  prog+='zone_serve(NET, "zone://url.or.jp/")\n';
  ips.forEach(f=>{ prog+='zone_serve(NET, '+J("zone://url.or.jp/lan/"+f.ip)+')\n'; });

  let out=[];
  Bada.run(prog,{maxSteps:200000000,out:s=>out.push(s)});
  const text=out.join("\n");

  console.log("============================================================");
  console.log(" NGN Quantum Grid — project this machine onto the NTT NGN");
  console.log("============================================================");
  /* readable backbone + entanglement lines */
  text.split("\n").forEach(l=>{
    if(l.startsWith("NTT NGN")||l.startsWith("  NGN-")||l.startsWith("entangle ")) console.log(l);
    else if(l.startsWith("@@BELL ")){ const f=l.split(" "); console.log("  "+f[1]+"  <=NTT=>  "+f[2]+"   |00>="+f[3]+" |11>="+f[6]+"   entanglement: "+(f[7]==="1"?"intact":"TAPPED")); }
  });
  console.log("");
  console.log("projected IPs -> zone://url.or.jp/lan/<ip>:");
  ips.forEach(f=>console.log("  "+f.ip+" ("+f.name+")"));
  /* served blocks */
  const blocks=text.split("@@HOST").slice(1);
  console.log("");
  console.log("browse over NTT NGN:");
  blocks.forEach(b=>{
    const path0=/@@PATH (\S+)/.exec(b), st=/@@STATUS (\S+)/.exec(b), q=/@@QUORUM (\d+ \d+)/.exec(b), jk=/@@JONESKEY (\d+)/.exec(b);
    if(st) console.log("  zone://url.or.jp"+(path0?path0[1]:"/")+"   status "+st[1]+"   quorum "+(q?q[1]:"?")+"   jones-key "+(jk?jk[1]:"?"));
  });
  console.log("============================================================");
}
main();
