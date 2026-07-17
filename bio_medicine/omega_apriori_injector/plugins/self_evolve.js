/*
 * plugins/self_evolve.js — テロメア分裂で実行時自己進化＋一意の機能(UID)プラグイン
 *
 * 付加した未知事前エンジンを、ホスト内で「テロメア分裂・自己進化」させ(genomeを更新)、
 * ゲノムから一意フィンガープリント(UID=一意の機能)を導く。さらに、進化ループとゲノムを
 * 内蔵した「自己進化できるソースコード」を生成する。
 *
 *   run(engine,"uid")                 → 一意ID 文字列 (genomeから決定論的)
 *   run(engine,"step",{target,gens})  → ホスト内でテロメア自己進化(genome更新), 統計を返す
 *   run(engine,"source","js"|"py")    → 自己進化できるソースコード(進化ループ内蔵)を生成
 *
 * ⚠ 概念実証・教育用。
 */
(function (global) {
  "use strict";
  var CELL_BYTES = 6;

  function hexToBytes(h) { h = (h || "").replace(/[^0-9a-fA-F]/g, ""); var n = h.length >> 1, b = new Uint8Array(n);
    for (var i = 0; i < n; i++) b[i] = parseInt(h.substr(i * 2, 2), 16); return b; }
  function bytesHex(b) { return Array.prototype.map.call(b, function (x) { return x.toString(16).padStart(2, "0"); }).join(""); }
  // FNV-1a → base36 (一意フィンガープリント)
  function fnv(s) { var h = 2166136261 >>> 0; for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
  function uidOf(cfg, hex) {
    var a = fnv(hex), b = fnv(hex + JSON.stringify(cfg) + "Ω");
    return "OAE-" + a.toString(36).toUpperCase().padStart(7, "0") + "-" + b.toString(36).toUpperCase().padStart(7, "0");
  }
  function evalFab(cfg, g, x) {
    var prev = x & ((1 << cfg.inbits) - 1), src = cfg.inbits, cur = 0;
    for (var L = 0; L < cfg.layers; L++) { cur = 0;
      for (var w = 0; w < cfg.width; w++) { var cell = L * cfg.width + w, p = cell * CELL_BYTES, addr = 0;
        for (var k = 0; k < 4; k++) { var sel = g[p + k] % Math.max(1, (L === 0 ? cfg.inbits : cfg.width)); if (sel >= src) sel = src ? sel % src : 0; addr |= ((prev >> sel) & 1) << k; }
        cur |= (((g[p + 4] | (g[p + 5] << 8)) >> addr) & 1) << w; }
      prev = cur; src = cfg.width; }
    return cur & ((1 << cfg.outbits) - 1);
  }
  var TARGETS = {
    popcount: function (x) { var c = 0; for (var i = 0; i < 6; i++) c += (x >> i) & 1; return c; },
    parity: function (x) { var c = 0; for (var i = 0; i < 6; i++) c += (x >> i) & 1; return c & 1; }
  };
  function fitness(cfg, g, tf) { var m = 0, t = 0, n = 1 << cfg.inbits;
    for (var x = 0; x < n; x++) { var d = evalFab(cfg, g, x) ^ (tf(x) & ((1 << cfg.outbits) - 1)); for (var b = 0; b < cfg.outbits; b++) { t++; if (!((d >> b) & 1)) m++; } } return m / t; }

  var plugin = {
    name: "self_evolve",
    description: "テロメア分裂で実行時自己進化＋一意の機能(UID)＋自己進化ソース生成",
    run: function (engine, mode, arg) {
      mode = mode || "uid";
      var cfg = engine.cfg;
      if (engine._telomere === undefined) { engine._telomere = 1000; engine._hayflick = 200; }

      if (mode === "uid") return uidOf(cfg, engine.meta.genome_hex);

      if (mode === "step") {
        arg = arg || {};
        var tf = TARGETS[arg.target || "popcount"] || TARGETS.popcount;
        var gens = arg.gens || 12, attr = arg.attrition || 30;
        var g = hexToBytes(engine.meta.genome_hex), gs = g.length;
        var bestG = g.slice(), bf = fitness(cfg, g, tf);
        var uid0 = uidOf(cfg, engine.meta.genome_hex);
        for (var gen = 0; gen < gens && engine._telomere > engine._hayflick; gen++) {
          // テロメア分裂: 子=変異, 良ければ採用 (1+1 進化戦略)
          var child = bestG.slice();
          var frac = (engine._telomere - engine._hayflick) / Math.max(1, 1000 - engine._hayflick);
          var rate = 0.01 + 0.06 * frac;
          for (var i = 0; i < gs; i++) if (Math.random() < rate) child[i] = Math.random() * 256 | 0;
          var f = fitness(cfg, child, tf);
          if (f >= bf) { bf = f; bestG = child; }
          engine._telomere -= attr;             // 分裂=短縮
        }
        var senescent = engine._telomere <= engine._hayflick;
        engine.meta.genome_hex = bytesHex(bestG);
        if (engine.fab && engine.fab.load) engine.fab.load(bestG);   // 進化結果を反映
        return { uid_before: uid0, uid_after: uidOf(cfg, engine.meta.genome_hex),
          fitness: Math.round(bf * 1e4) / 1e4, telomere: engine._telomere, senescent: senescent, gens: gens };
      }

      if (mode === "source") {
        var lang = (arg || "js").toLowerCase();
        var hex = engine.meta.genome_hex, uid = uidOf(cfg, hex);
        if (lang === "py" || lang === "python") return pySource(cfg, hex, uid);
        return jsSource(cfg, hex, uid);
      }
      throw new Error("self_evolve: unknown mode " + mode);
    }
  };

  // ---- 自己進化できる JS モジュール（進化ループ内蔵） ----
  function jsSource(cfg, hex, uid) {
    return "// Self-evolving Omega-Apriori engine — UID " + uid + " (一意の機能)\n" +
"// conceptual/educational only.\n" +
"var OmegaSelfEvolve = (function(){\n" +
"  var CFG=" + JSON.stringify(cfg) + ", CB=6;\n" +
"  var GENOME='" + hex + "';\n" +
"  function h2b(h){var n=h.length>>1,b=new Uint8Array(n);for(var i=0;i<n;i++)b[i]=parseInt(h.substr(i*2,2),16);return b;}\n" +
"  function b2h(b){return Array.prototype.map.call(b,function(x){return x.toString(16).padStart(2,'0');}).join('');}\n" +
"  function fnv(s){var h=2166136261>>>0;for(var i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619);}return h>>>0;}\n" +
"  function uid(){var a=fnv(GENOME),b=fnv(GENOME+JSON.stringify(CFG)+'\\u03a9');return 'OAE-'+a.toString(36).toUpperCase().padStart(7,'0')+'-'+b.toString(36).toUpperCase().padStart(7,'0');}\n" +
"  function infer(x){var g=h2b(GENOME),prev=x&((1<<CFG.inbits)-1),src=CFG.inbits,cur=0;\n" +
"    for(var L=0;L<CFG.layers;L++){cur=0;for(var w=0;w<CFG.width;w++){var cell=L*CFG.width+w,p=cell*CB,addr=0;\n" +
"      for(var k=0;k<4;k++){var sel=g[p+k]%Math.max(1,(L===0?CFG.inbits:CFG.width));if(sel>=src)sel=src?sel%src:0;addr|=((prev>>sel)&1)<<k;}\n" +
"      cur|=(((g[p+4]|(g[p+5]<<8))>>addr)&1)<<w;}prev=cur;src=CFG.width;}return cur&((1<<CFG.outbits)-1);}\n" +
"  var telomere=1000,hayflick=200;\n" +
"  // テロメア分裂・自己進化: target(x)へ向けて 1+1 戦略で genome を更新\n" +
"  function selfEvolve(target,gens){gens=gens||20;var g=h2b(GENOME);\n" +
"    function fit(gg){var m=0,t=0,n=1<<CFG.inbits;for(var x=0;x<n;x++){var y=(function(z){var pv=z&((1<<CFG.inbits)-1),s=CFG.inbits,c=0;for(var L=0;L<CFG.layers;L++){c=0;for(var w=0;w<CFG.width;w++){var cl=L*CFG.width+w,p=cl*CB,a=0;for(var k=0;k<4;k++){var se=gg[p+k]%Math.max(1,(L===0?CFG.inbits:CFG.width));if(se>=s)se=s?se%s:0;a|=((pv>>se)&1)<<k;}c|=(((gg[p+4]|(gg[p+5]<<8))>>a)&1)<<w;}pv=c;s=CFG.width;}return c&((1<<CFG.outbits)-1);})(x);var d=y^(target(x)&((1<<CFG.outbits)-1));for(var b=0;b<CFG.outbits;b++){t++;if(!((d>>b)&1))m++;}}return m/t;}\n" +
"    var bf=fit(g);for(var gen=0;gen<gens&&telomere>hayflick;gen++){var c=g.slice();for(var i=0;i<c.length;i++)if(Math.random()<0.04)c[i]=Math.random()*256|0;var f=fit(c);if(f>=bf){bf=f;g=c;}telomere-=30;}\n" +
"    GENOME=b2h(g);return {fitness:bf,uid:uid(),telomere:telomere,senescent:telomere<=hayflick};}\n" +
"  return {uid:uid,infer:infer,selfEvolve:selfEvolve,genome:function(){return GENOME;},telomere:function(){return telomere;}};\n" +
"})();\n" +
"if(typeof module!=='undefined')module.exports=OmegaSelfEvolve;\n";
  }
  function pySource(cfg, hex, uid) {
    return "# Self-evolving Omega-Apriori engine — UID " + uid + " (unique function)\n" +
"# conceptual/educational only.\n" +
"import random\n" +
"CFG=" + JSON.stringify(cfg) + "; CB=6\n" +
"GENOME='" + hex + "'\n" +
"def _h2b(h): return [int(h[i*2:i*2+2],16) for i in range(len(h)//2)]\n" +
"def _b2h(b): return ''.join('%02x'%x for x in b)\n" +
"def _fnv(s):\n h=2166136261\n for ch in s:\n  h^=ord(ch); h=(h*16777619)&0xffffffff\n return h\n" +
"def uid():\n import json\n a=_fnv(GENOME); b=_fnv(GENOME+json.dumps(CFG)+'\\u03a9')\n" +
" def b36(n):\n  d='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'; s=''\n  while n: s=d[n%36]+s; n//=36\n  return (s or '0').rjust(7,'0')\n return 'OAE-'+b36(a)+'-'+b36(b)\n" +
"def infer(x,g=None):\n g=g or _h2b(GENOME); prev=x&((1<<CFG['inbits'])-1); src=CFG['inbits']; cur=0\n" +
" for L in range(CFG['layers']):\n  cur=0\n  for w in range(CFG['width']):\n   cell=L*CFG['width']+w; p=cell*CB; addr=0\n" +
"   for k in range(4):\n    sel=g[p+k]%max(1,(CFG['inbits'] if L==0 else CFG['width']))\n    if sel>=src: sel=sel%src if src else 0\n    addr|=((prev>>sel)&1)<<k\n" +
"   cur|=(((g[p+4]|(g[p+5]<<8))>>addr)&1)<<w\n  prev=cur; src=CFG['width']\n return cur&((1<<CFG['outbits'])-1)\n" +
"_telomere=[1000]; _hayflick=200\n" +
"def self_evolve(target,gens=20):\n global GENOME\n g=_h2b(GENOME)\n" +
" def fit(gg):\n  m=t=0\n  for x in range(1<<CFG['inbits']):\n   d=infer(x,gg)^(target(x)&((1<<CFG['outbits'])-1))\n   for b in range(CFG['outbits']):\n    t+=1\n    if not ((d>>b)&1): m+=1\n  return m/t\n" +
" bf=fit(g)\n for _ in range(gens):\n  if _telomere[0]<=_hayflick: break\n  c=list(g)\n  for i in range(len(c)):\n   if random.random()<0.04: c[i]=random.randint(0,255)\n  f=fit(c)\n  if f>=bf: bf=f; g=c\n  _telomere[0]-=30\n GENOME=_b2h(g)\n return {'fitness':bf,'uid':uid(),'telomere':_telomere[0],'senescent':_telomere[0]<=_hayflick}\n";
  }

  plugin._uidOf = uidOf;
  (global.OMEGA_PLUGINS = global.OMEGA_PLUGINS || {}).self_evolve = plugin;
  if (typeof module !== "undefined" && module.exports) module.exports = plugin;
})(typeof window !== "undefined" ? window : globalThis);
