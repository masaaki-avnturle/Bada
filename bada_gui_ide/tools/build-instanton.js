#!/usr/bin/env node
/* ============================================================================
 * build-instanton.js — build "InstantOn", a single self-contained HTML
 * (dist/instanton.html) + stage it as the InstantOn app's www/index.html.
 *
 * InstantOn configures your PC so that turning the power OFF saves state to
 * disk (hibernate / Windows fast startup) and turning it back ON skips the
 * normal boot and resumes instantly from where you left off.
 *
 * Real actions run in the desktop app (Electron) after a confirmation, or via
 * the CLI. A plain browser / Android APK is display-only (shows the commands).
 * ==========================================================================*/
"use strict";
const fs = require("fs");
const path = require("path");
const IDE = path.join(__dirname, "..");

const html = `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>InstantOn — 瞬間起動</title>
<style>
  :root{color-scheme:light dark;--bg:#04060a;--panel:#0a1220;--line:#1c2838;--ink:#d6e2ee;
        --dim:#8aa0b8;--gold:#c8a44a;--green:#2e9e57;--red:#d0574a;--blue:#4a80d0;}
  *{box-sizing:border-box;}
  body{margin:0;background:var(--bg);color:var(--ink);
       font-family:system-ui,"Segoe UI","Hiragino Kaku Gothic ProN",Meiryo,sans-serif;line-height:1.6;}
  header{padding:16px 20px;border-bottom:1px solid var(--line);background:linear-gradient(180deg,#0a1220,#04060a);}
  h1{margin:0;font-size:19px;} h1 .a{color:var(--gold);}
  header p{margin:4px 0 0;color:var(--dim);font-size:12.5px;}
  main{max-width:660px;margin:0 auto;padding:18px 20px 50px;}
  #env{font-size:12.5px;padding:8px 12px;border-radius:8px;margin-bottom:14px;}
  #env.desk{background:#123a24;color:#7ce0a3;} #env.view{background:#3a2e12;color:#e8cf8a;}
  .flow{display:flex;gap:8px;align-items:center;justify-content:center;margin:6px 0 16px;color:var(--dim);font-size:13px;flex-wrap:wrap;}
  .flow b{color:var(--gold);} .flow .ar{color:#3a5a80;}
  .card{background:#070c15;border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:14px;}
  .card h2{margin:0 0 4px;font-size:16px;} .card h2 .ic{margin-right:6px;}
  .card p{margin:4px 0 0;color:var(--dim);font-size:12.5px;}
  .cmd{font-family:"SFMono-Regular",Consolas,monospace;font-size:11.5px;background:#020407;border:1px solid var(--line);
       border-radius:7px;padding:8px 10px;margin-top:10px;color:#bcd;word-break:break-all;white-space:pre-wrap;}
  .row{display:flex;gap:8px;align-items:center;margin-top:10px;flex-wrap:wrap;}
  button{font:inherit;border:1px solid var(--line);background:#132033;color:var(--ink);border-radius:8px;padding:9px 15px;cursor:pointer;}
  button.go{border:0;background:var(--green);color:#eafff0;font-weight:600;}
  button.copy{padding:6px 10px;font-size:12px;}
  .out{font-family:"SFMono-Regular",Consolas,monospace;font-size:11.5px;white-space:pre-wrap;color:#9fb;margin-top:8px;}
  .note{color:var(--dim);font-size:12px;} code{color:var(--gold);}
</style>
</head>
<body>
<header>
  <h1>Instant<span class="a">On</span> <span class="note">瞬間起動</span></h1>
  <p>電源を切ると状態をディスクに保存し、次に電源を入れると<b>通常のブート準備を飛ばして、いきなり前回の状態から立ち上がる</b>ように設定します(復帰起動 / 高速スタートアップ)。<b>あなた自身の PC 対象</b>。</p>
</header>
<main>
  <div id="env" class="view">環境を判定中…</div>
  <div class="flow"><b>電源OFF</b><span class="ar">→</span>状態をディスクに保存(ハイバネート)<span class="ar">→</span><b>電源ON</b><span class="ar">→</span>ブートを飛ばして<b>即復帰</b></div>

  <div class="card">
    <h2><span class="ic">🔎</span>現在の設定を確認</h2>
    <p>ハイバネート/高速スタートアップが有効か、休止に必要な swap があるかを表示します(安全・読み取りのみ)。</p>
    <div class="cmd" data-cmd="status">—</div>
    <div class="row"><button class="go" data-run="status">状態を確認</button><button class="copy" data-copy="status">コマンドをコピー</button></div>
    <div class="out" data-out="status"></div>
  </div>

  <div class="card">
    <h2><span class="ic">⚡</span>インスタントオンを有効化</h2>
    <p><b>Windows</b>: ハイバネート on + 高速スタートアップ(ハイブリッドブート)on + 電源ボタン=休止。<b>Linux</b>: 電源キー/フタ閉じ=ハイバネートに設定。以後「電源オフ」で状態が保存され、次回はブートを飛ばして即復帰します。<span class="note">(要 管理者 / sudo)</span></p>
    <div class="cmd" data-cmd="enable">—</div>
    <div class="row"><button class="go" data-run="enable">有効化</button><button class="copy" data-copy="enable">コマンドをコピー</button></div>
    <div class="out" data-out="enable"></div>
  </div>

  <div class="card">
    <h2><span class="ic">🌙</span>いま休止(次回インスタント起動)</h2>
    <p>いま状態をディスクに保存して電源を落とします。次に電源を入れると、そのまま前回の続きから即座に立ち上がります。</p>
    <div class="cmd" data-cmd="hibernate-now">—</div>
    <div class="row"><button data-run="hibernate-now">いま休止する</button><button class="copy" data-copy="hibernate-now">コマンドをコピー</button></div>
    <div class="out" data-out="hibernate-now"></div>
  </div>

  <div class="card">
    <h2><span class="ic">↩︎</span>無効化(通常起動に戻す)</h2>
    <p>インスタントオン設定を解除し、通常のシャットダウン/起動に戻します。<span class="note">(要 管理者 / sudo)</span></p>
    <div class="cmd" data-cmd="disable">—</div>
    <div class="row"><button data-run="disable">無効化</button><button class="copy" data-copy="disable">コマンドをコピー</button></div>
    <div class="out" data-out="disable"></div>
  </div>

  <p class="note">実行は必ず確認後に行われます。ブラウザ単体・Android では OS 設定は行えません(表示のみ。Android は要 root/system)。CLI 同梱: <code>node cli/instanton.js &lt;status|enable|hibernate-now|disable&gt;</code>。<br>※ Linux で復帰起動を使うには、休止用の swap 領域(RAM以上)が必要です。「状態を確認」で swap の有無を確認してください。</p>
</main>

<script>
(function(){
  "use strict";
  var bridge=(typeof window!=="undefined" && window.instantOn)?window.instantOn:null;
  function osGuess(){ var ua=navigator.userAgent||"";
    if(/Windows/i.test(ua))return "win32"; if(/Android/i.test(ua))return "android"; if(/Mac/i.test(ua))return "darwin"; return "linux"; }
  var CMDS={
    linux:{ "status":"cat /sys/power/state; swapon --show; systemctl show systemd-logind -p HandlePowerKey",
      "enable":"sudo sh -c 'printf \\"[Login]\\\\nHandlePowerKey=hibernate\\\\nHandleLidSwitch=hibernate\\\\n\\" > /etc/systemd/logind.conf.d/90-instanton.conf && systemctl restart systemd-logind'",
      "hibernate-now":"sync && systemctl hibernate",
      "disable":"sudo rm -f /etc/systemd/logind.conf.d/90-instanton.conf && sudo systemctl restart systemd-logind" },
    win32:{ "status":"powercfg /a & reg query \\"HKLM\\\\SYSTEM\\\\CurrentControlSet\\\\Control\\\\Session Manager\\\\Power\\" /v HiberbootEnabled",
      "enable":"powercfg /hibernate on & reg add \\"...\\\\Power\\" /v HiberbootEnabled /t REG_DWORD /d 1 /f & powercfg -SETACVALUEINDEX SCHEME_CURRENT SUB_BUTTONS PBUTTONACTION 2",
      "hibernate-now":"shutdown /h",
      "disable":"reg add \\"...\\\\Power\\" /v HiberbootEnabled /t REG_DWORD /d 0 /f" },
    darwin:{ "status":"pmset -g | grep hibernatemode","enable":"sudo pmset -a hibernatemode 25","hibernate-now":"sync && pmset sleepnow","disable":"sudo pmset -a hibernatemode 3" },
    android:{ "status":"(要 root) dumpsys power","enable":"(要 root)","hibernate-now":"(要 root)","disable":"(要 root)" }
  };
  var platform=bridge?bridge.platform:osGuess();
  var envEl=document.getElementById("env");
  if(bridge){ envEl.className="desk"; envEl.textContent="デスクトップ版: ボタンを押すと確認のうえ実際に設定/実行します ("+platform+")"; }
  else { envEl.className="view"; envEl.textContent="表示のみモード ("+platform+"): 実行はデスクトップ版(Electron)または端末で。"+(platform==="android"?" Android の休止/起動設定には root/system 権限が必要です。":""); }

  Array.prototype.forEach.call(document.querySelectorAll(".cmd"),function(el){
    var a=el.getAttribute("data-cmd");
    if(bridge){ bridge.preview(a).then(function(r){ el.textContent=(r&&r.command)||"(この OS では未対応)"; }); }
    else { el.textContent=(CMDS[platform]||CMDS.linux)[a]||"(未対応)"; }
  });
  function label(a){ return ({"status":"状態確認","enable":"インスタントオン有効化","hibernate-now":"いま休止","disable":"無効化"})[a]||a; }

  document.querySelectorAll("button[data-run]").forEach(function(b){
    b.addEventListener("click",function(){
      var a=this.getAttribute("data-run"); var out=document.querySelector('[data-out="'+a+'"]');
      if(!bridge){ out.innerHTML='<span class="note">表示のみモードでは実行できません。端末で次を実行してください:</span>\\n'+((CMDS[platform]||CMDS.linux)[a]); return; }
      if(a!=="status" && !confirm(label(a)+" を実行します。よろしいですか?")) return;
      out.textContent="実行中…";
      bridge.run(a).then(function(r){
        if(r.ok) out.textContent=(r.out||"[ok] "+(r.command||""));
        else out.innerHTML='<span style="color:#f2a49b">[失敗 code '+(r.code)+']</span> '+(r.command||"")+"\\n"+((r.err||"").trim()||"権限が必要かもしれません(sudo / 管理者)。");
      });
    });
  });
  document.querySelectorAll("button[data-copy]").forEach(function(b){
    b.addEventListener("click",function(){
      var a=this.getAttribute("data-copy"); var el=document.querySelector('[data-cmd="'+a+'"]');
      var txt=(el&&el.textContent&&el.textContent!=="—")?el.textContent:((CMDS[platform]||CMDS.linux)[a]);
      try{ navigator.clipboard.writeText(txt); var self=this; this.textContent="コピー済"; setTimeout(function(){self.textContent="コマンドをコピー";},1200);}catch(e){}
    });
  });
})();
</script>
</body>
</html>
`;

fs.mkdirSync(path.join(IDE, "dist"), { recursive: true });
fs.writeFileSync(path.join(IDE, "dist", "instanton.html"), html);
console.log("built dist/instanton.html (" + fs.statSync(path.join(IDE, "dist", "instanton.html")).size + " bytes)");
const APPWWW = path.join(IDE, "instanton-app", "www");
if (fs.existsSync(path.join(IDE, "instanton-app"))) {
  fs.mkdirSync(APPWWW, { recursive: true });
  fs.writeFileSync(path.join(APPWWW, "index.html"), html);
  console.log("staged instanton-app/www/index.html");
}
