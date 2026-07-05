# frozen_string_literal: true

require_relative "jones"
require_relative "telomere"

module OmegaIQ
  # IQ測定 — the IQ measurement, fused from the invariants above.
  #
  # Four normalised components (each ~[0,1]):
  #   complexity : Jones exponent span (topological richness of the strand)
  #   magnitude  : |V(t_eval)| probed at the thermometer's Boltzmann point
  #   entropy    : telomere split entropy (bits, normalised by the Hayflick limit)
  #   coherence  : thermal spatial order from the IR camera
  #
  # raw = weighted mean in [0,1]; IQ standardised to mean 100, sd 15 by a fixed
  # calibration (raw = 0.5 -> IQ 100, gain 60), so results are reproducible.
  #
  # 真逆 (mirror): every score is also computed for the mirror knot (V(1/t)) with
  # the telomere's opposite action (elongation, not shortening). `divergence` is
  # |IQ - IQ_mirror|: the subject's chirality — 0 for a perfectly balanced
  # (amphichiral) 上がる作用=下げる作用 state.
  class IQ
    WEIGHTS = { complexity: 0.30, magnitude: 0.20, entropy: 0.30, coherence: 0.20 }.freeze
    CALIB_MEAN = 0.5
    CALIB_GAIN = 60.0

    Result = Struct.new(:iq, :components, :raw, :jones, keyword_init: true)

    def initialize(crossings, t_eval:, coherence:)
      @crossings = crossings
      @t_eval = t_eval
      @coherence = coherence
    end

    # Full measurement: forward (順) and 真逆 (mirror), plus their divergence.
    def measure
      forward = score(@crossings, invert_action: false)
      reverse = score(Jones.mirror(@crossings), invert_action: true)
      {
        iq: forward.iq,
        mirror_iq: reverse.iq,
        divergence: (forward.iq - reverse.iq).abs.round(1),
        chiral_balance: (200.0 - (forward.iq - reverse.iq).abs).round(1),
        forward: forward,
        reverse: reverse,
        band: band(forward.iq)
      }
    end

    private

    def score(crossings, invert_action:)
      jones = Jones.polynomial(crossings)
      span = jones.zero? ? 0 : (jones.max_exp - jones.min_exp) / 4.0
      complexity = squash(span / 4.0)

      mag = jones.eval(@t_eval).abs
      magnitude = squash(Math.log(1 + mag))

      tel = Telomere.new(crossings).divide
      hl = [tel.hayflick_limit, 1].max
      ent = tel.entropy / (Math.log2(hl + 1) + 1e-9)
      # 真逆: opposite telomere action reflects the entropy about its midpoint
      ent = 1.0 - ent if invert_action
      entropy = squash(ent)

      coherence = squash(@coherence)

      comps = { complexity: complexity, magnitude: magnitude,
                entropy: entropy, coherence: coherence }
      raw = WEIGHTS.sum { |k, w| w * comps[k] }
      iq = (100 + CALIB_GAIN * (raw - CALIB_MEAN)).round(1)
      Result.new(iq: iq, components: comps, raw: raw.round(4), jones: jones)
    end

    # Smooth clamp to (0,1) via a logistic so extreme inputs never saturate hard.
    def squash(x)
      1.0 / (1.0 + Math.exp(-4.0 * (x - 0.5)))
    end

    def band(iq)
      case iq
      when ...85 then "senescent-strand (低テロメア活性)"
      when 85...100 then "baseline"
      when 100...115 then "elevated"
      when 115...130 then "high-coherence"
      else "superchiral (超分裂活性)"
      end
    end
  end
end
