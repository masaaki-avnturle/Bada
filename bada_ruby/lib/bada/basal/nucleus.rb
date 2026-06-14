# frozen_string_literal: true

module Bada
  module Basal
    # Nucleus — the small-class unit of the in-body neural system. Each nucleus
    # is isomorphic to a layer of neurons: it maps an input activation vector to
    # an output activation vector (weighted sum + rectifier). Nuclei are "dumb"
    # colleagues; the BasalGanglia mediator wires them together (Mediator
    # pattern), and activation functions are interchangeable (Strategy).
    class Nucleus
      attr_reader :name, :sign

      def initialize(name, sign)
        @name = name      # symbol
        @sign = sign      # +1 excitatory, -1 inhibitory (its projection sign)
      end

      def relu(x) = x.positive? ? x : 0.0
      def vrelu(v) = v.map { |x| relu(x) }

      # Subclasses override. Returns an activation vector (or scalar for STN).
      def activate(*) = raise(NotImplementedError)
    end

    # Cortex: source of channel saliences (the candidate actions / token logits).
    class Cortex < Nucleus
      def initialize = super(:cortex, +1)
      def activate(salience) = salience.dup
    end

    # Striatum D1 (direct / "Go"): excited by cortex, *facilitated* by dopamine.
    # Observer of the dopamine subject (its @da is updated on notify).
    class StriatumD1 < Nucleus
      attr_reader :weights, :da

      def initialize(n)
        super(:striatum_d1, +1)
        @weights = Array.new(n, 1.0)
        @da = 0.0
      end

      def activate(cortex)
        cortex.each_index.map { |i| relu((1.0 + @da) * @weights[i] * cortex[i]) }
      end

      # Observer hook + plasticity: reward strengthens the Go weight that was active.
      def on_dopamine(da, rpe, trace)
        @da = da
        trace.each_index { |i| @weights[i] += 0.1 * rpe * trace[i] } if rpe && trace
      end
    end

    # Striatum D2 (indirect / "NoGo"): excited by cortex, *suppressed* by dopamine.
    class StriatumD2 < Nucleus
      attr_reader :weights, :da

      def initialize(n)
        super(:striatum_d2, -1)
        @weights = Array.new(n, 1.0)
        @da = 0.0
      end

      def activate(cortex)
        cortex.each_index.map { |i| relu((1.0 - @da) * @weights[i] * cortex[i]) }
      end

      def on_dopamine(da, rpe, trace)
        @da = da
        # NoGo learns the opposite sign (avoidance learning)
        trace.each_index { |i| @weights[i] += 0.1 * (-rpe) * trace[i] } if rpe && trace
      end
    end

    # Subthalamic nucleus (hyperdirect): diffuse global excitation = a broad
    # "hold your horses" NoGo proportional to overall cortical drive.
    class STN < Nucleus
      def initialize = super(:stn, +1)
      def activate(cortex)
        return 0.0 if cortex.empty?
        relu(cortex.sum / cortex.length.to_f)
      end
    end

    # External globus pallidus: inhibited by D2, excited by STN.
    class GPe < Nucleus
      def initialize(base: 1.0, a_stn: 0.5) = (super(:gpe, -1); @base = base; @a = a_stn)
      def activate(d2, stn)
        d2.each_index.map { |i| relu(@base + @a * stn - d2[i]) }
      end
    end

    # Internal globus pallidus (OUTPUT): tonically active (inhibits thalamus).
    # Lowered by the direct pathway (D1) and by GPe; raised by STN.
    class GPi < Nucleus
      def initialize(base: 1.0, b_stn: 0.5, c_gpe: 0.5)
        super(:gpi, -1)
        @base = base; @b = b_stn; @c = c_gpe
      end

      def activate(d1, gpe, stn)
        d1.each_index.map { |i| relu(@base + @b * stn - d1[i] - @c * gpe[i]) }
      end
    end

    # Thalamus (gate): inhibited by GPi. Low GPi on a channel disinhibits the
    # thalamus there -> that action is selected. This is selective disinhibition.
    class Thalamus < Nucleus
      def initialize(drive: 1.0) = (super(:thalamus, +1); @drive = drive)
      def activate(gpi) = gpi.map { |g| relu(@drive - g) }
    end
  end
end
