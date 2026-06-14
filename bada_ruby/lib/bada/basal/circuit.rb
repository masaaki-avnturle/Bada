# frozen_string_literal: true

require_relative "nucleus"
require_relative "thermal"
require_relative "dopamine"

module Bada
  module Basal
    # BasalGanglia — Mediator + Composite. It owns the nuclei (colleagues) and
    # coordinates the direct (Go), indirect (NoGo) and hyperdirect pathways,
    # producing per-channel saliences and a selected action via thermal gating.
    #
    # Pathways:
    #   cortex --(diffuse heat)--> D1, D2, STN
    #   D1 --| GPi            (direct / Go: lowers GPi -> disinhibits thalamus)
    #   D2 --| GPe --| GPi    (indirect / NoGo: raises GPi)
    #   STN --> GPi           (hyperdirect: broad NoGo)
    #   GPi --| thalamus      (selective disinhibition -> action selection)
    class BasalGanglia
      attr_reader :n, :dopamine, :thermal, :last

      def initialize(n, thermal:, dopamine:)
        @n = n
        @cortex = Cortex.new
        @d1 = StriatumD1.new(n)
        @d2 = StriatumD2.new(n)
        @stn = STN.new
        @gpe = GPe.new
        @gpi = GPi.new
        @thalamus = Thalamus.new
        @thermal = thermal
        @dopamine = dopamine
        # Observer wiring: striatum listens to dopamine.
        @dopamine.subscribe(@d1).subscribe(@d2)
        @dopamine.tonic! # set initial DA level on the striatum
        @last = {}
      end

      # Composite view: the nuclei as a small signed network (the NN isomorphism).
      def nuclei = [@cortex, @d1, @d2, @stn, @gpe, @gpi, @thalamus]

      # Run the circuit on a salience vector; return diagnostics + selected index.
      def evaluate(salience)
        raise "expected #{@n} channels" unless salience.length == @n
        heat = @thermal.diffuse(salience)
        c = @cortex.activate(heat)
        d1 = @d1.activate(c)
        d2 = @d2.activate(c)
        stn = @stn.activate(c)
        gpe = @gpe.activate(d2, stn)
        gpi = @gpi.activate(d1, gpe, stn)
        thal = @thalamus.activate(gpi)
        @last = { cortex: c, d1: d1, d2: d2, stn: stn, gpe: gpe, gpi: gpi, thalamus: thal }
        @last
      end

      def select(salience)
        thal = evaluate(salience)[:thalamus]
        idx = @thermal.gate(thal)
        @trace = @last[:d1] # eligibility trace for learning
        @last[:selected] = idx
        idx
      end

      def distribution(salience)
        @thermal.distribution(evaluate(salience)[:thalamus])
      end

      # Deliver reward for the last selection; dopamine broadcasts the RPE and
      # the striatum learns (Observer + plasticity).
      def reward(r)
        @dopamine.reward(r, trace: @trace)
      end
    end
  end
end
