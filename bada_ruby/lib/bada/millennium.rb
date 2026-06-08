# frozen_string_literal: true

require_relative "special"
require_relative "entropy"
require_relative "manifold"

module Bada
  # The seven Clay Mathematics Institute Millennium Prize Problems, each rooted
  # in the global partial integral manifold ∬ 1/(x log x)² of the gamma function
  # Γ, with a "theory decomposition" that splits a question across all seven.
  #
  # The reports already touch most of these: ζ/Γ (Riemann), cohomology & D-brane
  # (Hodge), Thurston–Perelman & Ricci flow (Poincaré), quantum group / gauge
  # (Yang–Mills), Ricci-style flow (Navier–Stokes), Shannon entropy (P vs NP),
  # and L-functions of the gamma gauge (Birch–Swinnerton-Dyer).
  module Millennium
    module_function

    PROBLEMS = [
      {
        key: :riemann, name: "Riemann Hypothesis", field: "解析的数論",
        keywords: %w[zeta riemann prime gamma beta critical zeros リーマン ゼータ 素数 ガンマ 臨界],
        signature: "ζ(s) = β(p,q)/log x = x log x, Γ(p)Γ(q)/Γ(p+q)",
        link: "ζ(s)=β(p,q)/log x のゲージそのもので、Γ の部分積分が臨界線を与える"
      },
      {
        key: :hodge, name: "Hodge Conjecture", field: "代数幾何・コホモロジー",
        keywords: %w[hodge cohomology cohom dbrane brane sheaf cycle projection ホッジ コホモロジー 代数 層 サイクル],
        signature: "cohom D_χ(M)[I_m], D-brane isotopy, sheaf of manifold, double integrate of projection",
        link: "コホモロジー類 cohom D_χ(M) が D-brane のアイソトピーとして多様体上に実現される"
      },
      {
        key: :poincare, name: "Poincaré Conjecture (解決)", field: "幾何学的トポロジー",
        keywords: %w[poincare thurston perelman ricci flow geometriz sphere ポアンカレ サーストン ペレルマン リッチ 幾何化 多様体 トポロジー],
        signature: "d/dt g_ij = -2 R_ij, Thurston Perelman manifold, S^3 geometrization",
        link: "Ricci 流 d/dt g_ij = -2R_ij が大域的多様体を S^3 へ幾何化する（ペレルマンにより解決）"
      },
      {
        key: :yang_mills, name: "Yang–Mills Existence & Mass Gap", field: "場の量子論",
        keywords: %w[yang mills gauge quantum group mass gap quark gluon ヤン ミルズ ゲージ 質量 量子 クォーク 場],
        signature: "⊕(iℏ∇)^⊕L, quantum group, vector of constance for zeta function, quarks levels",
        link: "ゲージ作用素 ⊕(iℏ∇)^⊕L の質量ギャップが ζ の量子群スペクトルとして現れる"
      },
      {
        key: :navier_stokes, name: "Navier–Stokes Existence & Smoothness", field: "偏微分方程式・流体",
        keywords: %w[navier stokes flow smooth turbulence viscous gradient laplacian ナビエ ストークス 流体 滑らか 乱流 粘性],
        signature: "global partial differential equation, integrate of cut, -Δv + ∇_i∇_j v",
        link: "大域的部分微分方程式の滑らかさが Ricci 流型の ∬1/(x log x)² 正則化で保たれる"
      },
      {
        key: :p_np, name: "P vs NP", field: "計算複雑性",
        keywords: %w[complexity computation entropy shannon information polynomial 計算 複雑 エントロピー 情報 多項式 シャノン],
        signature: "Shannon entropy H = -Σ p log p, manifold entropy invariant Ξ",
        link: "探索の困難さがシャノンエントロピー H と多様体不変量 Ξ の分解可能性として定式化される"
      },
      {
        key: :bsd, name: "Birch–Swinnerton-Dyer Conjecture", field: "数論・楕円曲線",
        keywords: %w[birch swinnerton dyer elliptic curve lfunction rank バーチ 楕円曲線 楕円 階数 数論],
        signature: "L(E,s) at s=1, Γ-factor, rank of elliptic curve, β(p,q)/log x gauge",
        link: "楕円曲線の L 関数 L(E,1) が Γ 因子つき β(p,q)/log x ゲージの階数として分解される"
      }
    ].freeze

    def problems
      PROBLEMS
    end

    # Characteristic manifold invariant of each problem's signature text.
    def signature_invariant(problem)
      @sig_cache ||= {}
      @sig_cache[problem[:key]] ||= Manifold.xi(problem[:signature])
    end

    # Gamma-function-rooted coupling: every problem is reached from the global
    # partial integral manifold ∬ 1/(x log x)² of Γ. The coupling strength is
    # the beta/zeta gauge between the question's invariant and the problem's.
    def gamma_coupling(xi_q, problem)
      xi_p = signature_invariant(problem)
      # zeta gauge β(p,q)/log x with p,q from the two invariants
      Special.zeta_gauge(xi_q + 1.0, xi_p + 1.0, 2.0 + (xi_q - xi_p).abs)
    end

    # Decompose a question's theory across all seven problems: rank by keyword
    # overlap + manifold-invariant proximity + gamma coupling, and emit a theory
    # fragment for each that starts from the global partial integral manifold.
    def decompose_theory(text, top: 7)
      raw = text.is_a?(String) ? text.downcase : Array(text).join(" ").downcase
      tokens = Entropy.tokenize(raw)
      h = Entropy.shannon(tokens)
      xi_q = Manifold.xi(tokens)

      scored = PROBLEMS.map do |prob|
        # Substring match (handles Japanese, which is tokenized per-character).
        overlap = prob[:keywords].count { |k| raw.include?(k.downcase) }
        xi_p = signature_invariant(prob)
        proximity = 1.0 / (1.0 + (xi_q - xi_p).abs)
        coupling = gamma_coupling(xi_q, prob)
        score = overlap * 1.0 + proximity * 0.8 + coupling * 0.4
        {
          key: prob[:key], name: prob[:name], field: prob[:field],
          score: score, overlap: overlap, invariant: xi_p,
          coupling: coupling,
          theory: "#{prob[:name]}：ガンマ関数 Γ の大域的部分積分多様体 ∬1/(x·log x)² を起点に、" \
                  "#{prob[:link]}。(関連度 #{format('%.3f', score)}, Ξ=#{format('%.3f', xi_p)})"
        }
      end

      ranked = scored.sort_by { |s| -s[:score] }.first(top)
      {
        question_entropy: h,
        question_invariant: xi_q,
        origin: "Γ → ∬ 1/(x·log x)² （ガンマ関数における大域的部分積分多様体）",
        dominant: ranked.first[:name],
        decomposition: ranked
      }
    end
  end
end
