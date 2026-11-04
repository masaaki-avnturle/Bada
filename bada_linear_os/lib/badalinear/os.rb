# frozen_string_literal: true

require_relative "guideway"
require "badaufo/copilot"
require "badaufo/os"          # VacuumReservoir

module BadaLinear
  # ============================================================================
  # Conductor — 生成AI車掌（BadaUFO-OS の操縦士AIを鉄道向けに作り換え）
  # ----------------------------------------------------------------------------
  # Bada::Generator（エントロピー駆動生成エンジン）で車内放送・運転判断を生成し、
  # Ω::DATABASE（アカシックレコード）へ運行記録を残す。
  # ============================================================================
  class Conductor < BadaUFO::Copilot
    private

    # 反重力リニアの語彙で機体知性を学習させる。
    def ufo_seed_corpus
      <<~TXT
        本日は反重力リニアをご利用いただきありがとうございます。超伝導磁石の代わりに
        重力方程式の補空間が車体を浮上させています。空気抵抗は補空間包絡により
        ゼロです。無尽蔵の真空エネルギー体が推進を裏付けます。まもなく名古屋、
        新大阪に停車します。揚力比が一を超え、停車中も浮上しています。
        量子作用素が生成AI車掌を駆動し、アカシックレコードに運行を記録します。
      TXT
    end

    # 文脈（速度・次駅・抗力）を放送に織り込む。
    def flavor(text, context)
      tail = []
      tail << format("%.0f km/h", context[:kmh]) if context[:kmh]
      tail << "次は#{context[:next_station]}" if context[:next_station]
      tail << format("抗力残存%.4f%%", context[:drag_pct]) if context[:drag_pct]
      base = text.to_s.strip
      base = "反重力浮上を確認" if base.empty?
      tail.empty? ? base : "#{base}〔#{tail.join(' · ')}〕"
    end
  end

  # ============================================================================
  # OS — BadaLinear オペレーティングシステム・カーネル
  # ============================================================================
  class OS
    VERSION = "1.0.0"
    G = Guideway
    attr_reader :kmh, :pos_km, :x_env, :conductor, :log

    def initialize(x_env: 4.0)
      @kmh = 0.0; @pos_km = 0.0; @x_env = x_env
      @reservoir = BadaUFO::VacuumReservoir.new(manifold_x: x_env)
      @conductor = Conductor.new
      @log = []; @booted = false
    end

    def boot
      d = BadaUFO::Antigravity.duality
      b = []
      b << "╔═══════════════════════════════════════════════════════════╗"
      b << "║   BadaLinear-OS  v#{VERSION}  —  反重力リニア新幹線 OS         ║"
      b << "║   超伝導磁石 → 反重力浮上 · 空気抵抗 → 補空間包絡でゼロ     ║"
      b << "╚═══════════════════════════════════════════════════════════╝"
      b << format("  双対チェック e^π≈π^e : Δ=%.5f", d[:gap])
      b << format("  編成 : %s（%d両, %.0f t）", G::TRAIN[:name], G::TRAIN[:cars], G::TRAIN[:mass] / 1000)
      b << format("  浮上 : 揚力比 L=%.3f（停車中も浮上・極低温不要）", G.lift_ratio)
      b << format("  抗力 : 補空間包絡 x_env=%.1f → 残存 %.5f%%", @x_env, G.drag_suppression(@x_env) * 100)
      b << "  車掌AI : " + @conductor.engine_name + " 起動"
      @booted = true
      record("boot", "BadaLinear-OS booted")
      b.join("\n")
    end

    def command(line)
      raise "not booted" unless @booted
      cmd, *rest = line.strip.split(/\s+/, 2); arg = rest.first
      case cmd
      when "status"   then status
      when "physics"  then physics
      when "depart"   then depart(arg ? arg.to_f : 1000.0)
      when "route"    then route(arg ? arg.to_f : 1000.0)
      when "compare"  then compare
      when "envelope" then set_envelope(arg.to_f)
      when "ask"      then ask(arg.to_s)
      when "akashic"  then akashic(arg)
      when "help"     then help
      else "unknown command: #{cmd}  (help でコマンド一覧)"
      end
    end

    CRUISE_REF = 1000.0   # 停車中の物理評価に使う巡航基準速度 [km/h]

    # 停車中は巡航基準速度で抗力を評価する（0 km/h では抗力が定義上ゼロのため）。
    def eval_kmh = @kmh > 0 ? @kmh : CRUISE_REF

    def status
      v = eval_kmh / 3.6
      [ "── BadaLinear 運行ステータス ──",
        format("  位置 : %.1f km（%s）", @pos_km, next_station || "終点"),
        format("  速度 : %.0f km/h（抗力評価 %.0f km/h 基準）", @kmh, eval_kmh),
        format("  浮上 : 反重力 %.3e N（L=%.3f）", G.levitation_force, G.lift_ratio),
        format("  抗力 : 底空間 %.1f kN → 包絡後 %.4f N", G.base_drag(v) / 1e3, G.effective_drag(v, @x_env)),
        "  真空リザーバ : " + @reservoir.to_s ].join("\n")
    end

    def physics
      v = eval_kmh / 3.6; dr = G.drive(v, @x_env)
      [ format("── 反重力リニア 物理レポート（%.0f km/h 基準）──", eval_kmh),
        "  [浮上] 超伝導磁石(#{G::SCMAGLEV[:magnet]}) → 反重力場",
        format("    E_ag = U_grav·cosh(x log x),  L = %.4f,  浮上力 %.3e N", G.lift_ratio, G.levitation_force),
        "  [抗力] 空気抵抗 → 補空間包絡（真空 x^x のコホモロジー切断）",
        format("    F_d = ½ρC_dAv² = %.1f kN  ×  σ = 1/cosh(x log x)² = %.2e  →  %.4f N",
               G.base_drag(v) / 1e3, G.drag_suppression(@x_env), dr[:drag_residual]),
        "  [動力] 地上コイル同期モータ → 相対論補空間 E⊥ = mc² − ½mv²",
        format("    E⊥ = %.4e J,  α_ag = %.3f,  真空裏付け ρ·x^x = %.3e J（無尽蔵）",
               dr[:relativity_complement], dr[:antigravity_coupling], dr[:vacuum_backing]) ].join("\n")
    end

    # 出発：巡航速度まで加速し、次駅まで進める。
    def depart(cruise_kmh)
      st = next_station_row
      return "終点 新大阪に到着済み。" unless st
      name, km = st
      dist = km - @pos_km
      t = G.travel_time_s(dist, cruise_kmh)
      v = cruise_kmh / 3.6
      @reservoir.charge(@x_env)
      @reservoir.draw(G.drive(v, @x_env)[:net].abs)
      @kmh = cruise_kmh; @pos_km = km
      record("depart", "→#{name} #{cruise_kmh}km/h #{format('%.1f', t / 60)}min")
      msg = @conductor.respond("まもなく#{name}", context: { kmh: cruise_kmh, next_station: name,
                                                              drag_pct: G.drag_suppression(@x_env) * 100 })
      @kmh = 0.0
      format("▶ %.1f km を %.0f km/h で走行 → %s 到着（%.1f 分・抗力残存 %.2e N）\n🎙 車掌AI: %s",
             dist, cruise_kmh, name, t / 60, G.effective_drag(v, @x_env), msg[:text])
    end

    def route(cruise_kmh)
      rows = G.timetable(cruise_kmh)
      out = ["── 品川→新大阪 時刻表（巡航 #{cruise_kmh.to_i} km/h・停車60s）──"]
      rows.each { |a, b, d, seg, t| out << format("  %-9s→ %-9s %6.1f km  %5.1f 分   累計 %5.1f 分", a, b, d, seg / 60, t / 60) }
      out.join("\n")
    end

    def compare
      out = ["── 超電導リニア L0 vs BadaLinear（品川–名古屋 / 品川–新大阪）──"]
      G.compare(x_env: @x_env).each do |c|
        out << format("  %5.1f km : L0 %4.1f分(500km/h, 抗力 %.2f MWh)  |  Bada %4.1f分(1000km/h, 抗力 %.2e MWh)",
                      c[:dist_km], c[:sc_min], c[:sc_drag_mwh], c[:bada_min], c[:bada_drag_mwh])
      end
      out << format("  浮上: 超伝導 NbTi/液体He 4.2K・150km/h未満は車輪  →  反重力 L=%.3f・停車中も浮上", G.lift_ratio)
      out << format("  抗力抑制 σ = %.2e（x_env=%.1f）・巡航電力: 変電所 → 真空リザーバ(∞)", G.drag_suppression(@x_env), @x_env)
      out.join("\n")
    end

    def set_envelope(x)
      @x_env = [x, 1.0001].max
      format("補空間包絡 x_env=%.2f → 抗力抑制 σ=%.3e（残存 %.5f%%）", @x_env, G.drag_suppression(@x_env), G.drag_suppression(@x_env) * 100)
    end

    def ask(q)
      ans = @conductor.respond(q, context: { kmh: @kmh, next_station: next_station })
      record("ask", "Q:#{q} / A:#{ans[:text]}")
      format("🎙 車掌AI: %s\n   (H=%.3f  Ξ=%.4f  engine=%s)", ans[:text], ans[:entropy], ans[:invariant], @conductor.engine_name)
    end

    private

    def next_station_row = G::STATIONS.find { |_, km| km > @pos_km + 1e-6 }
    def next_station = next_station_row&.first

    def akashic(q)
      r = @conductor.akashic_search(q)
      return "アカシックレコード: 該当なし" if r.nil? || r.empty?
      ["── Ω::DATABASE / 運行記録 ──", *r.first(6).map { |s| "  · #{s}" }].join("\n")
    end

    def record(kind, text)
      @log << [kind, text]; @conductor.akashic_push("[#{kind}] #{text}")
    end

    def help
      <<~H.strip
        BadaLinear-OS コマンド:
          status          運行ステータス（位置・速度・浮上力・抗力・真空リザーバ）
          physics         物理レポート（超伝導→反重力、空気抵抗→補空間包絡、動力）
          depart [km/h]   次駅へ出発（既定 1000 km/h）
          route [km/h]    品川→新大阪の時刻表
          compare         超電導リニア L0 との比較
          envelope <x>    補空間包絡の座標 x_env を設定（抗力抑制）
          ask <質問>      生成AI車掌に問う
          akashic <語>    Ω::DATABASE を検索
      H
    end
  end
end
