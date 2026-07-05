# frozen_string_literal: true

require_relative "pipeline"

module OmegaIQ
  # A small Bada-language runtime for the IQ app. It keeps the three core Bada
  # operators from the repo README (<-, -<, >-, Omega::push) and adds the app
  # verbs the IQ measurement needs. A `.bada` program is executed line by line.
  #
  #   set diagram = "assets/diagram_arrows.txt"
  #   set thermal = "assets/thermal_frame.pgm"
  #   load  drawing from diagram        # 絵 -> 方程式
  #   jones                             # Jones多項式
  #   split telomere                    # テロメア分裂
  #   sense thermal from thermal        # 赤外線カメラ + 温度計
  #   measure iq                        # IQ測定 (順 + 真逆)
  #   mirror                            # 真逆の性質を反転表示
  #   report
  #
  # Comments start with '#'. Strings use double quotes.
  class BadaRuntime
    attr_reader :env, :out, :state

    def initialize(base_dir: Dir.pwd)
      @env = {}
      @out = []
      @state = {}
      @base = base_dir
    end

    def run(source)
      source.each_line do |raw|
        line = raw.strip.sub(/#.*\z/, "").strip
        next if line.empty?

        exec_line(line)
      end
      @out
    end

    private

    def exec_line(line)
      case line
      when /\Aset\s+(\w+)\s*=\s*(.+)\z/
        @env[$1] = literal($2)
      when /\Aload\s+drawing\s+from\s+(\w+)\z/
        path = resolve(@env.fetch($1))
        @state[:drawing] = Drawing.load(path).analyse
        emit "Ω::load drawing (#{@state[:drawing].segments.length} lines, arrow #{@state[:drawing].arrow_order.inspect})"
      when /\Ajones\z/
        cr = crossings
        @state[:jones] = Jones.polynomial(cr)
        emit "Ω::jones V(t) = #{@state[:jones].to_s('t', 4)}"
      when /\Asplit\s+telomere\z/
        @state[:telomere] = Telomere.new(crossings).divide
        emit "Ω::telomere Hayflick=#{@state[:telomere].hayflick_limit} entropy=#{format('%.4f', @state[:telomere].entropy)}"
      when /\Asense\s+thermal\s+from\s+(\w+)\z/
        path = @env[$1] ? resolve(@env[$1]) : nil
        @state[:thermal] = Thermal.read(path)
        emit format("Ω::thermal mean=%.2fC coherence=%.4f t_eval=%.6f",
                    @state[:thermal].mean_c, @state[:thermal].coherence, @state[:thermal].t_eval)
      when /\Ameasure\s+iq\z/
        th = @state.fetch(:thermal)
        @state[:measure] = IQ.new(crossings, t_eval: th.t_eval, coherence: th.coherence).measure
        emit format("Ω::iq 順=%.1f 真逆=%.1f divergence=%.1f",
                    @state[:measure][:iq], @state[:measure][:mirror_iq], @state[:measure][:divergence])
      when /\Amirror\z/ # 真逆の性質
        @state[:mirror_jones] = Jones.polynomial(Jones.mirror(crossings))
        emit "Ω::mirror 真逆 V(1/t) = #{@state[:mirror_jones].to_s('t', 4)}"
      when /\Areport\z/
        r = full_report
        emit Pipeline.render(r)
      # --- core Bada operators (kept from the language spec) ---
      when /\A(\w+)\s*<-\s*(.+)\z/, /\A(\w+)\s*-<\s*(.+)\z/, /\A(\w+)\s*>-\s*(.+)\z/
        emit "Ω::op #{line}"
      when /\A(?:Omega|Ω)::push\s+(\w+)/
        emit "Ω::push #{$1}"
      else
        raise "Bada syntax error: #{line.inspect}"
      end
    end

    def crossings
      @state.fetch(:drawing).crossings
    end

    def full_report
      cr = crossings
      {
        drawing: @state[:drawing],
        thermal: @state.fetch(:thermal),
        crossings: cr,
        jones: @state[:jones] || Jones.polynomial(cr),
        mirror_jones: @state[:mirror_jones] || Jones.polynomial(Jones.mirror(cr)),
        telomere: @state[:telomere] || Telomere.new(cr).divide,
        measure: @state.fetch(:measure)
      }
    end

    def literal(src)
      s = src.strip
      s =~ /\A"(.*)"\z/ ? $1 : s
    end

    def resolve(path)
      File.expand_path(path, @base)
    end

    def emit(msg)
      @out << msg
    end
  end
end
