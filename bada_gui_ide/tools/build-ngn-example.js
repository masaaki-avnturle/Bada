#!/usr/bin/env node
/* ============================================================================
 * build-ngn-example.js — generate examples/ngn-quantum.bada: the zone://
 * ultra-network PROJECTED ONTO THE NTT NGN line, fusing the HDD pseudo-quantum
 * computer (sectors hold |psi|^2), entanglement (Bell pairs over NTT lines),
 * the Von-Neumann home/office PCs, and zone://url.or.jp (UltraDB + Jones cipher).
 *
 * File = browser/zone-lib.bada + ngngrid/ngn-extra.bada + a readable driver.
 * ==========================================================================*/
"use strict";
const fs = require("fs");
const path = require("path");
const IDE = path.join(__dirname, "..");
const zoneLib = fs.readFileSync(path.join(IDE, "browser", "zone-lib.bada"), "utf8");
const ngnExtra = fs.readFileSync(path.join(IDE, "ngngrid", "ngn-extra.bada"), "utf8");

const driver = `
# ============================================================
# ngn-quantum.bada -- AUTO-GENERATED (zone-lib + ngn-extra + demo).
# The ultra-network zone://url.or.jp projected onto the NTT NGN.
# ============================================================

def show_entangle(a, b) {
    bell := hdd_bell()
    ok := "TAPPED"
    if ((bell[1] == 0) && (bell[2] == 0)) { ok := "intact" }
    print("  " + a + "  <=NTT=>  " + b + "   |00>=" + f5(bell[0]) + " |11>=" + f5(bell[3]) + "   entanglement: " + ok)
    fact := ["ngn-entangle", a, b]
    fact >> tuplespace
    return bell
}
def show_get(net, who, url) {
    p := zone_parse(url)
    host := p[0]
    key := zone_id(url)
    reps := dht_replicas(net, key)
    jk := jones_key(zone_diagram(host))
    good := 0
    body := ""
    have := false
    i := 0
    while (i < len(reps)) {
        rec := store_lookup(reps[i][2], url)
        if (len(rec) > 0) {
            opened := zone_open([ rec[1], rec[2], rec[3] ], jk)
            if (len(opened) > 0) { good := good + 1; if (!have) { body := opened[0]; have := true } }
        }
        i := i + 1
    }
    if (!have) { print("  " + who + " -> " + url + " : NOT AVAILABLE"); return "" }
    print("  " + who + " -> " + url)
    print("    200 over NTT NGN   quorum " + good + "/" + len(reps) + "   jones-key " + jk)
    print("    body: " + body)
    return body
}

print("================================================================")
print("NGN QUANTUM GRID -- zone://url.or.jp projected onto the NTT NGN line")
print("================================================================")

NET := zone_boot()
print("")
print("NTT NGN backbone (regional offices = zone ring peers, UltraDB x" + REPLICAS + "):")
for pr in NET { print("  NGN-" + pr[0] + "   id " + pr[1]) }

print("")
print("home/office PCs (Von-Neumann) on NTT subscriber lines, each an")
print("HDD-backed pseudo-quantum register (sectors hold |psi|^2):")
homePC := pc_new("home-PC (Tokyo)",   "192.168.0.23", 4)
offPC  := pc_new("office-PC (Osaka)",  "192.168.10.5", 0)
nasPC  := pc_new("NAS (Nagoya)",       "192.168.20.9", 1)
print("  " + homePC[0] + "  ip " + homePC[1] + "  hdd|0>^2 = " + f5(homePC[3][0]))
print("  " + offPC[0]  + "  ip " + offPC[1]  + "  hdd|0>^2 = " + f5(offPC[3][0]))
print("  " + nasPC[0]  + "  ip " + nasPC[1]  + "  hdd|0>^2 = " + f5(nasPC[3][0]))

print("")
print("--- entanglement over NTT lines (Bell pairs; zero-preservation = tap-evidence) ---")
show_entangle(homePC[0], offPC[0])
show_entangle(homePC[0], nasPC[0])
show_entangle(offPC[0],  nasPC[0])

print("")
print("--- project each PC's IP onto the NGN-replicated zone table ---")
ngn_register(NET, homePC[1], homePC[2])
ngn_register(NET, offPC[1],  offPC[2])
ngn_register(NET, nasPC[1],  nasPC[2])
print("  projected: " + homePC[1] + ", " + offPC[1] + ", " + nasPC[1] + " -> zone://url.or.jp/lan/<ip>")

print("")
print("--- publish the ultra-network WWW across the NGN, then browse it over NTT ---")
zone_publish(NET, "zone://url.or.jp/", "# Ultra Network over NTT NGN | no http, no center | entangled home/office PCs")
zone_publish(NET, "zone://url.or.jp/lan/", "# NGN LAN index | home/office nodes projected onto NTT")
show_get(NET, homePC[0], "zone://url.or.jp/")
show_get(NET, offPC[0],  "zone://url.or.jp/lan/" + homePC[1])

print("")
print("Akashic/NGN ledger = " + len(tuplespace) + " append-only facts")
print("(entanglements + node projections + replicated zone records + measurements)")
print("================================================================")
`;

const out = zoneLib.trimEnd() + "\n" + ngnExtra.trimEnd() + "\n" + driver;
fs.writeFileSync(path.join(IDE, "examples", "ngn-quantum.bada"), out);
console.log("wrote examples/ngn-quantum.bada (" + out.length + " bytes)");
