# frozen_string_literal: true

require_relative "jones"

module OmegaIQ
  # Jones多項式のテロメアの分裂過程 — the telomere splitting process.
  #
  # A telomere is modelled as the knotted strand described by the PD code. Cell
  # division = one application of the Kauffman skein at the "telomere crossing":
  # the crossing is resolved into its A-smoothing and its B-smoothing, producing
  # two daughter diagrams, each with one fewer crossing. Repeating this builds a
  # binary division tree; the telomere "shortens" by one crossing per generation
  # (a Hayflick step) and reaches senescence (the unknot) when no crossing is
  # left.
  #
  #   generation g : diagrams have (n - g) crossings, 2^g daughters
  #   loop spectrum: the multiset of circle-counts of the fully-smoothed states
  #   split entropy: Shannon entropy of that loop spectrum (bits)
  class Telomere
    attr_reader :crossings, :generations, :spectrum, :entropy, :length0

    def initialize(crossings)
      @crossings = crossings
      @length0 = crossings.length
    end

    def divide
      @generations = []
      remaining = @crossings.dup
      gen = 0
      until remaining.empty?
        @generations << {
          generation: gen,
          telomere_length: remaining.length,
          daughters: 2**gen
        }
        remaining = smooth_one(remaining) # resolve the leading (telomere) crossing
        gen += 1
      end
      @generations << { generation: gen, telomere_length: 0, daughters: 2**gen, senescent: true }
      @spectrum = loop_spectrum
      @entropy = shannon(@spectrum)
      self
    end

    # Number of divisions before senescence (== initial crossing number).
    def hayflick_limit
      @length0
    end

    private

    # A-smoothing of the leading (telomere) crossing: identify the joined arc
    # pairs, drop the crossing, and relabel. Returns the diagram with one fewer
    # crossing (the shortened telomere for the next generation).
    def smooth_one(cross)
      return [] if cross.empty?

      _id, e0, e1, e2, e3, _s = cross.first
      pairs = [[e0, e1], [e2, e3]] # A-smoothing identifications
      merge = {}
      pairs.each { |x, y| merge[y] = x }
      cross.drop(1).map do |cid, a0, a1, a2, a3, ss|
        [cid, merge.fetch(a0, a0), merge.fetch(a1, a1),
         merge.fetch(a2, a2), merge.fetch(a3, a3), ss]
      end
    end

    # Circle-count of every fully-smoothed state (the 2^n leaves of the tree).
    def loop_spectrum
      n = @crossings.length
      labels = @crossings.flat_map { |c| c[1, 4] }.uniq
      spec = Hash.new(0)
      (0...(1 << n)).each do |state|
        uf = UnionFind.new(labels)
        @crossings.each_with_index do |c, i|
          Jones.apply_smoothing(uf, c, state[i].zero?)
        end
        spec[uf.component_count] += 1
      end
      spec
    end

    def shannon(spec)
      total = spec.values.sum.to_f
      return 0.0 if total.zero?

      -spec.values.sum do |cnt|
        p = cnt / total
        p.positive? ? p * Math.log2(p) : 0.0
      end
    end
  end
end
