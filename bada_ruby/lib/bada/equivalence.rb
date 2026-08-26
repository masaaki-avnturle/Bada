# frozen_string_literal: true

require_relative "special"

module Bada
  # Bada::Equivalence — 等価原理・放射性崩壊・トポロジーの標準ライブラリ
  #
  # Bada 言語から `eotvos(...)` のように呼び出せる関数群。いずれも
  # 教科書どおりの物理・数学で、外部データや実験装置の設計値は含まない。
  #
  #   等価原理 : 慣性質量 m_i と重力質量 m_g が等価であるという原理。
  #              エトヴェシュ比 η = 2(a₁−a₂)/(a₁+a₂) で破れを測る。
  #              m_g/m_i が両者で等しければ η = 0。
  #
  #   半減期   : dN/dt = −λN、T½ = ln2/λ。壊変系列は Bateman 方程式。
  #
  #   トポロジー: メビウスの帯の二重被覆、オイラー標数、巻き数。
  #
  # ⚠️ 概念シミュレーション。核種の実データや臨界計算は含まない。
  module Equivalence
    module_function

    # --- 等価原理 -------------------------------------------------------- #

    # 重力場中の落下加速度 a = (m_g/m_i)·g。
    # 等価原理が厳密なら m_g/m_i は物質によらず 1 で、a = g。
    def acceleration(g, m_grav, m_inert)
      raise ArgumentError, "inertial mass must be > 0" if m_inert <= 0

      g * (m_grav.to_f / m_inert.to_f)
    end

    # エトヴェシュ比 η = 2(a₁−a₂)/(a₁+a₂)。
    # 2 つの試験体の落下加速度の相対差。等価原理が成り立てば 0。
    def eotvos(a1, a2)
      denom = a1 + a2
      return 0.0 if denom.abs < 1e-300

      2.0 * (a1 - a2) / denom
    end

    # 2 物体の (m_g, m_i) から直接 η を求める。
    def eotvos_ratio(m_grav1, m_inert1, m_grav2, m_inert2, g = 9.80665)
      eotvos(acceleration(g, m_grav1, m_inert1),
             acceleration(g, m_grav2, m_inert2))
    end

    # 自由落下の測地線を積分し、時刻 t での位置と速度を返す。
    # 等価原理のもとでは初期条件が同じなら質量によらず同一の軌道になる。
    # 戻り値: [x, v]
    def free_fall(g, m_grav, m_inert, t, x0 = 0.0, v0 = 0.0)
      a = acceleration(g, m_grav, m_inert)
      [x0 + v0 * t + 0.5 * a * t * t, v0 + a * t]
    end

    # 重力赤方偏移 Δν/ν = gh/c² （等価原理から導かれる帰結）。
    def redshift(g, height, c = 299_792_458.0)
      g * height / (c * c)
    end

    # --- 放射性崩壊 / 半減期 ---------------------------------------------- #

    # 崩壊定数 λ = ln2 / T½
    def decay_constant(half_life)
      raise ArgumentError, "half-life must be > 0" if half_life <= 0

      Math.log(2.0) / half_life.to_f
    end

    # 半減期 T½ = ln2 / λ
    def half_life(lambda_)
      raise ArgumentError, "lambda must be > 0" if lambda_ <= 0

      Math.log(2.0) / lambda_.to_f
    end

    # 指数崩壊則 N(t) = N₀·exp(−λt)
    def decay(n0, half_life, t)
      n0.to_f * Math.exp(-decay_constant(half_life) * t.to_f)
    end

    # 残存比 N/N₀ = 2^(−t/T½)
    def remaining_fraction(half_life, t)
      2.0**(-t.to_f / half_life.to_f)
    end

    # 放射能 A = λN（単位時間あたりの崩壊数）
    def activity(n0, half_life, t)
      decay_constant(half_life) * decay(n0, half_life, t)
    end

    # Bateman 方程式による壊変系列 A → B → C → …
    #
    #   half_lives : 各核種の半減期（最後の核種は安定なら nil を渡す）
    #   n0         : 親核種の初期量
    #   t          : 時刻
    #
    # 戻り値: 各核種の量の配列。総量は常に n0 に保存される。
    def decay_chain(half_lives, n0, t)
      lams = half_lives.map { |h| h.nil? ? 0.0 : decay_constant(h) }
      n = lams.size
      out = Array.new(n, 0.0)

      # 親核種は単純な指数崩壊
      out[0] = n0.to_f * Math.exp(-lams[0] * t)

      # 娘以降は Bateman の解（λ が縮退していない場合の閉形式）
      (1...n).each do |k|
        sum = 0.0
        (0..k).each do |i|
          denom = 1.0
          ok = true
          (0..k).each do |j|
            next if j == i

            d = lams[j] - lams[i]
            if d.abs < 1e-12
              ok = false   # 縮退 → 閉形式が使えない
              break
            end
            denom *= d
          end
          next unless ok

          sum += Math.exp(-lams[i] * t) / denom
        end
        prod = (0...k).reduce(1.0) { |acc, j| acc * lams[j] }
        out[k] = n0.to_f * prod * sum
      end

      # 最終核種が安定 (λ=0) なら、収支の残りをそこへ入れて総量を保存する
      if lams.last.zero?
        out[-1] = n0.to_f - out[0...-1].sum
      end
      out
    end

    # 永年平衡の目安: 親の半減期が娘よりはるかに長いとき、
    # 娘の量は N_B ≈ N_A·λ_A/λ_B に近づく。
    def secular_equilibrium_ratio(half_life_parent, half_life_daughter)
      decay_constant(half_life_parent) / decay_constant(half_life_daughter)
    end

    # --- トポロジー -------------------------------------------------------- #

    # メビウスの帯の二重被覆: 1 周で向きが反転し、2 周で戻る。
    # laps 周したあとの向き (+1 / −1) を返す。
    def mobius_orientation(laps)
      laps.to_i.even? ? 1 : -1
    end

    # 向き付け可能か（偶数周で元に戻っているか）。
    def orientable_return?(laps)
      mobius_orientation(laps) == 1
    end

    # オイラー標数 χ = V − E + F
    def euler_characteristic(vertices, edges, faces)
      vertices - edges + faces
    end

    # 種数 g の向き付け可能閉曲面の χ = 2 − 2g
    def genus_to_euler(genus)
      2 - 2 * genus
    end

    # メビウスの帯の χ は 0（円板と同じ 1 ではない）。
    def mobius_euler
      0
    end

    # 巻き数（写像度）: 角度の総変化を 2π で割ったもの。
    # angles は連続な角度列（ラジアン）。
    def winding_number(angles)
      return 0.0 if angles.size < 2

      total = 0.0
      (1...angles.size).each do |i|
        d = angles[i] - angles[i - 1]
        # 分枝の飛びを [-π, π) に畳む
        d -= 2 * Math::PI while d >= Math::PI
        d += 2 * Math::PI while d < -Math::PI
        total += d
      end
      total / (2 * Math::PI)
    end

    # --- Γ多様体との接続 ---------------------------------------------------- #

    # 等価原理を Γ 多様体上で書く: 部分積分の漸化 Γ(s+1)=s·Γ(s) は
    # 「s ステップ進めても関係式の形が変わらない」という不変性を持つ。
    # 質量比 m_g/m_i がこの不変量に一致するとき η = 0 になることを、
    # 比 1.0 からのずれとして数値化する。
    def gamma_invariance_defect(s)
      lhs = Special.gamma(s + 1.0)
      rhs = s * Special.gamma(s)
      return 0.0 if lhs.abs < 1e-300

      (lhs - rhs).abs / lhs.abs
    end
  end
end
