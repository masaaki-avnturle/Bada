#!/usr/bin/env node
/* ============================================================================
 * lan-to-zone.js — import the IP addresses on YOUR OWN PC / LAN into the
 * ultra-network as encrypted zone:// records under zone://url.or.jp/lan/.
 *
 * Reads your own machine's IPv4 interfaces (and default gateway), then runs
 * the zone:// runtime (browser/zone-lib.bada) to publish each IP as a page
 * replicated across the UltraDatabase quorum and sealed with the Jones
 * quantum cipher, and reads each back to confirm 200 + quorum.
 *
 *   node lan-to-zone.js
 * ==========================================================================*/
"use strict";
const os = require("os");
const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

const IDE = path.join(__dirname, "..", "..");
const Bada = require(path.join(IDE, "www", "bada.js"));
const zoneLib = fs.readFileSync(path.join(IDE, "browser", "zone-lib.bada"), "utf8");

function sh(c){ try{ return execSync(c,{encoding:"utf8",timeout:6000,stdio:["ignore","pipe","ignore"]}); }catch(e){ return ""; } }

function localIps(){
  const out=[]; const ifs=os.networkInterfaces();
  for(const name of Object.keys(ifs))
    for(const a of ifs[name]||[])
      if(a.family==="IPv4" && !a.internal) out.push({name,ip:a.address,mac:a.mac,cidr:a.cidr});
  return out;
}
function gateway(){
  if(process.platform==="linux"){ const m=/default via (\d+\.\d+\.\d+\.\d+)/.exec(sh("ip route show default")); if(m)return m[1]; }
  else if(process.platform==="darwin"){ const m=/gateway:\s*(\d+\.\d+\.\d+\.\d+)/.exec(sh("route -n get default")); if(m)return m[1]; }
  else if(process.platform==="win32"){ const m=/0\.0\.0\.0\s+0\.0\.0\.0\s+(\d+\.\d+\.\d+\.\d+)/.exec(sh("route print 0.0.0.0")); if(m)return m[1]; }
  return "";
}
function J(s){ return JSON.stringify(String(s)); }

function main(){
  const ifaces=localIps();
  const gw=gateway();
  const nodes=[];
  ifaces.forEach(f=>nodes.push({ip:f.ip,label:f.name+" (this PC)"}));
  if(gw) nodes.push({ip:gw,label:"default gateway (modem)"});

  if(!nodes.length){ console.error("no LAN IPv4 addresses found"); process.exit(1); }

  const at=new Date().toISOString().slice(0,19).replace("T"," ");
  let prog=zoneLib+"\nNET := zone_boot()\n";
  nodes.forEach(n=>{
    const page="# LAN node "+n.ip+"\\nlabel: "+n.label+"\\nimported: "+at;
    prog+="zone_publish(NET, "+J("zone://url.or.jp/lan/"+n.ip)+", "+J(page)+")\n";
  });
  const idx="# LAN zone index\\n"+nodes.map(n=>"-> zone://url.or.jp/lan/"+n.ip+" | "+n.ip+" ("+n.label+")").join("\\n");
  prog+="zone_publish(NET, "+J("zone://url.or.jp/lan/")+", "+J(idx)+")\n";
  nodes.forEach(n=>{ prog+="zone_serve(NET, "+J("zone://url.or.jp/lan/"+n.ip)+")\n"; });

  let out=[];
  Bada.run(prog,{maxSteps:20000000,out:s=>out.push(s)});
  const text=out.join("\n");

  console.log("============================================================");
  console.log(" LAN -> zone://url.or.jp  import  (your own machine only)");
  console.log("============================================================");
  console.log("");
  /* parse each served block */
  const blocks=text.split("@@HOST").slice(1);
  let i=0;
  for(const b of blocks){
    const st=/@@STATUS (\S+)/.exec(b), q=/@@QUORUM (\d+ \d+)/.exec(b), jk=/@@JONESKEY (\d+)/.exec(b), tg=/@@TAG (\d+)/.exec(b);
    const n=nodes[i++]; if(!n) break;
    console.log("zone://url.or.jp/lan/"+n.ip+"   ["+n.label+"]");
    console.log("  status "+(st?st[1]:"?")+"   quorum "+(q?q[1]:"?")+"   jones-key "+(jk?jk[1]:"?")+"   tag "+(tg?tg[1]:"?"));
  }
  console.log("");
  console.log("index: zone://url.or.jp/lan/   ("+nodes.length+" nodes, replicated across the UltraDB quorum, Jones-encrypted)");
  console.log("============================================================");
}

main();
