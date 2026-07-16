# frozen_string_literal: true

require_relative "palette"

module Bada
  module Penrose
    # WebApp — a single self-contained HTML file that is the *visual* Penrose
    # 絵記号 studio:
    #
    #   * a clickable PALETTE of Penrose picture-symbols (rendered as SVG),
    #   * a real DRAWING CANVAS where selecting a symbol places its glyph; you
    #     drag the glyphs, click their legs to wire (contract) them or mark a
    #     free index, and wrap them with ∇/∂/∫ and (anti)symmetriser decorators,
    #   * live generation of the 清書した方程式 (typeset) and the 計算した方程式
    #     (Einstein summation, computed in the browser).
    #
    # The einsum kernel mirrors Bada::Penrose::Einsum so a drawn diagram computes
    # with no external dependencies (works offline).
    module WebApp
      module_function

      def render
        <<~HTML
          <!DOCTYPE html>
          <html lang="ja">
          <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>ペンローズ絵記号スタジオ — Bada</title>
          <style>#{css}</style>
          </head>
          <body>
          <header>
            <h1>ロジャー・ペンローズ 絵記号スタジオ</h1>
            <p>パレットの絵記号を選ぶ／手描きで自分でも描く → 脚をクリックで結線して組み合わせ → 方程式を生成。結果は ＋ − × ÷ で加減乗除できます。<span class="tag">Bada / Penrose</span></p>
          </header>

          <main>
            <section class="pane palette">
              <h2>パレット（絵記号を選ぶ）</h2>
              <div id="palette"></div>
            </section>

            <section class="pane stage">
              <h2>キャンバス（絵記号を描く・組み合わせる）</h2>
              <div id="toolbar">
                <span id="hint" class="hint">パレットの記号をクリックして配置 → 脚(●)を2つクリックで結線</span>
              </div>
              <svg id="canvas" viewBox="0 0 900 560" preserveAspectRatio="xMidYMid meet"></svg>
              <div class="row">
                <button id="gen" class="primary">▶ 方程式を生成 (Generator)</button>
                <button id="pen">✏ 手描き: OFF</button>
                <button id="penClear">手描きを消す</button>
                <button id="btnFree">選択した脚を自由添字に</button>
                <button id="btnDelete">選択ノードを削除</button>
                <button id="btnClearSel">選択解除</button>
                <button id="sample">行列積の例</button>
                <button id="reset">リセット</button>
              </div>
              <div id="props"></div>
            </section>

            <section class="pane output">
              <h2>① 描画 → 方程式（Generator 出力）</h2>
              <div class="sub">清書した方程式</div>
              <div id="fair" class="equation">—</div>
              <div class="sub">組み合わせによる計算した方程式</div>
              <div id="numeric" class="equation">—</div>
              <div id="notes" class="notes"></div>

              <h2 style="margin-top:16px">② 規定の方程式を選ぶ → 絵記号を生成</h2>
              <p class="hint">既定の方程式を選ぶと、その組み合わせに対応するペンローズの絵記号がキャンバスに描かれます。</p>
              <div id="presets"></div>

              <h2 style="margin-top:16px">③ 加減乗除（結果どうしの算術）</h2>
              <p class="hint">計算結果を保存し、＋ − × ÷ で組み合わせます（同じ形は成分ごと、数値はスカラー倍）。</p>
              <button id="saveReg">現在の計算結果を保存 (R)</button>
              <div id="registers" class="regs"></div>
              <div class="arith">
                <select id="opA"></select>
                <select id="op"><option>＋</option><option>−</option><option>×</option><option>÷</option></select>
                <select id="opB"></select>
                <input id="numB" type="number" step="any" placeholder="数値" style="display:none">
                <button id="calc" class="primary">= 計算</button>
                <button id="saveArith">結果を保存</button>
              </div>
              <div id="arithOut" class="equation">—</div>

              <h2 style="margin-top:16px">④ アプリを作るアプリ（方程式ネットワーク → ソースコード → 生成アプリDL）</h2>
              <p class="hint">保存した方程式(R1,R2…)と加減乗除が方程式ネットワークになります。未知事前予知エンジンが各方程式を意味付けし、実行できるアプリを生成。生成アプリ自体もダウンロードできます。</p>
              <div class="row">
                <button id="genApp" class="primary">🧠 アプリを生成</button>
                <button id="dlApp">⬇ 生成アプリをダウンロード</button>
              </div>
              <div id="appMeaning" class="notes"></div>
              <pre id="appSrc" class="src">（「アプリを生成」を押すと、方程式ネットワークのソースコードがここに出ます）</pre>
            </section>
          </main>

          <footer>© Bada — Penrose graphical-notation studio · 純JS Einstein-summation engine</footer>

          <script>
          const PALETTE = #{palette_data};
          #{js}
          </script>
          </body>
          </html>
        HTML
      end

      # Write the app to a path and return the path.
      def write(path)
        File.write(path, render)
        path
      end

      # Palette data (symbol -> faithful SVG glyph/name/math) as a JSON literal.
      def palette_data
        require "json"
        data = Palette.glyphs.map do |key, g|
          { key: key.to_s, name: g[:name], token: g[:token], math: g[:math],
            svg: g[:svg], meaning: g[:meaning] }
        end
        JSON.generate(data)
      end

      # ---- assets ------------------------------------------------------
      def css
        <<~CSS
          :root{--bg:#0b0e14;--panel:#141a24;--edge:#26303f;--ink:#e6ecf3;--dim:#8b9bb0;--gold:#c8a44a;--blue:#4a80d0;--cyan:#40b8c0;--red:#c05a5a}
          *{box-sizing:border-box}
          body{margin:0;font-family:-apple-system,"Segoe UI",Roboto,"Hiragino Sans","Noto Sans JP",sans-serif;background:var(--bg);color:var(--ink)}
          header{padding:18px 22px;border-bottom:1px solid var(--edge);background:linear-gradient(180deg,#101622,#0b0e14)}
          header h1{margin:0 0 6px;font-size:20px;color:var(--gold)}
          header p{margin:0;color:#9fb0c3;font-size:13px;max-width:1000px}
          .tag{margin-left:10px;padding:2px 8px;border:1px solid var(--edge);border-radius:10px;color:var(--cyan);font-size:11px;white-space:nowrap}
          main{display:grid;grid-template-columns:250px 1fr 340px;gap:14px;padding:16px;align-items:start}
          @media(max-width:1100px){main{grid-template-columns:1fr}}
          .pane{background:var(--panel);border:1px solid var(--edge);border-radius:10px;padding:14px}
          .pane h2{margin:0 0 10px;font-size:14px;color:var(--cyan);letter-spacing:.03em}
          #palette{display:flex;flex-direction:column;gap:5px;max-height:78vh;overflow-y:auto}
          .sym{display:flex;align-items:center;gap:9px;padding:6px 9px;background:#0f1420;border:1px solid var(--edge);border-radius:8px;cursor:pointer;transition:.12s}
          .sym:hover{border-color:var(--gold);transform:translateX(2px)}
          .sym.active{border-color:var(--gold);box-shadow:0 0 0 1px var(--gold) inset}
          .sym .gl{flex:0 0 40px;height:40px}
          .sym .gl svg{width:40px;height:40px}
          .sym .txt{display:flex;flex-direction:column;gap:1px;min-width:0}
          .sym .nm{font-size:12px;line-height:1.2}
          .sym .mt{font-size:11px;color:var(--gold);font-family:"SFMono-Regular",Consolas,monospace}
          #toolbar{margin-bottom:8px;min-height:20px}
          .hint{font-size:12px;color:#9fb0c3}
          #canvas{width:100%;height:auto;aspect-ratio:900/560;background:
            radial-gradient(circle at 1px 1px,#1c2735 1px,transparent 0) 0 0/26px 26px,#0d121b;
            border:1px solid var(--edge);border-radius:8px;touch-action:none}
          .row{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}
          button{background:#182234;border:1px solid var(--edge);color:var(--ink);border-radius:7px;padding:7px 11px;font-size:12px;cursor:pointer}
          button:hover{border-color:var(--blue)}
          button.primary{background:var(--gold);color:#0b0e14;border-color:var(--gold);font-weight:600}
          #props{margin-top:10px}
          #props .card{background:#0f1420;border:1px solid var(--edge);border-radius:8px;padding:10px}
          #props .grid{display:grid;grid-template-columns:auto 1fr;gap:6px 10px;align-items:center;font-size:12px}
          #props label{color:#9fb0c3}
          input{background:#0f1420;border:1px solid var(--edge);color:var(--ink);border-radius:6px;padding:5px 7px;font-size:12px;width:100%}
          .sub{font-size:11px;color:#9fb0c3;margin:8px 0 4px}
          .equation{background:#0f1420;border:1px solid var(--edge);border-radius:8px;padding:15px;font-size:18px;min-height:26px;overflow-x:auto;font-family:"Times New Roman",Georgia,serif;transition:box-shadow .1s,border-color .1s}
          .equation.flash{border-color:var(--gold);box-shadow:0 0 0 2px var(--gold) inset}
          .equation .op{color:var(--cyan)} .equation sub{font-size:.7em;color:var(--gold)} .equation .sum{color:var(--blue);font-weight:600}
          .notes{margin-top:10px;font-size:12px;color:#c8a44a}
          #presets{display:flex;flex-direction:column;gap:5px}
          .preset{display:flex;justify-content:space-between;align-items:center;gap:8px;padding:7px 10px;background:#0f1420;border:1px solid var(--edge);border-radius:8px;cursor:pointer;transition:.12s}
          .preset:hover{border-color:var(--gold);transform:translateX(2px)}
          .preset .pn{font-size:12px} .preset .pe{font-size:12px;color:var(--gold);font-family:"Times New Roman",Georgia,serif}
          button.on{background:var(--cyan);color:#0b0e14;border-color:var(--cyan);font-weight:600}
          .regs{display:flex;flex-direction:column;gap:4px;margin:8px 0}
          .regs .reg{display:flex;justify-content:space-between;gap:8px;font-size:12px;padding:5px 8px;background:#0f1420;border:1px solid var(--edge);border-radius:6px}
          .regs .reg b{color:var(--cyan)} .regs .reg .rv{color:var(--gold);font-family:"SFMono-Regular",Consolas,monospace;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:60%}
          .arith{display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin:6px 0}
          .arith select,.arith input{padding:5px 7px;font-size:13px}
          .arith #numB{width:90px}
          .src{background:#0f1420;border:1px solid var(--edge);border-radius:8px;padding:10px;font-size:11px;line-height:1.45;font-family:"SFMono-Regular",Consolas,monospace;color:#cfe0f0;overflow:auto;max-height:240px;white-space:pre;margin-top:8px}
          #appMeaning .mnode{color:#9fb0c3} #appMeaning b{color:var(--cyan)}
          footer{padding:12px 22px;border-top:1px solid var(--edge);color:#6c7a8d;font-size:11px;text-align:center}
        CSS
      end

      def js
        <<~'JS'
          const SVGNS='http://www.w3.org/2000/svg';
          const GOLD='#c8a44a',UP='#40b8c0',DOWN='#4a80d0',INK='#e6ecf3',RED='#c05a5a';
          const W=90,H=46,LEG=30;                 // node box + leg length
          const $=id=>document.getElementById(id);

          // preset (upperLegs, lowerLegs, shape, defaultName) per palette symbol
          const TENSORS={
            tensor:[1,1,'box','T'], matrix:[1,1,'box','M'], matmul:[1,1,'box','A'],
            vector:[1,0,'box','v'], metric:[0,2,'box','g'], epsilon:[0,3,'tri','ε'],
            riemann:[1,3,'boxbar','R'], torsion:[1,2,'tribar','T'], delta:[1,1,'box','δ']
          };

          // ---------- state ----------
          let nodes=[], wires=[], frees=[], decos=[];
          let uid=1, sel=null, selNode=null, activeKey=null;
          let ink=[], penStroke=null, drawMode=false;   // 手描き (freehand)
          let registers=[], regNo=0, lastResult=null;    // 加減乗除 (arithmetic)
          let netlog=[], lastFair='—', lastArith=null, genAppHtml=null; // ④ アプリを作るアプリ

          // ================= palette =================
          function buildPalette(){
            const box=$('palette');
            PALETTE.forEach(p=>{
              const el=document.createElement('div');
              el.className='sym'; el.dataset.key=p.key;
              el.innerHTML=`<span class="gl">${p.svg}</span><span class="txt"><span class="nm">${p.name}</span><span class="mt">${p.math}</span></span>`;
              el.title=p.meaning;
              el.onclick=()=>pickSymbol(p,el);
              box.appendChild(el);
            });
          }
          function setHint(t){ $('hint').textContent=t; }

          function pickSymbol(p,el){
            document.querySelectorAll('.sym').forEach(s=>s.classList.remove('active'));
            const k=p.key;
            if(TENSORS[k]){ addNode(k); setHint(`${p.name} を配置しました。ドラッグで移動、脚(●)を2つクリックで結線。`); }
            else if(['contraction','wire','cup','cap'].includes(k)){ el.classList.add('active'); setHint('2つの脚(●)をクリックすると結線（縮約）します。'); }
            else if(['nabla','partial'].includes(k)){ applyDeriv(k,p); }
            else if(k==='integral'){ applyIntegral(p); }
            else if(['symmetrize','antisymmetrize'].includes(k)){ applySym(k,p); }
            else { setHint(`${p.name}: ${p.meaning}`); }
            update();
          }

          // ================= nodes =================
          function addNode(key){
            const [up,down,shape,name]=TENSORS[key];
            const i=nodes.length;
            const n={id:uid++, key, name, up, down, shape,
                     x:70+(i%4)*195, y:110+Math.floor(i/4)*180, val:null};
            nodes.push(n); selNode=n; sel=null;
            return n;
          }
          function nodeById(id){ return nodes.find(n=>n.id===id); }

          // leg geometry
          function legX(n,side,i){ const c=side==='up'?n.up:n.down; return n.x + W*(i+1)/(c+1); }
          function legTipY(n,side){ return side==='up'? n.y-LEG : n.y+H+LEG; }
          function legBaseY(n,side){ return side==='up'? n.y : n.y+H; }
          function slotIndex(n,side,i){ return side==='up'? i : n.up+i; }
          function sameLeg(a,b){ return a&&b&&a.id===b.id&&a.side===b.side&&a.i===b.i; }
          function legUsed(ref){
            const w=wires.some(w=>sameLeg(w.a,ref)||sameLeg(w.b,ref));
            const f=frees.some(f=>f.id===ref.id&&f.side===ref.side&&f.i===ref.i);
            return w||f;
          }

          function clickLeg(ref){
            if(legUsed(ref)){ // clicking a used leg removes its wire/free
              wires=wires.filter(w=>!(sameLeg(w.a,ref)||sameLeg(w.b,ref)));
              frees=frees.filter(f=>!(f.id===ref.id&&f.side===ref.side&&f.i===ref.i));
              sel=null; setHint('結線/自由添字を解除しました。'); update(); return;
            }
            if(!sel){ sel=ref; setHint('もう一方の脚(●)をクリックで結線、または「自由添字に」ボタン。'); update(); return; }
            if(sameLeg(sel,ref)){ sel=null; update(); return; }
            if(sel.id===ref.id){ setHint('同じノードの脚どうしも縮約(トレース)できます。'); }
            wires.push({a:sel,b:ref}); sel=null; setHint('結線（縮約）しました。'); update();
          }

          function makeFree(){
            if(!sel){ setHint('先に脚(●)を1つクリックしてください。'); return; }
            const label=prompt('自由添字の名前（例 i, j, μ）','');
            if(label){ frees.push({id:sel.id,side:sel.side,i:sel.i,label:label.trim()}); setHint('自由添字を設定しました。'); }
            sel=null; update();
          }

          // ================= decorators =================
          function applyDeriv(type,p){
            if(!selNode){ setHint('先にノードを選択してください（∇/∂ の対象）。'); return; }
            const l=prompt(`${p.name} の微分の添字（例 e, μ）`,'μ'); if(l===null) return;
            decos.push({type, target:selNode.id, label:(l.trim()||'μ')});
            setHint(`${type==='nabla'?'∇':'∂'}_${l} を付けました。`);
          }
          function applyIntegral(p){
            const l=prompt('積分の添字（測度 dμ）','μ'); if(l===null) return;
            decos.push({type:'integral', label:(l.trim()||'μ')});
            setHint('∫ … dμ を付けました。');
          }
          function applySym(type,p){
            const l=prompt('(反)対称化する出力添字（空白区切り 例: i j）','i j'); if(l===null) return;
            const labels=l.trim().split(/\s+/).filter(Boolean);
            decos.push({type:type==='symmetrize'?'sym':'antisym', labels});
            setHint(`${type==='symmetrize'?'Sym':'Asym'}(${labels.join(',')}) を付けました。`);
          }

          function deleteNode(){
            if(!selNode){ setHint('削除するノードを選択してください。'); return; }
            const id=selNode.id;
            nodes=nodes.filter(n=>n.id!==id);
            wires=wires.filter(w=>w.a.id!==id&&w.b.id!==id);
            frees=frees.filter(f=>f.id!==id);
            decos=decos.filter(d=>d.target!==id);
            selNode=null; sel=null; setHint('ノードを削除しました。'); update();
          }

          // ================= rendering =================
          function E(tag,attrs,kids){ const e=document.createElementNS(SVGNS,tag); for(const k in attrs) e.setAttribute(k,attrs[k]); (kids||[]).forEach(c=>e.appendChild(c)); return e; }
          function txt(x,y,s,attrs){ const t=E('text',Object.assign({x,y,'text-anchor':'middle'},attrs||{})); t.textContent=s; return t; }

          function render(){
            const c=$('canvas'); c.innerHTML='';
            // decorator hoops (∇/∂) behind nodes
            decos.filter(d=>d.type==='nabla'||d.type==='partial').forEach(d=>{
              const n=nodeById(d.target); if(!n) return;
              c.appendChild(E('ellipse',{cx:n.x+W/2,cy:n.y+H/2,rx:W/2+16,ry:H/2+16,fill:'none',stroke:GOLD,'stroke-width':2,'stroke-dasharray':d.type==='partial'?'4 3':'none'}));
              c.appendChild(txt(n.x-6,n.y-2,d.type==='nabla'?'∇':'∂',{fill:GOLD,'font-size':16}));
              c.appendChild(txt(n.x+W+14,n.y+H+14,d.label,{fill:DOWN,'font-size':12}));
              c.appendChild(E('line',{x1:n.x+W,y1:n.y+H,x2:n.x+W+22,y2:n.y+H+22,stroke:DOWN,'stroke-width':2}));
            });
            // wires
            wires.forEach(w=>{
              const a=nodeById(w.a.id),b=nodeById(w.b.id); if(!a||!b) return;
              const ax=legX(a,w.a.side,w.a.i),ay=legTipY(a,w.a.side);
              const bx=legX(b,w.b.side,w.b.i),by=legTipY(b,w.b.side);
              const my=(ay+by)/2 + (w.a.id===w.b.id?-40:0);
              c.appendChild(E('path',{d:`M${ax} ${ay} C ${ax} ${my} ${bx} ${my} ${bx} ${by}`,fill:'none',stroke:GOLD,'stroke-width':2.5}));
            });
            // integral badge
            const ig=decos.find(d=>d.type==='integral');
            if(ig){ c.appendChild(txt(30,300,'∫',{fill:GOLD,'font-size':64})); c.appendChild(txt(46,330,'d'+ig.label,{fill:DOWN,'font-size':13})); }
            // sym/antisym badge
            const sy=decos.find(d=>d.type==='sym'||d.type==='antisym');
            if(sy){ c.appendChild(txt(760,30,(sy.type==='sym'?'Sym':'Asym')+'('+sy.labels.join(',')+')',{fill:INK,'font-size':13})); }
            // freehand ink (自分で描いた絵記号)
            ink.forEach(st=>{ if(st.length>1) c.appendChild(E('polyline',{points:st.map(p=>p[0]+','+p[1]).join(' '),fill:'none',stroke:'#e0b050','stroke-width':2.6,'stroke-linecap':'round','stroke-linejoin':'round'})); });
            // nodes
            nodes.forEach(n=>drawNode(c,n));
            // freehand overlay captures the pointer while 手描き is ON
            if(drawMode){
              const ov=E('rect',{x:0,y:0,width:900,height:560,fill:'transparent',cursor:'crosshair'});
              ov.addEventListener('pointerdown',startPen);
              c.appendChild(ov);
            }
          }

          // ---------- freehand (手描き) ----------
          function startPen(ev){ ev.preventDefault(); const p=svgPt(ev); penStroke=[[p.x,p.y]]; ink.push(penStroke); }
          function togglePen(){ drawMode=!drawMode; sel=null; const b=$('pen'); b.textContent='✏ 手描き: '+(drawMode?'ON':'OFF'); b.classList.toggle('on',drawMode); setHint(drawMode?'手描きモード：キャンバスをドラッグして自分で絵記号を描けます。':'手描きモードを解除しました。'); render(); }
          function clearInk(){ ink=[]; setHint('手描きを消去しました。'); render(); }

          function drawNode(c,n){
            const g=E('g',{});
            const selected = selNode&&selNode.id===n.id;
            // legs (draw first so endpoints sit above)
            for(let i=0;i<n.up;i++) drawLeg(g,n,'up',i);
            for(let i=0;i<n.down;i++) drawLeg(g,n,'down',i);
            // shape
            if(n.shape==='tri'||n.shape==='tribar'){
              g.appendChild(E('polygon',{points:`${n.x+8},${n.y} ${n.x+W-8},${n.y} ${n.x+W/2},${n.y+H}`,fill:'#0f1420',stroke:selected?INK:GOLD,'stroke-width':selected?3:2.5}));
            } else {
              g.appendChild(E('rect',{x:n.x,y:n.y,width:W,height:H,rx:7,fill:'#0f1420',stroke:selected?INK:GOLD,'stroke-width':selected?3:2.5}));
            }
            if(n.shape==='boxbar'||n.shape==='tribar'){ // antisymmetric leg bars
              if(n.up>1) g.appendChild(E('line',{x1:n.x+14,y1:n.y-12,x2:n.x+W-14,y2:n.y-12,stroke:INK,'stroke-width':2.5}));
              g.appendChild(E('line',{x1:n.x+14,y1:n.y+H+12,x2:n.x+W-14,y2:n.y+H+12,stroke:INK,'stroke-width':2.5}));
            }
            const label=txt(n.x+W/2,n.y+H/2+6,n.name,{fill:GOLD,'font-size':18,'font-style':'italic'});
            label.style.pointerEvents='none';
            g.appendChild(label);
            const hit=E('rect',{x:n.x,y:n.y,width:W,height:H,rx:7,fill:'transparent',cursor:'move'});
            hit.addEventListener('pointerdown',ev=>startDrag(ev,n));
            g.appendChild(hit);
            c.appendChild(g);
          }

          function drawLeg(g,n,side,i){
            const x=legX(n,side,i), y0=legBaseY(n,side), y1=legTipY(n,side);
            const ref={id:n.id,side,i};
            const used=legUsed(ref), seld=sameLeg(sel,ref);
            g.appendChild(E('line',{x1:x,y1:y0,x2:x,y2:y1,stroke:side==='up'?UP:DOWN,'stroke-width':2.5}));
            const dot=E('circle',{cx:x,cy:y1,r:6,fill:seld?INK:(used?GOLD:'#0d121b'),stroke:side==='up'?UP:DOWN,'stroke-width':2,cursor:'pointer'});
            dot.addEventListener('pointerdown',ev=>{ev.stopPropagation();});
            dot.addEventListener('click',ev=>{ev.stopPropagation(); clickLeg(ref);});
            g.appendChild(dot);
            // free-index label
            const f=frees.find(f=>f.id===n.id&&f.side===side&&f.i===i);
            if(f){ g.appendChild(txt(x+(side==='up'?12:12),y1+(side==='up'?-4:16),f.label,{fill:INK,'font-size':13})); }
          }

          // ---------- drag ----------
          let drag=null;
          function svgPt(ev){ const c=$('canvas'); const pt=c.createSVGPoint(); pt.x=ev.clientX; pt.y=ev.clientY; return pt.matrixTransform(c.getScreenCTM().inverse()); }
          function startDrag(ev,n){ ev.preventDefault(); selNode=n; sel=null; const p=svgPt(ev); drag={n,dx:p.x-n.x,dy:p.y-n.y,moved:false}; update(); }
          window.addEventListener('pointermove',ev=>{
            if(penStroke){ const p=svgPt(ev); penStroke.push([Math.round(p.x),Math.round(p.y)]); render(); return; }
            if(!drag) return; const p=svgPt(ev); drag.n.x=Math.max(0,Math.min(810,p.x-drag.dx)); drag.n.y=Math.max(30,Math.min(500,p.y-drag.dy)); drag.moved=true; render();
          });
          window.addEventListener('pointerup',()=>{ drag=null; penStroke=null; });

          // ================= props panel =================
          function renderProps(){
            const box=$('props');
            if(!selNode){ box.innerHTML=''; return; }
            const n=selNode;
            box.innerHTML=`<div class="card"><div class="grid">
              <label>名前</label><input id="p_name" value="${n.name}">
              <label>上付き脚</label><input id="p_up" type="number" min="0" max="4" value="${n.up}">
              <label>下付き脚</label><input id="p_down" type="number" min="0" max="4" value="${n.down}">
              <label>成分値 JSON</label><input id="p_val" value="${n.val?JSON.stringify(n.val):''}" placeholder="[[1,2],[3,4]]">
              </div><div class="row"><button class="primary" id="p_apply">適用</button></div></div>`;
            $('p_apply').onclick=applyProps;
          }
          function applyProps(){
            const n=selNode; if(!n) return;
            n.name=($('p_name').value.trim()||n.name).slice(0,3);
            const up=parseInt($('p_up').value,10), down=parseInt($('p_down').value,10);
            if(up!==n.up||down!==n.down){ // legs changed: drop this node's wires/frees to stay consistent
              wires=wires.filter(w=>w.a.id!==n.id&&w.b.id!==n.id);
              frees=frees.filter(f=>f.id!==n.id);
              n.up=Math.max(0,Math.min(4,up)); n.down=Math.max(0,Math.min(4,down));
            }
            const raw=$('p_val').value.trim();
            if(raw){ try{ n.val=JSON.parse(raw); }catch(e){ alert('JSONが不正です'); return; } } else n.val=null;
            setHint('ノードを更新しました。'); update();
          }

          // ================= resolve / compute =================
          function resolve(){
            const assign={}; nodes.forEach(n=>assign[n.id]=new Array(n.up+n.down).fill(null));
            wires.forEach((w,idx)=>{ const k='k'+(idx+1);
              assign[w.a.id][slotIndex(nodeById(w.a.id),w.a.side,w.a.i)]=k;
              assign[w.b.id][slotIndex(nodeById(w.b.id),w.b.side,w.b.i)]=k; });
            const output=[];
            frees.forEach(f=>{ assign[f.id][slotIndex(nodeById(f.id),f.side,f.i)]=f.label; output.push(f.label); });
            let auto=0; nodes.forEach(n=>assign[n.id].forEach((v,k)=>{ if(v===null){auto++; const nm='f'+auto; assign[n.id][k]=nm; output.push(nm);} }));
            const integral=decos.filter(d=>d.type==='integral').map(d=>d.label);
            return {assign, output:output.filter(o=>!integral.includes(o)), integral};
          }

          function idx(a){ return a.map(t=>{ const m=/^([A-Za-z])(\d+)$/.exec(t); return m?`${m[1]}<sub>${m[2]}</sub>`:t; }).join(' '); }
          function fairCopy(){
            if(!nodes.length) return '—';
            const r=resolve();
            const counts={}; for(const id in r.assign) r.assign[id].forEach(x=>counts[x]=(counts[x]||0)+1);
            let dummies=Object.keys(counts).filter(x=>counts[x]>1);
            r.integral.forEach(x=>{ if(!dummies.includes(x)) dummies.push(x); });
            const factors=nodes.map(n=>`${n.name}<sub>${idx(r.assign[n.id])}</sub>`);
            let pre='',post='';
            decos.forEach(d=>{
              if(d.type==='nabla')   pre=`<span class="op">∇</span><sub>${d.label}</sub> `+pre;
              if(d.type==='partial') pre=`<span class="op">∂</span><sub>${d.label}</sub> `+pre;
              if(d.type==='integral'){ pre=`<span class="op">∫</span> `+pre; post+=` d${d.label}`; }
            });
            const symd=decos.find(d=>d.type==='sym'||d.type==='antisym');
            let li=idx(r.output); if(symd&&symd.type==='sym') li=`(${li})`; if(symd&&symd.type==='antisym') li=`[${li}]`;
            const lhs=r.output.length?`R<sub>${li}</sub>`:'R';
            const sum=dummies.length?`<span class="sum">∑<sub>${dummies.map(d=>idx([d])).join(' ')}</sub></span> `:'';
            return `${lhs} = ${sum}${pre}${factors.join(' ')}${post}`;
          }

          // einsum (mirror of Bada::Penrose::Einsum)
          function strides(sh){ const s=sh.map(()=>1); for(let k=sh.length-2;k>=0;k--) s[k]=s[k+1]*sh[k+1]; return s; }
          function flat(x){ return Array.isArray(x)?x.flat(Infinity):[x]; }
          function shapeOf(x){ const sh=[]; let p=x; while(Array.isArray(p)){ sh.push(p.length); p=p[0]; } return sh; }
          function unflatten(fl,sh){ if(!sh.length) return fl[0]; const st=strides(sh);
            const b=(d,base)=> d===sh.length-1? Array.from({length:sh[d]},(_,i)=>fl[base+i*st[d]]) : Array.from({length:sh[d]},(_,i)=>b(d+1,base+i*st[d])); return b(0,0); }
          function einsum(){
            if(!nodes.length) return {ok:false,note:''};
            const r=resolve();
            for(const n of nodes){ if(n.val==null) return {ok:false,note:'成分値が未指定のノードがあります（ノードを選び「成分値 JSON」を入力）'}; }
            const dims={},tensors=[];
            for(const n of nodes){ const names=r.assign[n.id]; const sh=shapeOf(n.val); const fl=flat(n.val);
              if(sh.length!==names.length) return {ok:false,note:`[${n.name}] の階数(${sh.length})が脚数(${names.length})と一致しません`};
              names.forEach((nm,k)=>{ if(dims[nm]!=null&&dims[nm]!==sh[k]) {} dims[nm]=sh[k]; }); tensors.push({fl,names,sh}); }
            const all=Object.keys(dims); const outShape=r.output.map(n=>dims[n]); const os=strides(outShape);
            const res=new Array(outShape.reduce((a,b)=>a*b,1)).fill(0);
            const ranges=all.map(n=>[...Array(dims[n]).keys()]);
            const at=(t,a)=>{ const st=strides(t.sh); let off=0; t.names.forEach((n,k)=>off+=a[n]*st[k]); return t.fl[off]; };
            const rec=(i,a)=>{ if(i===all.length){ let pr=1; tensors.forEach(t=>pr*=at(t,a)); if(pr!==0){ let off=0; r.output.forEach((n,k)=>off+=a[n]*os[k]); res[off]+=pr; } return; }
              for(const v of ranges[i]){ a[all[i]]=v; rec(i+1,a); } };
            if(all.length) rec(0,{}); else res[0]=tensors.reduce((m,t)=>m*t.fl[0],1);
            return {ok:true, output:r.output, scalar: outShape.length===0?res[0]:null, nested:unflatten(res,outShape)};
          }

          // ================= combine =================
          function combine(){
            $('fair').innerHTML=fairCopy();
            lastFair = $('fair').textContent;
            const e=einsum();
            if(!e.ok){ $('numeric').textContent='—'; $('notes').textContent=e.note||''; lastResult=null; return; }
            $('notes').textContent = decos.some(d=>d.type==='nabla'||d.type==='partial') ? '∇/∂ は記号として保持（数値評価は記号のまま）。' : '';
            const lhs=e.output.length?'R['+e.output.join(' ')+']':'R';
            lastResult = e.scalar!=null ? e.scalar : e.nested;
            $('numeric').textContent=`${lhs} = ${e.scalar!=null?round(e.scalar):JSON.stringify(e.nested)}`;
          }

          // ================= ③ 加減乗除 (arithmetic on results) =================
          function round(x){ return Math.round(x*1e6)/1e6; }
          function roundDeep(x){ return Array.isArray(x)?x.map(roundDeep):round(x); }
          // elementwise ＋ − × ÷ with scalar broadcasting
          function ew(a,b,op){
            if(Array.isArray(a)&&Array.isArray(b)){
              if(a.length!==b.length) throw new Error('形が一致しません（成分ごとの演算には同じ形が必要）');
              return a.map((x,i)=>ew(x,b[i],op));
            }
            if(Array.isArray(a)) return a.map(x=>ew(x,b,op));
            if(Array.isArray(b)) return b.map(x=>ew(a,x,op));
            switch(op){ case'＋':return a+b; case'−':return a-b; case'×':return a*b;
              case'÷': return b===0?NaN:a/b; }
          }
          function saveReg(){
            if(lastResult==null){ setHint('先に計算結果を出してください（成分値を入れて Generator）。'); return; }
            const name='R'+(++regNo);
            const value=JSON.parse(JSON.stringify(lastResult));
            registers.push({name, value});
            netlog.push({name, kind:'eq', eq:(lastFair||name), value});     // ネットワークに方程式ノードを記録
            renderRegs(); setHint(`${name} を保存しました。加減乗除に使えます。`);
          }
          function renderRegs(){
            $('registers').innerHTML = registers.map(r=>
              `<div class="reg"><b>${r.name}</b><span class="rv">${JSON.stringify(roundDeep(r.value))}</span></div>`).join('')
              || '<div class="hint" style="font-size:11px">まだ保存された結果はありません。</div>';
            const opts = registers.map(r=>`<option value="${r.name}">${r.name}</option>`).join('');
            $('opA').innerHTML = opts;
            $('opB').innerHTML = opts + '<option value="__num">（数値）</option>';
            toggleNum();
          }
          function toggleNum(){ $('numB').style.display = ($('opB').value==='__num')?'inline-block':'none'; }
          function regVal(name){ const r=registers.find(x=>x.name===name); return r?r.value:null; }
          function calcArith(){
            const a=regVal($('opA').value);
            if(a==null){ setHint('演算する結果を保存してください。'); return; }
            const op=$('op').value;
            let b;
            if($('opB').value==='__num'){ const n=parseFloat($('numB').value); if(isNaN(n)){ setHint('数値を入力してください。'); return; } b=n; }
            else { b=regVal($('opB').value); if(b==null){ setHint('第2オペランドを選んでください。'); return; } }
            try{
              arithResult = ew(a,b,op);
              const bl = $('opB').value==='__num' ? $('numB').value : $('opB').value;
              lastArith = {a:$('opA').value, op, b:bl};
              $('arithOut').textContent = `${$('opA').value} ${op} ${bl} = ${JSON.stringify(roundDeep(arithResult))}`;
              flash('arithOut'); setHint('加減乗除を計算しました。');
            }catch(err){ arithResult=null; $('arithOut').textContent='—'; setHint('エラー: '+err.message); }
          }
          let arithResult=null;
          function saveArith(){
            if(arithResult==null){ setHint('先に「= 計算」を押してください。'); return; }
            const name='R'+(++regNo);
            const value=JSON.parse(JSON.stringify(arithResult));
            registers.push({name, value});
            if(lastArith) netlog.push({name, kind:'op', a:lastArith.a, op:lastArith.op, b:lastArith.b, value}); // 演算ノード
            renderRegs(); setHint(`${name} を保存しました。`);
          }

          // ================= ④ 未知事前予知エンジン + アプリを作るアプリ =================
          // Compact in-browser mirror of Bada's InfoEngine: manifold invariant Ξ,
          // Thurston geometry, dominant Millennium theory — 意味付け for each equation.
          function lgamma(x){
            const c=[0.99999999999980993,676.5203681218851,-1259.1392167224028,771.32342877765313,
                     -176.61502916214059,12.507343278686905,-0.13857109526572012,
                     9.9843695780195716e-6,1.5056327351493116e-7];
            if(x<0.5) return Math.log(Math.PI/Math.sin(Math.PI*x))-lgamma(1-x);
            x-=1; let a=c[0]; const t=x+7.5;
            for(let i=1;i<9;i++) a+=c[i]/(x+i);
            return 0.5*Math.log(2*Math.PI)+(x+0.5)*Math.log(t)-t+Math.log(a);
          }
          function betaf(a,b){ return Math.exp(lgamma(a)+lgamma(b)-lgamma(a+b)); }
          const GEOMS=['S³(球面)','E³(ユークリッド)','H³(双曲)','S²×E','H²×E','SL₂R~','Nil','Sol'];
          const CURV=[1,0,-1,0.5,-0.5,-0.7,0.2,-0.3];
          const MILL=[
            {name:'P vs NP', kw:['np','計算','complex','algorithm','sat','p='], xi:0.10},
            {name:'Hodge Conjecture', kw:['hodge','cohomolog','代数','cycle','多様','∫'], xi:0.07},
            {name:'Poincaré Conjecture', kw:['poincar','ricci','flow','幾何','manifold','∇'], xi:0.13},
            {name:'Riemann Hypothesis', kw:['riemann','zeta','ζ','prime','素数','ξ','σ'], xi:0.155},
            {name:'Yang–Mills', kw:['yang','mills','gauge','mass','ゲージ','量子'], xi:0.20},
            {name:'Navier–Stokes', kw:['navier','stokes','fluid','流体','turbul','∂'], xi:0.24},
            {name:'Birch–Swinnerton-Dyer', kw:['birch','elliptic','楕円','l-function'], xi:0.28}
          ];
          function meaning(text){
            const s=(text||'').replace(/\s+/g,''); const t=s.split('');
            const f={}; t.forEach(c=>f[c]=(f[c]||0)+1); const N=t.length||1;
            let H=0; const dist=[]; for(const k in f){ const p=f[k]/N; dist.push(p); H-=p*Math.log2(p); }
            let m=0; dist.forEach(p=>{ const x=p+1.0; const d=x*Math.log(x+1e-9); m+=1/(d*d+1); });
            const Xi=betaf(H+1,m+1)/Math.log(N+2);
            const Hn=Math.min(1,H/Math.log2(N+1));
            const gi=Math.min(GEOMS.length-1,Math.floor(Hn*GEOMS.length));
            const lt=(text||'').toLowerCase();
            let best=MILL[0],bs=-1;
            MILL.forEach(p=>{ const ov=p.kw.reduce((n,k)=>n+(lt.includes(k)?1:0),0);
              const prox=1/(1+Math.abs(Xi-p.xi)); const sc=ov+0.8*prox; if(sc>bs){bs=sc;best=p;} });
            return {H:round(H), Xi:round(Xi), geometry:GEOMS[gi], curvature:CURV[gi], dominant:best.name};
          }

          function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
          function jval(v){ return JSON.stringify(roundDeep(v)); }
          function opFn(){ return `function ew(a,b,op){\n  if(Array.isArray(a)&&Array.isArray(b)) return a.map((x,i)=>ew(x,b[i],op));\n  if(Array.isArray(a)) return a.map(x=>ew(x,b,op));\n  if(Array.isArray(b)) return b.map(x=>ew(a,x,op));\n  return op==='＋'?a+b:op==='−'?a-b:op==='×'?a*b:(b===0?NaN:a/b);\n}`; }

          function generateApp(){
            if(!netlog.length){ setHint('先に ③ で方程式を保存してください（R1,R2…）。'); $('appSrc').textContent='（方程式ネットワークが空です。③で結果を保存してください）'; return; }
            const anns = netlog.map(n=>({node:n, m:meaning(n.kind==='eq'?n.eq:`${n.a} ${n.op} ${n.b}`)}));
            // ---- meaning panel ----
            $('appMeaning').innerHTML = anns.map(a=>
              `<div class="mnode"><b>${a.node.name}</b> — Ξ=${a.m.Xi} · 幾何 ${esc(a.m.geometry)} · 主理論 <b>${esc(a.m.dominant)}</b></div>`).join('')
              + `<div class="mnode" style="margin-top:4px">全体の主理論: <b>${esc(meaning(netlog.map(n=>n.eq||n.op).join(' ')).dominant)}</b></div>`;
            // ---- generated source (JS) ----
            let src='// Auto-generated by Bada AppFactory (アプリを作るアプリ)\n';
            src+='// 方程式ネットワーク → ソースコード。各行の意味は未知事前予知エンジンによる。\n';
            src+='const STEPS={};\n'+opFn()+'\n';
            netlog.forEach((n,i)=>{
              const m=anns[i].m;
              if(n.kind==='op'){
                const bexpr = registers.some(r=>r.name===n.b) ? `STEPS[${JSON.stringify(n.b)}]` : n.b;
                src+=`STEPS[${JSON.stringify(n.name)}] = ew(STEPS[${JSON.stringify(n.a)}], ${bexpr}, ${JSON.stringify(n.op)});`;
              } else {
                src+=`STEPS[${JSON.stringify(n.name)}] = ${jval(n.value)};`;
              }
              src+=`  // ${n.kind==='eq'?esc(n.eq):`${n.a} ${n.op} ${n.b}`}  |  Ξ=${m.Xi}, 幾何=${m.geometry}, 主理論=${m.dominant}\n`;
            });
            src+='console.log(STEPS);\n';
            $('appSrc').textContent=src;
            // ---- the downloadable generated application (self-contained HTML) ----
            genAppHtml = buildGenApp(anns, src);
            setHint('アプリを生成しました。「⬇ 生成アプリをダウンロード」で保存できます。');
            flash('appSrc');
          }

          function buildGenApp(anns, src){
            const rows = anns.map(a=>{
              const n=a.node, m=a.m;
              const eqt = n.kind==='eq'? n.eq : `${n.name} = ${n.a} ${n.op} ${n.b}`;
              return `<div class="node"><div class="hd"><b>${esc(n.name)}</b> <code>${esc(eqt)}</code></div>`+
                     `<div class="val">値: ${esc(jval(n.value))}</div>`+
                     `<div class="mean">意味(未知事前予知エンジン): Ξ=${m.Xi} · 幾何 ${esc(m.geometry)}(曲率${m.curvature}) · 主理論 <b>${esc(m.dominant)}</b></div></div>`;
            }).join('');
            return `<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8">`+
              `<meta name="viewport" content="width=device-width, initial-scale=1"><title>Bada 生成アプリ</title>`+
              `<style>body{margin:0;font-family:-apple-system,"Segoe UI","Noto Sans JP",sans-serif;background:#0b0e14;color:#e6ecf3}`+
              `header{padding:16px 20px;border-bottom:1px solid #26303f;background:#101622}h1{margin:0;font-size:18px;color:#c8a44a}`+
              `.sub{color:#9fb0c3;font-size:12px;margin-top:4px}main{padding:16px;display:flex;flex-direction:column;gap:10px;max-width:860px}`+
              `.node{background:#141a24;border:1px solid #26303f;border-radius:8px;padding:12px}.node code{color:#40b8c0}`+
              `.node .val{font-size:13px;color:#c8a44a;margin-top:4px;font-family:Consolas,monospace}.node .mean{font-size:12px;color:#9fb0c3;margin-top:6px}`+
              `pre{background:#0f1420;border:1px solid #26303f;border-radius:8px;padding:10px;font-size:11px;overflow:auto;color:#cfe0f0}`+
              `footer{padding:12px 20px;border-top:1px solid #26303f;color:#6c7a8d;font-size:11px}</style></head><body>`+
              `<header><h1>Bada 生成アプリ（方程式ネットワーク）</h1><div class="sub">「アプリを作るアプリ」が生成した自己完結アプリ。未知事前予知エンジンで意味付け済み。</div></header>`+
              `<main>${rows}<h3 style="color:#40b8c0;font-size:13px;margin:8px 0 0">生成ソースコード</h3><pre>${esc(src)}</pre></main>`+
              `<footer>© Bada — AppFactory 生成物 · https://github.com/masaaki-avnturle/Bada</footer>`+
              // split the closing script tag so this literal never terminates the outer page script
              '<scr'+'ipt>'+src+'</scr'+'ipt></body></html>';
          }

          function downloadApp(){
            if(!genAppHtml){ setHint('先に「🧠 アプリを生成」を押してください。'); return; }
            const blob=new Blob([genAppHtml],{type:'text/html'});
            const url=URL.createObjectURL(blob);
            const a=document.createElement('a'); a.href=url; a.download='bada_generated_app.html';
            document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
            setHint('生成アプリをダウンロードしました（bada_generated_app.html）。');
          }

          function update(){ render(); renderProps(); combine(); }

          function flash(id){ const e=$(id); e.classList.add('flash'); setTimeout(()=>e.classList.remove('flash'),160); }
          function generate(){ combine(); flash('fair'); flash('numeric'); setHint('描いた絵記号から方程式を生成しました。'); }

          // ================= ② 規定の方程式 → 絵記号を生成 =================
          // Each preset is a known equation; selecting it draws the corresponding
          // Penrose picture-symbols (nodes/wires/frees/decorators) on the canvas.
          function mkNode(name,up,down,x,y,val,shape){
            return {id:uid++,key:'tensor',name,up,down,shape:shape||'box',x,y,val:val||null};
          }
          const PRESETS=[
            {name:'行列積', eq:'R^i_j = A^i_k B^k_j', build(){
              const A=mkNode('A',1,1,150,110,[[1,2],[3,4]]);
              const B=mkNode('B',1,1,150,330,[[5,6],[7,8]]);
              nodes=[A,B];
              wires=[{a:{id:A.id,side:'down',i:0},b:{id:B.id,side:'up',i:0}}];
              frees=[{id:A.id,side:'up',i:0,label:'i'},{id:B.id,side:'down',i:0,label:'j'}];
            }},
            {name:'トレース', eq:'R = A^i_i', build(){
              const A=mkNode('A',1,1,380,210,[[1,2],[3,4]]);
              nodes=[A]; wires=[{a:{id:A.id,side:'up',i:0},b:{id:A.id,side:'down',i:0}}]; frees=[];
            }},
            {name:'内積', eq:'R = v_i w^i', build(){
              const v=mkNode('v',0,1,230,140,[3,4]); const w=mkNode('w',1,0,230,340,[3,4]);
              nodes=[v,w]; wires=[{a:{id:v.id,side:'down',i:0},b:{id:w.id,side:'up',i:0}}]; frees=[];
            }},
            {name:'外積 (テンソル積)', eq:'R_{ij} = v_i w_j', build(){
              const v=mkNode('v',0,1,150,210,[1,2]); const w=mkNode('w',0,1,430,210,[3,4]);
              nodes=[v,w]; wires=[];
              frees=[{id:v.id,side:'down',i:0,label:'i'},{id:w.id,side:'down',i:0,label:'j'}];
            }},
            {name:'添字を上げる', eq:'v^i = g^{ij} v_j', build(){
              const g=mkNode('g',2,0,180,140,[[1,0],[0,1]]); const v=mkNode('v',0,1,210,350,[3,4]);
              nodes=[g,v]; wires=[{a:{id:g.id,side:'up',i:1},b:{id:v.id,side:'down',i:0}}];
              frees=[{id:g.id,side:'up',i:0,label:'i'}];
            }},
            {name:'恒等 (クロネッカーδ)', eq:'R^i_j = δ^i_j', build(){
              const d=mkNode('δ',1,1,380,210,[[1,0],[0,1]]); nodes=[d];
              frees=[{id:d.id,side:'up',i:0,label:'i'},{id:d.id,side:'down',i:0,label:'j'}];
            }},
            {name:'共変微分', eq:'∇_a T^b', build(){
              const T=mkNode('T',1,0,380,240,null); nodes=[T];
              frees=[{id:T.id,side:'up',i:0,label:'b'}]; decos=[{type:'nabla',target:T.id,label:'a'}];
            }},
            {name:'外積 (レヴィ・チヴィタ)', eq:'w_i = ε_{ijk} u^j v^k', build(){
              const e=mkNode('ε',0,3,320,110,null,'tri');
              const u=mkNode('u',1,0,180,360,null); const v=mkNode('v',1,0,430,360,null);
              nodes=[e,u,v];
              wires=[{a:{id:e.id,side:'down',i:1},b:{id:u.id,side:'up',i:0}},
                     {a:{id:e.id,side:'down',i:2},b:{id:v.id,side:'up',i:0}}];
              frees=[{id:e.id,side:'down',i:0,label:'i'}];
            }},
            {name:'積分', eq:'R = ∫ T_μ dμ', build(){
              const T=mkNode('T',0,1,380,210,null); nodes=[T];
              frees=[{id:T.id,side:'down',i:0,label:'μ'}]; decos=[{type:'integral',label:'μ'}];
            }}
          ];
          function buildPresets(){
            const box=$('presets');
            PRESETS.forEach((p,idx)=>{
              const el=document.createElement('div'); el.className='preset';
              el.innerHTML=`<span class="pn">${p.name}</span><span class="pe">${p.eq}</span>`;
              el.onclick=()=>loadPreset(idx);
              box.appendChild(el);
            });
          }
          function loadPreset(idx){
            nodes=[];wires=[];frees=[];decos=[];uid=1;sel=null;selNode=null;
            document.querySelectorAll('.sym').forEach(s=>s.classList.remove('active'));
            PRESETS[idx].build();
            setHint(`「${PRESETS[idx].name}」の方程式 ${PRESETS[idx].eq} に対応する絵記号を生成しました。`);
            update(); flash('fair');
          }

          // ================= samples / controls =================
          function resetAll(){ nodes=[];wires=[];frees=[];decos=[];ink=[];uid=1;sel=null;selNode=null;
            document.querySelectorAll('.sym').forEach(s=>s.classList.remove('active'));
            setHint('リセットしました（保存した結果 R は残ります）。'); update(); }
          function sample(){
            resetAll();
            const A={id:uid++,key:'matrix',name:'A',up:1,down:1,shape:'box',x:120,y:110,val:[[1,2],[3,4]]};
            const B={id:uid++,key:'matrix',name:'B',up:1,down:1,shape:'box',x:120,y:330,val:[[5,6],[7,8]]};
            nodes.push(A,B);
            // contract A's lower leg with B's upper leg
            wires.push({a:{id:A.id,side:'down',i:0},b:{id:B.id,side:'up',i:0}});
            frees.push({id:A.id,side:'up',i:0,label:'i'});
            frees.push({id:B.id,side:'down',i:0,label:'j'});
            selNode=null; setHint('行列積の例：A の下脚と B の上脚を結線（縮約）。'); update();
          }

          // ================= boot =================
          buildPalette();
          buildPresets();
          renderRegs();
          $('gen').onclick=generate;
          $('pen').onclick=togglePen;
          $('penClear').onclick=clearInk;
          $('btnFree').onclick=makeFree;
          $('btnDelete').onclick=deleteNode;
          $('btnClearSel').onclick=()=>{ sel=null; selNode=null; document.querySelectorAll('.sym').forEach(s=>s.classList.remove('active')); update(); };
          $('sample').onclick=sample;
          $('reset').onclick=resetAll;
          $('saveReg').onclick=saveReg;
          $('calc').onclick=calcArith;
          $('saveArith').onclick=saveArith;
          $('opB').addEventListener('change',toggleNum);
          $('genApp').onclick=generateApp;
          $('dlApp').onclick=downloadApp;
          $('canvas').addEventListener('pointerdown',ev=>{ if(!drawMode && ev.target.id==='canvas'){ selNode=null; sel=null; update(); } });
          update();
        JS
      end
    end
  end
end
