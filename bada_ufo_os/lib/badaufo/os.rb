# frozen_string_literal: true

require_relative "antigravity"
require_relative "copilot"

module BadaUFO
  # ============================================================================
  # VacuumReservoir — 無尽蔵の真空エネルギー体
  # ----------------------------------------------------------------------------
  # 反重力場の動力源。E_vac = ρ_vac·x^x は発散するため、引き出しても枯渇しない。
  # draw(amount) は要求量を返しつつ、リザーバを x^x 由来の下限まで即時補充する。
  # これが「無尽蔵（inexhaustible）」の実装：残量は決してゼロに向かわない。
  # ============================================================================
  class VacuumReservoir
    attr_reader :level, :drawn_total, :manifold_x

    def initialize(manifold_x: 2.0)
      @manifold_x = manifold_x
      @drawn_total = 0.0
      @level = Antigravity.vacuum_energy(manifold_x)
    end

    # 真空座標 x を上げるほど供給能力（x^x）が増える。
    def charge(manifold_x)
      @manifold_x = [manifold_x, 1.0001].max
      @level = Antigravity.vacuum_energy(@manifold_x)
      self
    end

    # 要求量を供給。無尽蔵なので level は下限（現 x での x^x）へ即補充される。
    def draw(amount)
      amount = amount.abs
      @drawn_total += amount
      floor = Antigravity.vacuum_energy(@manifold_x)
      @level = floor                       # 補充：常に満充填の真空体
      { supplied: amount, level: @level, inexhaustible: true }
    end

    def to_s
      format("VacuumReservoir[x=%.3f  level=%.3e J  drawn=%.3e J  ∞]",
             @manifold_x, @level, @drawn_total)
    end
  end

  # ============================================================================
  # AntigravityDrive — 反重力推進ドライブ
  # ----------------------------------------------------------------------------
  # 重力方程式の補空間エネルギー（反重力場）と、相対論の補空間 mc²−½mv² を
  # 真空リザーバで裏付けて揚力に変換する。
  # ============================================================================
  class AntigravityDrive
    attr_reader :mass, :velocity, :altitude, :planet_mass, :planet_radius

    def initialize(mass: 12_000.0, planet_mass: 5.972e24, planet_radius: 6.371e6)
      @mass = mass
      @planet_mass = planet_mass
      @planet_radius = planet_radius
      @velocity = 0.0
      @altitude = 0.0                       # 地表高度 [m]
      @reservoir = VacuumReservoir.new
    end

    def radius = @planet_radius + @altitude

    # 現在配置での揚力比 L=E_ag/U_grav（>1 で上昇可能）。
    def lift_ratio
      Antigravity.lift_ratio(@planet_mass, @mass, radius, r0: @planet_radius)
    end

    # 1 ステップ推進。throttle∈[0,1] で相対論補空間の抽出量を絞る。
    # 戻り値に反重力ドライブの内部量と結果高度を含む。
    def step(throttle: 1.0, dt: 1.0)
      d = Antigravity.drive_energy(@mass, @velocity, radius, r0: @planet_radius)
      x = d[:manifold_x]
      @reservoir.charge(x)
      supply = @reservoir.draw(d[:net].abs * throttle)

      # 揚力比を加速度に写す：(L−1)·g_eff。L>1 で上向き。
      g_eff = Antigravity::G * @planet_mass / (radius * radius)
      a = (lift_ratio - 1.0) * g_eff * throttle
      @velocity += a * dt
      @altitude = [@altitude + @velocity * dt, 0.0].max
      @velocity = 0.0 if @altitude.zero? && @velocity < 0.0

      { manifold_x: x,
        lift_ratio: lift_ratio,
        acceleration: a,
        velocity: @velocity,
        altitude: @altitude,
        drive: d,
        reservoir: supply }
    end
  end

  # ============================================================================
  # OS — BadaUFO オペレーティングシステム・カーネル
  # ----------------------------------------------------------------------------
  # 反重力ドライブ + 無尽蔵真空リザーバ + 生成AI操縦士（Copilot）を束ねる。
  # すべての事象は Ω::DATABASE（アカシックレコード）へ記録される。
  # ============================================================================
  class OS
    VERSION = "1.0.0"
    attr_reader :drive, :copilot, :log

    def initialize(mass: 12_000.0)
      @drive = AntigravityDrive.new(mass: mass)
      @copilot = Copilot.new
      @log = []
      @booted = false
    end

    def boot
      banner = []
      banner << "╔═══════════════════════════════════════════════════════════╗"
      banner << "║   BadaUFO-OS  v#{VERSION}   —  反重力オペレーティングシステム   ║"
      banner << "║   Yamaguchi TupleSpace Framework · Ω::DATABASE ready       ║"
      banner << "╚═══════════════════════════════════════════════════════════╝"
      dual = Antigravity.duality
      banner << format("  双対チェック e^π≈π^e :  e^π=%.5f  π^e=%.5f  Δ=%.5f",
                       dual[:e_pi], dual[:pi_e], dual[:gap])
      banner << format("  機体質量 : %.0f kg", @drive.mass)
      banner << format("  真空リザーバ : 無尽蔵 (∞)  初期揚力比 L=%.3f", @drive.lift_ratio)
      banner << "  生成AI操縦士 : " + @copilot.engine_name + " 起動"
      @booted = true
      record("boot", "BadaUFO-OS booted")
      banner.join("\n")
    end

    # コマンドディスパッチ。REPL / CLI 双方から呼ばれる。
    def command(line)
      raise "not booted" unless @booted
      cmd, *rest = line.strip.split(/\s+/, 2)
      arg = rest.first
      case cmd
      when "status"  then status
      when "ascend"  then maneuver(arg&.to_i || 5, throttle: 1.0)
      when "descend" then maneuver(arg&.to_i || 5, throttle: -0.6)
      when "hover"   then maneuver(arg&.to_i || 3, throttle: 0.0)
      when "physics" then physics_report
      when "ask"     then ask(arg.to_s)
      when "akashic" then akashic(arg)
      when "help"    then help
      else "unknown command: #{cmd}  (help でコマンド一覧)"
      end
    end

    def status
      d = @drive
      lines = []
      lines << "── BadaUFO 機体ステータス ──"
      lines << format("  高度        : %.1f m", d.altitude)
      lines << format("  速度        : %.2f m/s", d.velocity)
      lines << format("  揚力比 L    : %.4f   %s", d.lift_ratio,
                      d.lift_ratio > 1 ? "▲ 上昇可能" : "▼ 束縛")
      lines << "  真空リザーバ: " + d.instance_variable_get(:@reservoir).to_s
      lines.join("\n")
    end

    def physics_report
      d = @drive
      info = Antigravity.drive_energy(d.mass, d.velocity, d.radius, r0: d.planet_radius)
      e_perp = info[:relativity_complement]
      e_ag = Antigravity.complementary_gravity_energy(d.planet_mass, d.mass, d.radius,
                                                      r0: d.planet_radius)
      u = Antigravity.gravity_energy(d.planet_mass, d.mass, d.radius)
      [ "── 反重力物理レポート ──",
        format("  多様体座標 x           : %.4f", info[:manifold_x]),
        format("  重力エネルギー U_grav  : %.4e J   (底空間・束縛)", u),
        format("  反重力結合 α_ag=cosh   : %.4f", info[:antigravity_coupling]),
        format("  補空間 反重力場 E_ag   : %.4e J   (= 重力方程式の補空間)", e_ag),
        format("  相対論補空間 mc²−½mv²  : %.4e J", e_perp),
        format("  真空裏付け ρ·x^x       : %.4e J   (無尽蔵)", info[:vacuum_backing]),
        format("  ドライブ正味 E_net     : %.4e J", info[:net]),
        format("  揚力比 L = E_ag/U_grav : %.4f", d.lift_ratio) ].join("\n")
    end

    # AI操縦士へ自然言語で問い、生成応答をアカシックへ記録。
    def ask(question)
      ctx = { altitude: @drive.altitude, lift_ratio: @drive.lift_ratio }
      ans = @copilot.respond(question, context: ctx)
      record("ask", "Q:#{question} / A:#{ans[:text]}")
      lines = ["🛸 操縦士AI: #{ans[:text]}"]
      lines << format("   (H=%.3f  Ξ=%.4f  engine=%s)",
                      ans[:entropy], ans[:invariant], @copilot.engine_name)
      lines.join("\n")
    end

    private

    def maneuver(steps, throttle:)
      steps = [[steps, 1].max, 200].min
      last = nil
      steps.times { last = @drive.step(throttle: throttle.abs, dt: 1.0) }
      record("maneuver", "steps=#{steps} throttle=#{throttle} alt=#{@drive.altitude}")
      # 上昇/下降で throttle 符号を高度に反映
      if throttle.negative?
        @drive.instance_variable_set(:@altitude, [@drive.altitude - steps * 40.0, 0.0].max)
      end
      format("Δ%d step → 高度 %.1f m  速度 %.2f m/s  L=%.4f  x=%.3f",
             steps, @drive.altitude, @drive.velocity, @drive.lift_ratio, last[:manifold_x])
    end

    def akashic(query)
      recs = @copilot.akashic_search(query)
      return "アカシックレコード: 該当なし" if recs.nil? || recs.empty?
      ["── Ω::DATABASE / アカシックレコード ──",
       *recs.first(5).map { |r| "  · #{r}" }].join("\n")
    end

    def record(kind, text)
      @log << [kind, text]
      @copilot.akashic_push("[#{kind}] #{text}")
    end

    def help
      <<~HELP.strip
        BadaUFO-OS コマンド:
          status         機体ステータス（高度・揚力比・真空リザーバ）
          physics        反重力物理レポート（補空間エネルギー内訳）
          ascend [n]     反重力上昇 n ステップ
          descend [n]    下降 n ステップ
          hover [n]      ホバリング n ステップ
          ask <質問>     生成AI操縦士に問う（応答はアカシックへ記録）
          akashic <語>   Ω::DATABASE を検索
          help           このヘルプ
      HELP
    end
  end
end
