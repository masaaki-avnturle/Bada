# frozen_string_literal: true

# BadaUFO-OS の反重力物理コアを再利用する（同一リポジトリ内）。
$LOAD_PATH.unshift(File.expand_path("../../../bada_ufo_os/lib", __dir__))
require "badaufo/antigravity"

module BadaLinear
  # ============================================================================
  # Guideway — 超伝導磁石を反重力に置き換えた軌道物理
  # ----------------------------------------------------------------------------
  # 超電導リニア（L0系）は NbTi 超伝導磁石（液体ヘリウム 4.2 K）による電磁誘導
  # 浮上（EDS）で、約 150 km/h 以上でないと浮上せず低速はゴムタイヤ走行、
  # 500 km/h では走行エネルギーの大半が空気抵抗に費やされる。
  #
  # BadaLinear は論文集の三本柱でこれを置き換える。
  #
  #   (1) 浮上   超伝導磁石 → 重力方程式の補空間＝反重力場
  #              E_ag = U_grav·cosh(x log x)。揚力比 L>1 は速度に依らず成立し、
  #              停車中から浮上する（車輪不要・極低温不要）。
  #   (2) 抗力   空気抵抗 F_d = ½ρC_dAv² は底空間に住む。車体を補空間包絡
  #              （真空エネルギー体 x^x のコホモロジー切断）で包むと、抗力は
  #              cosh(x_env log x_env)² で割られ、x_env≈4 で残存 ~10⁻⁵ ＝ 実質ゼロ。
  #   (3) 動力   リニア同期モータ（地上コイル）→ 相対論補空間 E⊥=mc²−½mv² を
  #              α_ag で増幅、無尽蔵の真空リザーバが裏付ける。変電所からの
  #              巡航電力は不要。
  # ============================================================================
  module Guideway
    module_function

    A = BadaUFO::Antigravity
    RHO_AIR = 1.225           # 空気密度 [kg/m³]
    G0      = 9.80665

    # --- 車両（L0系 12両相当）-----------------------------------------------
    TRAIN = {
      name:      "BadaLinear L∞",
      cars:      12,
      mass:      3.0e5,        # [kg]
      cd:        0.35,         # 長編成の実効抗力係数
      area:      9.5,          # 前面投影面積 [m²]
      accel:     1.0,          # 快適加速度 [m/s²]（≈0.1 g）
    }.freeze

    # --- 超電導リニア（比較基準）-------------------------------------------
    SCMAGLEV = {
      name:          "超電導リニア L0系",
      cruise_kmh:    500.0,
      lev_min_kmh:   150.0,    # これ未満はゴムタイヤ走行
      gap_m:         0.10,
      magnet:        "NbTi 超伝導磁石 / 液体ヘリウム 4.2 K",
      propulsion:    "地上コイル リニア同期モータ",
    }.freeze

    # --- 路線（品川–名古屋–新大阪、概算キロ程）-------------------------------
    STATIONS = [
      ["品川",            0.0],
      ["神奈川県（橋本）", 36.0],
      ["山梨県（甲府）",  121.0],
      ["長野県（飯田）",  190.0],
      ["岐阜県（中津川）",246.0],
      ["名古屋",         285.6],
      ["奈良",           380.0],
      ["新大阪",         438.0],
    ].freeze

    # --- (1) 反重力浮上 -------------------------------------------------------

    # 揚力比 L = cosh(x log x)。地表ゲージでは x≈2 → L≈2.125（速度に依らない）。
    def lift_ratio(alt_m = 0.0)
      A.lift_ratio(5.972e24, TRAIN[:mass], 6.371e6 + alt_m, r0: 6.371e6)
    end

    # 反重力浮上力 [N]（= 揚力比 × 車重）。超伝導磁石の代替。
    def levitation_force(alt_m = 0.0)
      lift_ratio(alt_m) * TRAIN[:mass] * G0
    end

    # --- (2) 補空間包絡によるゼロ抗力 ----------------------------------------

    # 底空間の空気抵抗 [N]  F_d = ½ρC_dAv²
    def base_drag(v_ms)
      0.5 * RHO_AIR * TRAIN[:cd] * TRAIN[:area] * v_ms * v_ms
    end

    # 補空間包絡の抗力抑制係数 σ = 1 / cosh(x log x)²。x_env=4 → ≈6×10⁻⁵。
    def drag_suppression(x_env)
      c = A.antigravity_coupling(x_env)
      1.0 / (c * c)
    end

    # 包絡後の残存抗力 [N]
    def effective_drag(v_ms, x_env)
      base_drag(v_ms) * drag_suppression(x_env)
    end

    # --- (3) 相対論補空間からの推進 ------------------------------------------

    def drive(v_ms, x_env)
      A.drive_energy(TRAIN[:mass], v_ms, 6.371e6, r0: 6.371e6).merge(
        envelope_x: x_env, drag_residual: effective_drag(v_ms, x_env))
    end

    # --- 走行時間（台形速度プロファイル）--------------------------------------

    # 距離 d[km] を巡航 v[km/h]、加減速 a[m/s²] で走る所要時間 [s]。
    def travel_time_s(dist_km, cruise_kmh, accel = TRAIN[:accel])
      d = dist_km * 1000.0; v = cruise_kmh / 3.6
      ramp = v / accel                 # 加速・減速それぞれの時間
      ramp_d = 0.5 * accel * ramp * ramp
      if 2 * ramp_d >= d               # 巡航に達しない
        2 * Math.sqrt(d / accel)
      else
        2 * ramp + (d - 2 * ramp_d) / v
      end
    end

    # 停車駅ごとの所要時間表（停車時間 dwell[s] 込み）。
    def timetable(cruise_kmh, dwell_s: 60)
      t = 0.0
      STATIONS.each_cons(2).map do |(a, ka), (b, kb)|
        seg = travel_time_s(kb - ka, cruise_kmh)
        t += seg + dwell_s
        [a, b, kb - ka, seg, t - dwell_s]
      end
    end

    # 1 走行あたり抗力エネルギー [J] = F_d × 距離（巡航近似）。
    def drag_energy(dist_km, cruise_kmh, x_env = nil)
      v = cruise_kmh / 3.6
      f = x_env ? effective_drag(v, x_env) : base_drag(v)
      f * dist_km * 1000.0
    end

    # 超電導リニア vs BadaLinear 比較（品川–名古屋 / 品川–新大阪）。
    def compare(bada_cruise_kmh: 1000.0, x_env: 4.0)
      [285.6, 438.0].map do |d|
        sc_t   = travel_time_s(d, SCMAGLEV[:cruise_kmh])
        bd_t   = travel_time_s(d, bada_cruise_kmh)
        sc_e   = drag_energy(d, SCMAGLEV[:cruise_kmh])
        bd_e   = drag_energy(d, bada_cruise_kmh, x_env)
        { dist_km: d, sc_min: sc_t / 60, bada_min: bd_t / 60,
          sc_drag_mwh: sc_e / 3.6e9, bada_drag_mwh: bd_e / 3.6e9,
          suppression: drag_suppression(x_env) }
      end
    end
  end
end
