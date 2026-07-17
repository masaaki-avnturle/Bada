# frozen_string_literal: true

require_relative "manifold"
require_relative "thurston"
require_relative "catastrophe"
require_relative "language"

module Bada
  # Foundry — "an application that builds applications", in the Bada language.
  #
  # 山口フレームワークの方程式ネットワーク（方程式同士の関係）を入力に取り、
  # アプリ自身の「未知事前予知エンジン」(Thurston–Perelman 配置 + カタストロフィ
  # 分岐 = InfoEngine の前段) で各方程式に *意味付け* を行い、その意味から
  #
  #   1. Bada 言語のソースコード（`.bada`）
  #   2. 実行可能な子アプリ（自己完結 HTML）
  #
  # を生成する。生成された子アプリ自体もダウンロード対象になる。
  #
  # Pipeline per equation (precognition / 未知事前予知):
  #   * Manifold.invariant   -> Ξ (global partial integral manifold entropy)
  #   * Thurston.place_entropy -> which model geometry the equation lands in
  #   * Catastrophe.decompose  -> branch count (how many sub-components to spawn)
  # geometry -> a UI/behaviour archetype for the generated app module.
  module Foundry
    module_function

    # 8つのサーストン幾何 -> 子アプリのモジュール原型（描画挙動）への写像。
    ARCHETYPES = {
      "S^3"     => { archetype: "pulse_rings",  role: "共鳴コア",     hue: 205 },
      "H^1×E^1" => { archetype: "hyper_fan",    role: "分岐ファン",   hue: 28  },
      "E^1"     => { archetype: "lattice",      role: "格子場",       hue: 150 },
      "S^1×E^1" => { archetype: "orbit",        role: "軌道系",       hue: 265 },
      "S^2×E^1" => { archetype: "sphere_wave",  role: "球面波",       hue: 190 },
      "H^1×S^1" => { archetype: "spiral",       role: "対数螺旋",     hue: 320 },
      "H^1"     => { archetype: "tessellation", role: "双曲網",       hue: 12  },
      "S^2×E"   => { archetype: "bloom",        role: "放射ブルーム", hue: 95  }
    }.freeze

    DEFAULT_ARCH = { archetype: "lattice", role: "格子場", hue: 150 }.freeze

    # 1方程式を未知事前予知エンジンに通し、意味付けされたモジュール仕様を返す。
    def meaning(equation, index: 0)
      inv = Manifold.invariant(equation)
      place = Thurston.place_entropy(equation)
      branches =
        begin
          Catastrophe.decompose(equation)[:branch_count]
        rescue StandardError
          1
        end
      arch = ARCHETYPES.fetch(place[:geometry], DEFAULT_ARCH)
      {
        index: index,
        equation: equation,
        xi: inv[:invariant],
        entropy: inv[:entropy],
        manifold: inv[:manifold_integral],
        extent: inv[:extent],
        geometry: place[:geometry],
        curvature: place[:curvature],
        kind: place[:kind].to_s,
        perelman_f: place[:perelman_f],
        ricci_collapsed: place[:ricci_collapsed],
        branches: [[branches, 1].max, 6].min,
        archetype: arch[:archetype],
        role: arch[:role],
        hue: arch[:hue]
      }
    end

    # 方程式ネットワーク（文字列配列）全体をアプリ仕様へ意味付け。
    # requirement: 作りたいアプリの要求文（説明可能に取り込む）。
    def spec(equations, app_name: nil, requirement: nil)
      mods = equations.reject { |e| e.to_s.strip.empty? }
                      .each_with_index.map { |eq, i| meaning(eq, index: i) }
      xi_total = mods.sum { |m| m[:xi] }
      name = app_name || derive_name(mods)
      req = requirement.to_s.strip.empty? ? nil : requirement_analysis(requirement)
      { name: name, xi_total: xi_total, module_count: mods.length, modules: mods, requirement: req }
    end

    # 要求文自体を未知事前予知エンジンで解析（説明可能な取り込み）。
    def requirement_analysis(text)
      inv = Manifold.invariant(text)
      place = Thurston.place_entropy(text)
      arch = ARCHETYPES.fetch(place[:geometry], DEFAULT_ARCH)
      { text: text, xi: inv[:invariant], entropy: inv[:entropy],
        geometry: place[:geometry], curvature: place[:curvature], role: arch[:role] }
    end

    # ネットワークの支配的幾何からアプリ名を導出。
    def derive_name(mods)
      return "Bada::EmptyApp" if mods.empty?
      dom = mods.group_by { |m| m[:geometry] }
                .max_by { |_, v| v.sum { |m| m[:xi] } }&.first
      arch = ARCHETYPES.fetch(dom, DEFAULT_ARCH)
      "Bada::#{arch[:archetype].split('_').map(&:capitalize).join}App"
    end

    # 意味付け仕様から Bada 言語のソースコードを生成（Interpreter で実行可能）。
    def bada_source(spec)
      lines = []
      lines << "# #{spec[:name]} — auto-generated Bada program"
      lines << "# forged by Bada::Foundry from an equation network"
      lines << "# modules=#{spec[:module_count]}  Xi_total=#{format('%.4f', spec[:xi_total])}"
      lines << ""
      spec[:modules].each do |m|
        v = m[:index]
        lines << "# module ##{m[:index]} [#{m[:role]} / #{m[:geometry]}] archetype=#{m[:archetype]}"
        lines << "set m#{v} = #{format('%.6f', m[:xi])}"
        lines << "m#{v} <- #{m[:equation].inspect}"
        lines << "m#{v} -< #{format('%.6f', m[:manifold] + 1.0)}"
        lines << "m#{v} >- m#{v}"
        lines << "Omega::push m#{v} as #{m[:archetype]}_#{m[:index]}"
        lines << "print m#{v}"
        lines << ""
      end
      lines.join("\n")
    end

    # 生成された Bada プログラムを実行し、TupleSpace への書き込み結果を返す
    # （子アプリが「意味を持って動く」ことの実行証跡）。
    def run_bada(source)
      Interpreter.new.run(source)
    end

    # 意味付け仕様から実行可能な子アプリ（自己完結 HTML）を生成。
    def app_html(spec)
      require "json"
      mods_json = JSON.generate(spec[:modules].map do |m|
        {
          i: m[:index], eq: m[:equation], xi: m[:xi], h: m[:entropy],
          geom: m[:geometry], curv: m[:curvature], role: m[:role],
          arch: m[:archetype], hue: m[:hue], branches: m[:branches]
        }
      end)
      title = spec[:name]
      <<~HTML
        <!DOCTYPE html>
        <html lang="ja"><head><meta charset="UTF-8">
        <meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no">
        <title>#{title}</title>
        <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{background:#06080f;color:#cfe0ff;font-family:Georgia,serif;overflow-x:hidden}
        header{padding:16px 20px;border-bottom:1px solid rgba(80,160,255,.15)}
        h1{font-weight:300;letter-spacing:.25em;font-size:16px;color:#8fb8ff}
        .sub{font-size:9px;letter-spacing:.3em;color:#5a7ec0;margin-top:6px}
        #grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:14px;padding:18px}
        .mod{border:1px solid rgba(80,160,255,.15);border-radius:6px;background:rgba(8,14,28,.7);overflow:hidden}
        .mod canvas{width:100%;height:180px;display:block;background:radial-gradient(ellipse at 50% 45%,rgba(15,25,55,.9),#06080f)}
        .mod .meta{padding:8px 10px;font-size:9px;letter-spacing:.08em;line-height:1.7;color:#9ab4e0}
        .mod .eq{color:#e0c080;font-style:italic;font-size:9.5px;word-break:break-all}
        .mod .role{color:#7fb0ff;letter-spacing:.2em;text-transform:uppercase;font-size:8px}
        footer{padding:14px 20px;font-size:8px;letter-spacing:.25em;color:#4a6ba0;border-top:1px solid rgba(80,160,255,.12)}
        </style></head><body>
        <header><h1>#{title}</h1>
        <div class="sub">FORGED BY BADA FOUNDRY · #{spec[:module_count]} MODULES · Ξ=#{format('%.3f', spec[:xi_total])}</div></header>
        <div id="grid"></div>
        <footer>Bada language child-application · 山口フレームワーク 方程式ネットワーク由来 · © Masaaki Yamaguchi</footer>
        <script>const MODULES=#{mods_json};</script>
        <script>#{child_render_js}</script>
        </body></html>
      HTML
    end

    # 子アプリに埋め込む共通レンダラ（8原型を Ξ / 曲率 / 分岐数で駆動）。
    def child_render_js
      <<~'JS'
        const grid=document.getElementById('grid');
        function mkModule(m){
          const wrap=document.createElement('div');wrap.className='mod';
          const cv=document.createElement('canvas');
          const meta=document.createElement('div');meta.className='meta';
          meta.innerHTML='<span class="role">'+m.role+' · '+m.geom+'</span><br>'+
            '<span class="eq">'+m.eq+'</span><br>Ξ='+m.xi.toFixed(4)+' · H='+m.h.toFixed(3)+' · 分岐'+m.branches;
          wrap.appendChild(cv);wrap.appendChild(meta);grid.appendChild(wrap);
          const ctx=cv.getContext('2d');
          function size(){const dpr=window.devicePixelRatio||1;cv.width=cv.clientWidth*dpr;cv.height=180*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);}
          size();window.addEventListener('resize',size);
          const hue=m.hue, sp=0.4+Math.min(2,m.xi)*0.8, n=Math.max(2,m.branches+2);
          const col=(a)=>'hsla('+hue+',80%,65%,'+a+')';
          let t=0;
          function frame(){
            const w=cv.clientWidth,h=180,cx=w/2,cy=h/2;
            ctx.clearRect(0,0,w,h);ctx.lineWidth=1.2;ctx.strokeStyle=col(.8);ctx.fillStyle=col(.8);
            ctx.shadowColor=col(.6);ctx.shadowBlur=8;
            const s=Math.min(w,h)*0.4;
            switch(m.arch){
              case 'pulse_rings':for(let i=0;i<n;i++){const r=s*(0.2+0.8*i/n)*(0.85+0.15*Math.sin(t*sp+i));ctx.beginPath();ctx.arc(cx,cy,r,0,7);ctx.stroke();}break;
              case 'hyper_fan':for(let i=0;i<n*2;i++){const a=-1+(i/(n*2-1))*2;ctx.beginPath();ctx.moveTo(cx,cy);for(let u=0;u<=s;u+=3){const y=Math.sinh(u/s*1.4)*14;ctx.lineTo(cx+Math.cos(a+t*sp*.1)*u,cy+Math.sin(a)*u+y);}ctx.stroke();}break;
              case 'lattice':{const g=s/n;ctx.globalAlpha=.9;for(let i=-n;i<=n;i++){const off=Math.sin(t*sp+i)*6;ctx.beginPath();ctx.moveTo(cx+i*g+off,cy-s);ctx.lineTo(cx+i*g,cy+s);ctx.stroke();ctx.beginPath();ctx.moveTo(cx-s,cy+i*g+off);ctx.lineTo(cx+s,cy+i*g);ctx.stroke();}ctx.globalAlpha=1;}break;
              case 'orbit':for(let i=0;i<n;i++){const a=t*sp*(1+i*.2)+i,r=s*(0.3+0.6*i/n);const x=cx+Math.cos(a)*r,y=cy+Math.sin(a)*r*.6;ctx.beginPath();ctx.arc(cx,cy,r,0,7);ctx.globalAlpha=.25;ctx.stroke();ctx.globalAlpha=1;ctx.beginPath();ctx.arc(x,y,4,0,7);ctx.fill();}break;
              case 'sphere_wave':for(let i=0;i<n+3;i++){const ph=i/(n+3);ctx.beginPath();for(let a=0;a<=6.3;a+=.1){const rr=s*(0.3+0.5*ph)*(1+0.12*Math.sin(a*3+t*sp));ctx.lineTo(cx+Math.cos(a)*rr,cy+Math.sin(a)*rr*(0.4+0.5*ph));}ctx.closePath();ctx.globalAlpha=.5;ctx.stroke();ctx.globalAlpha=1;}break;
              case 'spiral':ctx.beginPath();for(let a=0;a<n*6.3;a+=.08){const r=s*a/(n*6.3);ctx.lineTo(cx+Math.cos(a+t*sp)*r,cy+Math.sin(a+t*sp)*r);}ctx.stroke();break;
              case 'tessellation':{const pts=[];for(let i=0;i<n+2;i++){const a=i/(n+2)*6.3+t*sp*.2;pts.push([cx+Math.cos(a)*s,cy+Math.sin(a)*s]);}for(let i=0;i<pts.length;i++)for(let j=i+1;j<pts.length;j++){ctx.globalAlpha=.4;ctx.beginPath();ctx.moveTo(pts[i][0],pts[i][1]);ctx.lineTo(pts[j][0],pts[j][1]);ctx.stroke();}ctx.globalAlpha=1;}break;
              case 'bloom':for(let i=0;i<n*2;i++){const a=i/(n*2)*6.3;ctx.beginPath();for(let u=0;u<=1;u+=.05){const rr=s*u,pet=Math.sin(u*Math.PI)*20*Math.sin(t*sp+i);ctx.lineTo(cx+Math.cos(a)*rr-Math.sin(a)*pet,cy+Math.sin(a)*rr+Math.cos(a)*pet);}ctx.stroke();}break;
              default:ctx.beginPath();ctx.arc(cx,cy,s*.6,0,7);ctx.stroke();
            }
            t+=0.03;requestAnimationFrame(frame);
          }
          frame();
        }
        MODULES.forEach(mkModule);
      JS
    end

    # 方程式群 → プログラミング言語への変換（:bada / :javascript / :python / :ruby）。
    def to_language(spec, lang)
      case lang.to_s
      when "javascript", "js" then lang_js(spec)
      when "python", "py"     then lang_py(spec)
      when "ruby", "rb"       then lang_rb(spec)
      else bada_source(spec)
      end
    end

    def lang_js(spec)
      out = []
      out << "// #{spec[:name]} — 方程式群 → JavaScript (Bada Foundry)"
      out << "// 要求: #{spec[:requirement][:text]}" if spec[:requirement]
      out << "const xLogX=x=>x<=0?0:x*Math.log(x);"
      out << "const manifold=m=>1/((xLogX(m+2)**2)||1);   // -< ∬1/(x·logx)²"
      out << "const rightAct=x=>Math.exp(-xLogX(Math.abs(x)+1e-6)); // >- e^{-x·logx}"
      out << "const MODULES=["
      spec[:modules].each do |m|
        out << "  {id:#{m[:index]}, equation:#{m[:equation].inspect}, archetype:#{m[:archetype].inspect}, " \
               "xi:#{format('%.6f', m[:xi])}, M:#{format('%.6f', m[:manifold])}},"
      end
      out << "];"
      out << "for(const m of MODULES){const a=rightAct(manifold(m.M));" \
             "console.log(`#${m.id} ${m.archetype} Ξ=${m.xi.toFixed(4)} act=${a.toExponential(4)}`);}"
      out.join("\n")
    end

    def lang_py(spec)
      out = []
      out << "# #{spec[:name]} — 方程式群 → Python (Bada Foundry)"
      out << "# 要求: #{spec[:requirement][:text]}" if spec[:requirement]
      out << "import math"
      out << "def x_log_x(x): return 0.0 if x<=0 else x*math.log(x)"
      out << "def manifold(m): return 1.0/((x_log_x(m+2)**2) or 1.0)   # -< ∬1/(x·logx)²"
      out << "def right_act(x): return math.exp(-x_log_x(abs(x)+1e-6)) # >- e^{-x·logx}"
      out << "MODULES=["
      spec[:modules].each do |m|
        out << "    {\"id\":#{m[:index]}, \"equation\":#{m[:equation].inspect}, \"archetype\":#{m[:archetype].inspect}, " \
               "\"xi\":#{format('%.6f', m[:xi])}, \"M\":#{format('%.6f', m[:manifold])}},"
      end
      out << "]"
      out << "for m in MODULES:"
      out << "    a=right_act(manifold(m[\"M\"]))"
      out << "    print(f'#{'#'}{m[\"id\"]} {m[\"archetype\"]} Xi={m[\"xi\"]:.4f} act={a:.4e}')"
      out.join("\n")
    end

    def lang_rb(spec)
      out = []
      out << "# #{spec[:name]} — 方程式群 → Ruby (Bada Foundry)"
      out << "# 要求: #{spec[:requirement][:text]}" if spec[:requirement]
      out << "def x_log_x(x) = x<=0 ? 0.0 : x*Math.log(x)"
      out << "def manifold(m) = 1.0/(((x_log_x(m+2)**2)).nonzero? || 1.0)   # -< ∬1/(x·logx)²"
      out << "def right_act(x) = Math.exp(-x_log_x(x.abs+1e-6))             # >- e^{-x·logx}"
      out << "MODULES=["
      spec[:modules].each do |m|
        out << "  {id: #{m[:index]}, equation: #{m[:equation].inspect}, archetype: #{m[:archetype].inspect}, " \
               "xi: #{format('%.6f', m[:xi])}, m: #{format('%.6f', m[:manifold])}},"
      end
      out << "]"
      out << "MODULES.each { |mod| puts format(\"#%d %s Xi=%.4f act=%.4e\", mod[:id], mod[:archetype], mod[:xi], right_act(manifold(mod[:m]))) }"
      out.join("\n")
    end

    # 説明可能: 要求 + 方程式群 → 生成物の根拠を日本語で説明。
    def explanation(spec)
      out = []
      out << "■ 生成アプリ: #{spec[:name]} (#{spec[:module_count]} モジュール / Ξ_total=#{format('%.4f', spec[:xi_total])})"
      if spec[:requirement]
        r = spec[:requirement]
        out << "■ 要求の取り込み（説明可能）"
        out << "  要求文: 「#{r[:text]}」"
        out << format("  解析 → Ξ=%.4f / H=%.3f / サーストン幾何=%s（原型: %s）。同系幾何のモジュールが要求の中核挙動を担う。",
                      r[:xi], r[:entropy], r[:geometry], r[:role])
      else
        out << "■ 要求文は未入力（方程式ネットワークのみから構成）。"
      end
      out << "■ 方程式群 → モジュールの意味付け"
      spec[:modules].each do |m|
        out << "  ● #{m[:equation]}"
        out << format("     H=%.3f → 幾何 %s (κ=%s) → 原型「%s」(%s), 分岐%d, Ξ=%.4f",
                      m[:entropy], m[:geometry], m[:curvature], m[:role], m[:archetype], m[:branches], m[:xi])
        out << "     ★ 要求の幾何と一致" if spec[:requirement] && spec[:requirement][:geometry] == m[:geometry]
      end
      out << "■ 生成物: (1) 4言語へ変換 (2) 実行可能な子アプリ HTML (3) APK/EXE 化プロジェクト一式"
      out.join("\n")
    end

    # 一括生成: 仕様・Bada ソース・子アプリ HTML・説明をまとめて返す。
    def forge(equations, app_name: nil, requirement: nil)
      s = spec(equations, app_name: app_name, requirement: requirement)
      {
        spec: s,
        bada_source: bada_source(s),
        app_html: app_html(s),
        explanation: explanation(s)
      }
    end
  end
end
