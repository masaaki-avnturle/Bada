#!/usr/bin/env node
/* ============================================================================
 * qshark-capture.js — QuantumShark capture engine.
 *
 * Captures packets on YOUR OWN machine's interface (via tshark / tcpdump /
 * dumpcap, whichever is installed) and writes an ENCRYPTED capture file
 * (.qcap) sealed with the Jones-polynomial quantum cipher. The capture is
 * encrypted at rest with a master password; open it in dist/quantum-shark.html.
 *
 * Usage:
 *   node qshark-capture.js --master <pw> [--iface <if>] [--count 200] [--filter <bpf>] [-o capture.qcap]
 *   node qshark-capture.js --master <pw> --demo -o demo.qcap     # no capture tool needed
 *
 * Defensive use only: this captures traffic on interfaces you control.
 * ==========================================================================*/
"use strict";
const fs = require("fs");
const path = require("path");
const { execSync, spawnSync } = require("child_process");

const IDE = path.join(__dirname, "..", "..");
const Bada = require(path.join(IDE, "www", "bada.js"));
const cipherLib = fs.readFileSync(path.join(IDE, "modemvault", "modemvault-lib.bada"), "utf8");

function arg(name, def){ const i=process.argv.indexOf(name); return i>=0 && i+1<process.argv.length ? process.argv[i+1] : def; }
function has(name){ return process.argv.indexOf(name)>=0; }

const master = arg("--master", process.env.QSHARK_MASTER || "");
const iface  = arg("--iface", "");
const count  = parseInt(arg("--count","200"),10);
const bpf    = arg("--filter","");
const outPath= arg("-o","capture.qcap");
const demo   = has("--demo");

if(!master){ console.error("error: --master <password> is required (encryption key for the .qcap)"); process.exit(1); }

function which(c){ try{ execSync((process.platform==="win32"?"where ":"command -v ")+c,{stdio:"ignore"}); return true; }catch(e){ return false; } }

function demoRecords(){
  return [
    {no:1,time:"0.000000",src:"192.168.0.23",dst:"192.168.0.1",proto:"DNS",len:74,info:"Standard query A example.com"},
    {no:2,time:"0.004120",src:"192.168.0.1",dst:"192.168.0.23",proto:"DNS",len:90,info:"Standard query response A 93.184.216.34"},
    {no:3,time:"0.005001",src:"192.168.0.23",dst:"93.184.216.34",proto:"TCP",len:74,info:"49832 > 443 [SYN] Seq=0 Win=64240"},
    {no:4,time:"0.028744",src:"93.184.216.34",dst:"192.168.0.23",proto:"TCP",len:74,info:"443 > 49832 [SYN, ACK] Seq=0 Ack=1"},
    {no:5,time:"0.029001",src:"192.168.0.23",dst:"93.184.216.34",proto:"TLSv1.3",len:583,info:"Client Hello"},
    {no:6,time:"0.052210",src:"192.168.0.23",dst:"192.168.0.1",proto:"ARP",len:42,info:"Who has 192.168.0.1? Tell 192.168.0.23"}
  ];
}

function captureTshark(){
  const args=["-i", iface||"any", "-c", String(count), "-T","fields",
    "-e","frame.number","-e","frame.time_relative","-e","ip.src","-e","ip.dst",
    "-e","_ws.col.Protocol","-e","frame.len","-e","_ws.col.Info","-E","separator=\t"];
  if(bpf) args.push("-f", bpf);
  const r=spawnSync("tshark", args, {encoding:"utf8", timeout:120000});
  if(r.status!==0) throw new Error(r.stderr||"tshark failed");
  const recs=[];
  r.stdout.split("\n").forEach(line=>{ if(!line.trim())return;
    const f=line.split("\t");
    recs.push({no:parseInt(f[0]||"0",10),time:f[1]||"",src:f[2]||"",dst:f[3]||"",proto:f[4]||"",len:parseInt(f[5]||"0",10),info:f[6]||""});
  });
  return recs;
}
function captureTcpdump(){
  const args=["-i", iface||"any","-c",String(count),"-nn","-l","-tt"];
  if(bpf) args.push(bpf);
  const r=spawnSync("tcpdump", args, {encoding:"utf8", timeout:120000});
  if(r.status!==0) throw new Error(r.stderr||"tcpdump failed");
  const recs=[]; let n=1;
  r.stdout.split("\n").forEach(line=>{ if(!line.trim())return;
    const m=/^(\d+\.\d+)\s+(\S+)?\s*(.*?)([0-9.]+)\.\d+\s*>\s*([0-9.]+)\.\d+:?(.*)$/.exec(line);
    if(m){ recs.push({no:n++,time:m[1],src:m[4],dst:m[5],proto:(m[2]||"").toUpperCase()||"IP",len:0,info:(m[6]||"").trim().slice(0,120)}); }
    else { recs.push({no:n++,time:"",src:"",dst:"",proto:"",len:0,info:line.slice(0,140)}); }
  });
  return recs;
}

function seal(plain){
  const salt=1+Math.floor(((Date.now()%4000)+1));  /* nonce; Date is fine here (Node) */
  let out=[];
  Bada.run(cipherLib+"\nvault_seal("+JSON.stringify(master)+", "+ (salt%4000+1) +", "+JSON.stringify(plain)+")\n",
    {maxSteps:200000000, out:s=>out.push(s)});
  const t=out.join("\n");
  const ct=/@@CT (\[[^\]]*\])/.exec(t), tag=/@@TAG (\d+)/.exec(t), sm=/@@SALT (\d+)/.exec(t);
  if(!ct||!tag||!sm) throw new Error("seal failed");
  return { salt:parseInt(sm[1],10), ct:JSON.parse(ct[1]), tag:parseInt(tag[1],10) };
}

function main(){
  let records, sourceTool;
  if(demo){ records=demoRecords(); sourceTool="demo"; }
  else if(which("tshark")){ records=captureTshark(); sourceTool="tshark"; }
  else if(which("tcpdump")){ records=captureTcpdump(); sourceTool="tcpdump"; }
  else {
    console.error("No capture tool found (tshark / tcpdump).");
    console.error("Install Wireshark/tshark or tcpdump, or run with --demo to emit a sample .qcap.");
    process.exit(2);
  }
  const plain=JSON.stringify(records);
  const sealed=seal(plain);
  const check=seal("qshark-ok");
  const qcap={ magic:"QCAP1", tool:sourceTool, count:records.length, check:check, cap:sealed };
  fs.writeFileSync(outPath, JSON.stringify(qcap));
  console.log("captured "+records.length+" packets via "+sourceTool);
  console.log("encrypted with the Jones quantum cipher -> "+outPath);
  console.log("open it in dist/quantum-shark.html with your master password.");
}
main();
