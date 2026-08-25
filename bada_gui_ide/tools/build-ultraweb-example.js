#!/usr/bin/env node
/* ============================================================================
 * build-ultraweb-example.js — generate examples/ultraweb.bada, the evolved
 * ultra-network WWW that FUSES the earlier ultranetwork (the UltraDatabase /
 * Omega.DATABASE[first..fourth] distributed store + cognitive_system /
 * manifold_scan) into the zone:// scheme (P2P DHT + Jones quantum cipher).
 *
 * The file = browser/zone-lib.bada (the fused runtime) + a human-readable
 * demo driver, so it runs standalone in the interpreter / GUI IDE / CLI.
 * ==========================================================================*/
"use strict";
const fs = require("fs");
const path = require("path");
const IDE = path.join(__dirname, "..");
const lib = fs.readFileSync(path.join(IDE, "browser", "zone-lib.bada"), "utf8");

const demo = `
# ============================================================
# ultraweb.bada -- the EVOLVED ultra-network WWW (auto-generated:
#   browser/zone-lib.bada runtime  +  this demo driver).
#
# Fusion of the earlier ultranetwork (Omega.DATABASE[first,second,
# third,fourth] UltraDatabase + cognitive_system / manifold_scan)
# with the zone:// scheme (P2P DHT + Jones-polynomial quantum
# cipher + Bell-pair QKD + Akashic ledger):
#   * every zone record is REPLICATED across the 4 nearest peers
#     (Omega.DATABASE[1..4]); a quorum read out-votes and HEALS a
#     forged replica -- no single point of failure, Byzantine-tamper
#     tolerant.
#   * a cognitive_system SEARCH ranks the whole zone by relevance
#     (softmax = |psi|^2 on the phase core = the emerge_equation).
# ============================================================

def show_get(net, url) {
    print("")
    print("GET " + url)
    p := zone_parse(url)
    if (len(p) == 0) { print("  400 not a zone:// URL"); return "" }
    host := p[0]
    key := zone_id(url)
    jk := jones_key(zone_diagram(host))
    reps := dht_replicas(net, key)
    total := len(reps)
    good := 0
    present := 0
    have := false
    body := ""
    gs := []
    i := 0
    while (i < total) {
        rec := store_lookup(reps[i][2], url)
        if (len(rec) > 0) {
            present := present + 1
            opened := zone_open([ rec[1], rec[2], rec[3] ], jk)
            if (len(opened) > 0) {
                good := good + 1
                if (!have) { body := opened[0]; gs := [ rec[1], rec[2], rec[3] ]; have := true }
            }
        }
        i := i + 1
    }
    if (present == 0) { print("  404 zone-not-found (no replica holds it)"); return "" }
    if (!have) { print("  409 zone-guard-reject (quorum 0/" + total + ": all replicas forged)"); return "" }
    repaired := 0
    i := 0
    while (i < total) {
        rec := store_lookup(reps[i][2], url)
        bad := false
        if (len(rec) == 0) { bad := true }
        else { if (len(zone_open([ rec[1], rec[2], rec[3] ], jk)) == 0) { bad := true } }
        if (bad) { store_put(reps[i], url, gs); repaired := repaired + 1 }
        i := i + 1
    }
    if (repaired > 0) { ["zone-heal", url, repaired] >> tuplespace }
    print("  200 zone-delivered  quorum " + good + "/" + total + "  self-healed " + repaired + "  jones-key " + jk)
    print("  body: " + body)
    return body
}

def show_search(net, urls, query) {
    print("")
    print("search: \\"" + query + "\\"")
    terms := split(query, " ")
    logits := []
    raw := []
    i := 0
    while (i < len(urls)) {
        sc := score_text(zone_read_plain(net, urls[i]), terms)
        raw <- sc
        if (sc > 0) { logits <- sc } else { logits <- (0 - 40.0) }
        i := i + 1
    }
    rel := cognitive_system(logits, [], [])
    print("  relevance entropy = " + entropy(rel) + "  (softmax = |psi|^2)")
    used := []
    i := 0
    while (i < len(urls)) { used <- 0; i := i + 1 }
    ranked := 0
    while (ranked < len(urls)) {
        best := 0 - 1
        bv := 0
        j := 0
        while (j < len(urls)) {
            if (used[j] == 0) {
                if (best < 0) { best := j; bv := rel[j] }
                else { if (rel[j] > bv) { best := j; bv := rel[j] } }
            }
            j := j + 1
        }
        used[best] = 1
        if (raw[best] > 0) { print("  " + f5(rel[best]) + "  " + urls[best]) }
        ranked := ranked + 1
    }
}

def forge_replica(net, url, n) {
    reps := dht_replicas(net, zone_id(url))
    i := 0
    while (i < n && i < len(reps)) {
        rec := store_lookup(reps[i][2], url)
        if (len(rec) > 0) { rec[1][0] = (rec[1][0] + 13) % 65536 }
        i := i + 1
    }
}

print("================================================================")
print("ULTRAWEB -- evolved ultra-network WWW (UltraDB quorum + zone:// + Jones cipher)")
print("================================================================")

NET := zone_boot()
print("")
print("ring peers (server-less P2P), REPLICAS = " + REPLICAS + " (Omega.DATABASE[1..4]):")
for pr in NET { print("  node " + pr[3] + " : " + pr[0] + "  id " + pr[1]) }

# ---- publish a small ultra-web, each page replicated across 4 peers --
zone_publish(NET, "zone://url.or.jp/",              "# Ultra Network\\nthe worldwide web with no http and no center\\n-> zone://url.or.jp/labs | quantum labs")
zone_publish(NET, "zone://url.or.jp/labs",          "# Quantum Labs\\nqubit gates and the Jones cipher on the phase core")
zone_publish(NET, "zone://url.or.jp/security",      "# Security\\nJones polynomial key, Bell QKD, AEAD guard")
zone_publish(NET, "zone://bada.or.jp/",             "# Bada portal\\nthe quantum programming language of the ultra network")

print("")
print("--- resilient read (all 4 replicas healthy) ---")
show_get(NET, "zone://url.or.jp/")

print("")
print("--- Byzantine attack: forge 2 of the 4 replicas, then read ---")
forge_replica(NET, "zone://url.or.jp/", 2)
show_get(NET, "zone://url.or.jp/")
print("--- read again: the quorum has self-healed the forged replicas ---")
show_get(NET, "zone://url.or.jp/")

print("")
print("--- total forgery: corrupt ALL 4 replicas -> rejected ---")
forge_replica(NET, "zone://url.or.jp/", 4)
show_get(NET, "zone://url.or.jp/")
print("--- republish from the source heals the whole quorum ---")
zone_publish(NET, "zone://url.or.jp/", "# Ultra Network\\nrestored across the UltraDatabase quorum from the source")
show_get(NET, "zone://url.or.jp/")

print("")
print("================================================================")
print("cognitive_system search (emerge_equation: softmax = |psi|^2 phase core)")
print("================================================================")
INDEX := ["zone://url.or.jp/", "zone://url.or.jp/labs", "zone://url.or.jp/security", "zone://bada.or.jp/"]
show_search(NET, INDEX, "quantum")
show_search(NET, INDEX, "Jones")
show_search(NET, INDEX, "Bada")

print("")
print("Akashic zone table: ledger = " + len(tuplespace) + " append-only facts")
print("(replicated records + fetches + heals + measurements + search reweights)")
print("================================================================")
`;

const out = lib.trimEnd() + "\n" + demo;
fs.writeFileSync(path.join(IDE, "examples", "ultraweb.bada"), out);
console.log("wrote examples/ultraweb.bada (" + out.length + " bytes)");
