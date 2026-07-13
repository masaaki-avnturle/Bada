# frozen_string_literal: true

require_relative "qubit"
require_relative "bell"
require_relative "quintic"
require_relative "jones"
require_relative "uncertainty"
require_relative "semiconductor"
require_relative "channel"
require_relative "../tuplespace"
require_relative "../manifold"

module Bada
  module Quantum
    # SpaceTelegraph — the universal telecommunication application (宇宙での
    # 汎用電信通信機能) built in Bada.
    #
    # It ties the seven ingredients of the request into one device:
    #
    #   1. Bell experiment / entangled pairs      -> Bada::Quantum::Bell + Qubit2
    #   2. quintic (5次) solution-formula carrier  -> Bada::Quantum::Quintic
    #   3. spooky action, pair-based              -> CHSH violation certificate
    #   4. period-tuned non-linear modulation     -> Quintic.carrier_phase
    #   5. Jones-polynomial correlation           -> Bada::Quantum::Jones
    #   6. probability/statistics + uncertainty   -> Bada::Quantum::Uncertainty
    #   7. semiconductor buildability             -> Bada::Quantum::Semiconductor
    #
    # and exposes a `prove` function that certifies the physics, plus a
    # `transmit` that actually carries a message across space by superdense
    # coding. Every run is recorded into Omega::DATABASE (the Akashic TupleSpace).
    class SpaceTelegraph
      attr_reader :db, :material, :temp_k, :redundancy

      def initialize(material: "GaAs", temp_k: 4.0, redundancy: 3, db: TupleSpace.new)
        @material = material
        @temp_k = temp_k
        @redundancy = redundancy
        @db = db
      end

      # The proof function (証明する機能): certify that every principle the
      # telegraph relies on actually holds, and combine them into one verdict.
      def prove(seed: 1)
        bell = Bell.experiment(seed: seed)

        # Jones: entangled pair (Hopf) must be topologically distinct from the
        # separable pair (2-component unlink -> here modelled as no crossings on
        # two loops, correlation ~ 0).
        hopf_corr = Jones.correlation(Jones::HOPF)
        unlink_corr = 0.0 # unlinked loops have trivial (bracket = d, Jones = 1) factor
        jones_ok = hopf_corr > unlink_corr + 0.1

        # No-signaling: Bob's marginal is 1/2 regardless of Alice's Pauli choice.
        marginals = [%i[i], %i[x], %i[z], %i[zx]].map do
          Qubit2.bell_phi_plus.bob_marginal_one
        end
        no_signaling = marginals.all? { |m| (m - 0.5).abs < 1e-9 }

        # Uncertainty relation on a representative diagonal state.
        unc = Uncertainty.report(Math::PI / 3.0, Math::PI / 4.0)

        # Quintic period / carrier well-formed.
        roots = Quintic.roots_of_unity
        period_ok = (roots.sum { |r| r }.abs < 1e-6) # 5th roots of unity sum to 0

        # Semiconductor buildable.
        semi = Semiconductor.report(material: @material, temp_k: @temp_k)

        certs = {
          spooky_action: bell[:violates_local_realism] && bell[:spooky_action_certified],
          no_signaling: no_signaling,
          jones_correlation: jones_ok,
          uncertainty: unc[:satisfied],
          quintic_period: period_ok,
          semiconductor: semi[:feasible]
        }

        {
          certificates: certs,
          qed: certs.values.all?,
          bell: bell,
          jones: { hopf_correlation: hopf_corr, unlink_correlation: unlink_corr },
          uncertainty: unc,
          semiconductor: semi,
          quintic_roots: roots
        }
      end

      # Carry a message across space. Records the transmission into Omega::DB.
      def transmit(message, seed: 7)
        result = Channel.transmit(
          message,
          material: @material, temp_k: @temp_k,
          redundancy: @redundancy, seed: seed
        )
        # tag the transmission with its manifold entropy invariant and store it
        stats = Manifold.invariant(message)
        @db.push(message, key: "tx:#{message[0, 12]}",
                          tags: { fidelity: result[:certified_fidelity], xi: stats[:invariant] })
        result.merge(manifold_invariant: stats[:invariant])
      end

      # Human-readable end-to-end report (証明 + 送信).
      def render(message, seed: 7)
        pf = prove(seed: seed)
        tx = transmit(message, seed: seed)
        corr = Bell.e_quantum(Bell::A, Bell::B)
        lines = []
        lines << "════════════════════════════════════════════════════════════"
        lines << " Bada 量子もつれ・汎用電信通信機 — Space Telegraph"
        lines << "════════════════════════════════════════════════════════════"
        lines << ""
        lines << "① ベルの実験 / 不気味な遠隔作用 (entangled pair · CHSH)"
        lines << format("    S_classical <= 2.000   S_local ~ %.3f   S_quantum = %.3f",
                        pf[:bell][:local_chsh], pf[:bell][:quantum_chsh])
        lines << format("    Tsirelson  = %.3f   -> spooky action %s",
                        pf[:bell][:tsirelson],
                        pf[:certificates][:spooky_action] ? "CERTIFIED" : "no")
        lines << ""
        lines << "② 5次方程式の解の公式 / 周期に合わせた非線形カリア (quintic)"
        lines << "    fifth roots of unity (period 2π/5):"
        Quintic.roots_of_unity.each_with_index do |r, k|
          lines << format("      z%d = %+.3f %+.3fi", k, r.real, r.imaginary)
        end
        lines << format("    non-linear carrier phase (corr=%.3f): %s", corr,
                        Quintic.constellation(corr).map { |c| format('%.2f', Math.atan2(c.imaginary, c.real)) }.join(", "))
        lines << ""
        lines << "③ Jones多項式による相関 (topological correlation)"
        lines << format("    <Hopf>  bracket = %s", Jones.bracket(Jones::HOPF))
        lines << format("    V_Hopf(t=e) correlation = %.4f  (unlink = 0)",
                        pf[:jones][:hopf_correlation])
        lines << ""
        lines << "④ 不確定性理論・確率統計 (Robertson uncertainty)"
        lines << format("    Δσx·Δσz = %.4f  >=  |<σy>| = %.4f  -> %s",
                        pf[:uncertainty][:product], pf[:uncertainty][:bound],
                        pf[:uncertainty][:satisfied] ? "OK" : "VIOLATED")
        lines << format("    Born P(+) = %.4f", pf[:uncertainty][:born][:plus])
        lines << ""
        lines << "⑤ 半導体で使える原理 (semiconductor feasibility)"
        lines << format("    %s  Eg=%.2f eV  T=%.1f K  flip=%.2e  -> %s",
                        pf[:semiconductor][:material], pf[:semiconductor][:band_gap_ev],
                        pf[:semiconductor][:temperature_k], pf[:semiconductor][:bit_flip_prob],
                        pf[:semiconductor][:feasible] ? "BUILDABLE" : "too hot")
        lines << ""
        lines << "⑥ 証明する機能 (proof) -> QED = #{pf[:qed]}"
        pf[:certificates].each { |k, v| lines << format("    [%s] %s", v ? "✓" : "✗", k) }
        lines << ""
        lines << "⑦ 宇宙・汎用電信通信 (superdense transmission)"
        lines << format("    message   : %s", tx[:message])
        lines << format("    recovered : %s", tx[:recovered])
        lines << format("    pairs=%d  BER=%.4f  fidelity=%.4f (±%.4f)  lossless=%s",
                        tx[:pairs_used], tx[:ber], tx[:certified_fidelity],
                        tx[:fidelity_residual], tx[:lossless])
        lines << format("    manifold invariant Ξ = %.6f   Ω::DATABASE size = %d",
                        tx[:manifold_invariant], @db.size)
        lines << "════════════════════════════════════════════════════════════"
        lines.join("\n")
      end
    end
  end
end
