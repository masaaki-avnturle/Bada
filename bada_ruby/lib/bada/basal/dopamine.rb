# frozen_string_literal: true

module Bada
  module Basal
    # SNc / dopamine system as an Observer *subject*. It holds the tonic
    # dopamine level and broadcasts reward-prediction-error (RPE) to its
    # observers (the striatal nuclei), which adjust their plasticity. This is
    # the learning signal of the in-body neural system.
    class Dopamine
      attr_reader :level, :baseline

      def initialize(baseline: 0.3, lr: 0.2)
        @baseline = baseline
        @level = baseline
        @lr = lr
        @observers = []
        @value = 0.0 # running value estimate (for RPE)
      end

      def subscribe(observer)
        @observers << observer unless @observers.include?(observer)
        self
      end

      # Reward-prediction error and broadcast. `trace` = the activation vector
      # that was active when the action was taken (eligibility trace).
      def reward(r, trace: nil)
        rpe = r - @value
        @value += @lr * rpe
        # phasic dopamine: rises with positive RPE, dips with negative
        @level = (@baseline + rpe).clamp(0.0, 1.0)
        notify(rpe, trace)
        rpe
      end

      # Tonic update with no learning (just propagate current level).
      def tonic!
        notify(nil, nil)
      end

      private

      def notify(rpe, trace)
        @observers.each { |o| o.on_dopamine(@level, rpe, trace) }
      end
    end
  end
end
