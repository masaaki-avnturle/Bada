# frozen_string_literal: true

require_relative "drawing"
require_relative "jones"
require_relative "telomere"
require_relative "thermal"
require_relative "iq"

module OmegaIQ
  # End-to-end orchestration:
  #   絵 → 方程式 → Jones多項式 → テロメア分裂 → 赤外線/温度 → IQ (+ 真逆)
  class Pipeline
    def initialize(diagram_path:, thermal_path: nil)
      @diagram_path = diagram_path
      @thermal_path = thermal_path
    end

    def run
      drawing = Drawing.load(@diagram_path).analyse
      thermal = Thermal.read(@thermal_path)
      crossings = drawing.crossings
      jones = Jones.polynomial(crossings)
      telomere = Telomere.new(crossings).divide
      measure = IQ.new(crossings, t_eval: thermal.t_eval, coherence: thermal.coherence).measure

      {
        drawing: drawing,
        thermal: thermal,
        crossings: crossings,
        jones: jones,
        mirror_jones: Jones.polynomial(Jones.mirror(crossings)),
        telomere: telomere,
        measure: measure
      }
    end

    # Human-readable report (Japanese + English), used by bin/run_iq and the APK.
    def self.render(r)
      d = r[:drawing]; t = r[:thermal]; tel = r[:telomere]; m = r[:measure]
      out = []
      out << "==== Bada 赤外線IQ・テロメア分裂測定 ===="
      out << ""
      out << "[1] 絵の方程式化  drawing -> equations  (#{d.segments.length} lines, red-arrow order #{d.arrow_order.inspect})"
      d.equations.first(6).each { |e| out << "    #{e}" }
      out << "    ... (#{d.equations.length} equations)" if d.equations.length > 6
      out << ""
      out << "[2] Jones多項式   from #{r[:crossings].length} crossings, writhe #{Jones.writhe(r[:crossings])}"
      out << "    V(t)      = #{r[:jones].to_s('t', 4)}"
      out << "    真逆 V(1/t) = #{r[:mirror_jones].to_s('t', 4)}"
      out << ""
      out << "[3] テロメア分裂  Hayflick limit = #{tel.hayflick_limit} divisions"
      tel.generations.each do |g|
        tag = g[:senescent] ? "  <- senescence (unknot)" : ""
        out << "    gen #{g[:generation]}: length=#{g[:telomere_length]} daughters=#{g[:daughters]}#{tag}"
      end
      out << "    split entropy = #{format('%.4f', tel.entropy)} bits"
      out << ""
      out << "[4] 赤外線カメラ + 温度計  IR frame #{t.width}x#{t.height}"
      out << format("    mean temp = %.2f degC   coherence = %.4f   t_eval = %.6f",
                    t.mean_c, t.coherence, t.t_eval)
      out << ""
      out << "[5] IQ測定"
      m[:forward][:components].each { |k, v| out << format("    %-11s = %.4f", k, v) }
      out << format("    raw          = %.4f", m[:forward][:raw])
      out << ""
      out << format("    IQ (順)   = %6.1f   [%s]", m[:iq], m[:band])
      out << format("    IQ (真逆) = %6.1f", m[:mirror_iq])
      out << format("    真逆 divergence = %.1f   chiral balance = %.1f", m[:divergence], m[:chiral_balance])
      out.join("\n")
    end
  end
end
