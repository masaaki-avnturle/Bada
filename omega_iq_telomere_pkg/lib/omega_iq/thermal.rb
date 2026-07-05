# frozen_string_literal: true

module OmegaIQ
  # タブレットの赤外線カメラ + 温度計 — the tablet's infrared camera and thermometer.
  #
  # On a real BadaOS tablet the frame comes from the IR sensor and the scalar
  # temperature from the on-board thermometer. Off-device we read a thermal frame
  # asset in plain-text PGM (P2) form; if it is missing we synthesise one
  # deterministically. Either way we expose the same three numbers the IQ engine
  # needs:
  #
  #   mean_c     : mean temperature over the frame (thermometer reading, degC)
  #   coherence  : 1 - normalised spatial variance in [0,1] (thermal order)
  #   t_eval     : Boltzmann evaluation point for the Jones polynomial,
  #                t_eval = exp(-THETA / T_kelvin), so a hotter, more coherent
  #                telomere is probed at a t closer to 1.
  class Thermal
    THETA = 300.0 # reference activation scale (kelvin)

    attr_reader :width, :height, :pixels, :mean_c, :coherence, :t_eval

    def initialize(pixels, width, height)
      @pixels = pixels
      @width = width
      @height = height
      compute!
    end

    # Prefer the tablet sensor node if present (BadaOS exposes it as a P2 stream),
    # else the asset, else a deterministic synthetic frame.
    def self.read(asset_path, sensor_node: "/dev/badaos/ir0")
      if File.exist?(sensor_node)
        parse_pgm(File.read(sensor_node, encoding: "UTF-8"))
      elsif asset_path && File.exist?(asset_path)
        parse_pgm(File.read(asset_path, encoding: "UTF-8"))
      else
        synth
      end
    end

    def self.parse_pgm(text)
      # PGM comments run from '#' to end-of-line; strip them per line first.
      clean = text.each_line.map { |l| l.sub(/#.*$/, "") }.join(" ")
      toks = clean.split(/\s+/).reject(&:empty?)
      raise "not a P2 PGM" unless toks.shift == "P2"

      w = toks.shift.to_i
      h = toks.shift.to_i
      _max = toks.shift.to_i
      vals = toks.first(w * h).map(&:to_i)
      new(vals, w, h)
    end

    # Deterministic synthetic thermal field (a warm central telomere region).
    def self.synth(w = 8, h = 8)
      cx = (w - 1) / 2.0
      cy = (h - 1) / 2.0
      vals = []
      h.times do |y|
        w.times do |x|
          r2 = ((x - cx)**2 + (y - cy)**2) / (w * h / 4.0)
          vals << (120 + (100 * Math.exp(-r2))).round
        end
      end
      new(vals, w, h)
    end

    private

    def compute!
      n = @pixels.length.to_f
      # map 8-bit grey [0,255] to a physiological band ~ 20..45 degC
      temps = @pixels.map { |p| 20.0 + (p / 255.0) * 25.0 }
      @mean_c = temps.sum / n
      mu = @mean_c
      var = temps.sum { |t| (t - mu)**2 } / n
      # normalise variance by the band's max possible variance (~ (25/2)^2)
      @coherence = [1.0 - var / (12.5**2), 0.0].max
      t_kelvin = @mean_c + 273.15
      @t_eval = Math.exp(-THETA / t_kelvin)
    end
  end
end
