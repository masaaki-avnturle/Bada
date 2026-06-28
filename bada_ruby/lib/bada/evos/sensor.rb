# frozen_string_literal: true

require_relative "../error_correction"

module Bada
  module EVOS
    # A noisy physical sensor whose readings are conditioned by the Bada
    # integrable-system error corrector.
    #
    # Real EV sensors (current shunts, cell-voltage taps, thermistors) are
    # noisy and occasionally throw spikes. Instead of an ad-hoc filter, the
    # raw window is stabilised by `Bada::ErrorCorrection.correct` — the
    # "spinning-top (koma) geometry of special relativity": each sample is
    # projected onto the complex rotational body, outliers are Lorentz-damped
    # along the closed orbit, and the rotation-conserved magnitude is read
    # back. The residual is the corrector's own error bound, which the
    # diagnostics subsystem uses to flag a failing sensor.
    class Sensor
      attr_reader :name, :unit, :raw, :value, :residual

      def initialize(name, unit: "", window: 8)
        @name = name
        @unit = unit
        @window = [window.to_i, 1].max
        @raw = []
        @value = 0.0
        @residual = 0.0
      end

      # Push a raw sample; returns the error-corrected reading.
      def feed(sample)
        @raw << sample.to_f
        @raw.shift while @raw.length > @window
        c = Bada::ErrorCorrection.correct(@raw)
        @value = c[:value]
        @residual = c[:residual]
        @value
      end

      # Is the corrector confident in the reading (low residual)?
      def healthy?(tol: 0.25)
        return true if @value.abs < 1e-9
        (@residual / (@value.abs + 1e-9)) <= tol
      end

      def to_s
        format("%s=%.3f%s", @name, @value, @unit)
      end
    end
  end
end
