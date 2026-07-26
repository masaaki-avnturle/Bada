# frozen_string_literal: true

require_relative "special_bridge"

module BadaUFO
  # ============================================================================
  # Bada::Antigravity — 反重力場エネルギーの物理コア
  # ----------------------------------------------------------------------------
  # 山口フレームワーク（TupleSpace / 大域的微分・積分多様体理論）に基づく反重力
  # エンジンの数値中核。ユーザ理論の三本柱を、そのまま Bada の作用素で実装する。
  #
  #   (1) 重力方程式の「補空間」= 反重力場のエネルギー量
  #         重力 U_grav = G·M·m/r は多様体の底空間（束縛部）に住む。その
  #         コホモロジーの cut（∬1/(x log x)² dx_m の切断）＝補空間 に住むのが
  #         反重力場。補空間側の結合は反重力回転作用素
  #             □_ag(x) = 2( sin(i·x log x) + cos(i·x log x) ) = 2·cosh(x log x)
  #         の実部で与えられ、x>1 で単調増加＝際限なく増幅する。
  #
  #   (2) 特殊相対性理論の補空間 = E = mc² − ½mv² の補空間エネルギー
  #         全エネルギー mc² のうち運動として費やされるのは ½mv²。残り
  #             E_⊥ = mc² − ½mv²
  #         が「補空間に温存された」抽出可能エネルギー。これを反重力回転で
  #         増幅して揚力に変換する。
  #
  #   (3) 反重力場 = 無尽蔵の真空エネルギー体
  #         真空リザーバは □_dal(x) = e^{x log x} = x^x（ダランヴァージアン
  #         箱作用素の実部）でモデル化。x^x は発散する＝汲めども尽きぬ無尽蔵性。
  #         引き出しても下限を割らず、常に補充される（VacuumReservoir 参照）。
  #
  #   双対チェック:  e^π ≈ π^e  （重力 / 反重力の双対、Special.gravity_dual）
  # ============================================================================
  module Antigravity
    module_function

    C = 299_792_458.0            # 光速 [m/s]
    G = 6.674_30e-11             # 万有引力定数 [m³ kg⁻¹ s⁻²]
    RHO_VAC = 5.0e-10            # 真空エネルギー密度スケール [J] (基準ゲージ)

    # --- 多様体座標 ----------------------------------------------------------
    # 物理配置（無次元化した半径・速度比）を、作用素が住むネイピア円上の
    # 多様体座標 x>1 に写す。x=1 は x log x=0 の臨界（ネイピア）ステップ。
    def manifold_coord(ratio)
      1.0 + (ratio.abs.finite? ? ratio.abs : 0.0)
    end

    # --- (1) 重力とその補空間 ------------------------------------------------

    # 重力ポテンシャルエネルギーの大きさ  U = G·M·m / r  [J]（底空間・束縛部）。
    def gravity_energy(big_mass, mass, r)
      r = 1e-9 if r <= 0.0
      G * big_mass * mass / r
    end

    # 反重力結合係数  α_ag(x) = Re[□_ag(x)] / 2 = cosh(x log x) ≥ 1。
    # 補空間側での増幅率。x>1 で急増し、無尽蔵性の源となる。
    def antigravity_coupling(x)
      SpecialBridge.box_antigravity(x).real / 2.0
    end

    # 重力方程式の「補空間」に住む反重力場エネルギー [J]。
    #   E_ag = U_grav · α_ag(x)          （束縛エネルギーをコホモロジー切断で
    #                                       補空間へ持ち上げ、反重力回転で増幅）
    # x は半径ゲージ r/r0 から得た多様体座標。
    def complementary_gravity_energy(big_mass, mass, r, r0: 6.371e6)
      u = gravity_energy(big_mass, mass, r)
      x = manifold_coord(r0 / (r <= 0 ? 1e-9 : r))
      u * antigravity_coupling(x)
    end

    # --- (2) 特殊相対性理論とその補空間 --------------------------------------

    def rest_energy(mass)   = mass * C * C          # E = mc²
    def kinetic_energy(mass, v) = 0.5 * mass * v * v # ½mv²

    # 特殊相対性理論の補空間エネルギー  E_⊥ = mc² − ½mv²  [J]。
    # 運動に費やされなかった＝補空間に温存された抽出可能エネルギー。
    def complementary_relativity_energy(mass, v)
      rest_energy(mass) - kinetic_energy(mass, v)
    end

    # --- (3) 無尽蔵の真空エネルギー体 ----------------------------------------

    # 真空エネルギー体  E_vac = ρ_vac · x^x  [J]。
    # □_dal(x)=e^{x log x}=x^x（ダランヴァージアン箱作用素）。x^x は発散する
    # ため、引き出す量に対し常に上回る＝無尽蔵。
    def vacuum_energy(x)
      SpecialBridge.box_dalanversian(x).real * RHO_VAC
    end

    # --- 統合: 反重力ドライブの揚力 -----------------------------------------

    # 反重力揚力比  L = E_ag / U_grav。L>1 で機体は上昇する。
    # 補空間の反重力エネルギーが束縛重力を上回る度合い。
    def lift_ratio(big_mass, mass, r, r0: 6.371e6)
      u = gravity_energy(big_mass, mass, r)
      return Float::INFINITY if u <= 0.0
      complementary_gravity_energy(big_mass, mass, r, r0: r0) / u
    end

    # 反重力ドライブが 1 ステップで供給する正味エネルギー [J]。
    #   相対論補空間 E_⊥ を反重力結合で増幅し、真空リザーバが裏付ける。
    def drive_energy(mass, v, r, r0: 6.371e6)
      x = manifold_coord(r0 / (r <= 0 ? 1e-9 : r))
      e_perp = complementary_relativity_energy(mass, v)
      coupling = antigravity_coupling(x)
      { manifold_x: x,
        relativity_complement: e_perp,
        antigravity_coupling: coupling,
        vacuum_backing: vacuum_energy(x),
        net: e_perp * coupling }
    end

    # 重力 / 反重力双対の健全性チェック  e^π ≈ π^e。
    def duality
      d = SpecialBridge.gravity_dual
      d.merge(gap: (d[:e_pi] - d[:pi_e]).abs)
    end
  end
end
