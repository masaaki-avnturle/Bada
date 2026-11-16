# frozen_string_literal: true

require "json"

module Bada
  # ZetaShannon — the Bada-written Zeta-Shannon language engine, wired in as the
  # first engine of the version ladder's `local` rung.
  #
  # The engine itself is pure Bada (../bada_zeta_shannon/zeta_shannon.bada) and
  # runs on the quantum-Bada interpreter, which is JavaScript. This module keeps
  # one long-lived `node bridge.js` child and talks JSON Lines to it, so facts
  # taught with `learn` and the conversation belief persist across questions.
  #
  # The engine answers only from its ledger. When it has no evidence it
  # *abstains*; what happens then is chosen by BADA_LOCAL_ENGINE:
  #
  #   auto  (default)  grounded answer when the ledger has evidence,
  #                    otherwise hand the question on to OmegaChat
  #   zeta             Zeta-Shannon only: an abstention is returned as the answer
  #   omega            skip this engine; the local rung is OmegaChat, as before
  #
  # Nothing here raises: if node or the engine files are missing, or the child
  # dies or times out, every call returns nil and the caller falls back.
  #
  # Configuration (environment):
  #   BADA_LOCAL_ENGINE   auto | zeta | omega
  #   BADA_ZETA_HOME      directory holding bridge.js (default: ../bada_zeta_shannon)
  #   BADA_NODE           node executable (default: "node")
  module ZetaShannon
    module_function

    ENGINE = "zeta-shannon"
    MODES = %w[auto zeta omega].freeze
    START_TIMEOUT = 20
    CALL_TIMEOUT = 20
    LOCK = Mutex.new

    def mode
      m = ENV.fetch("BADA_LOCAL_ENGINE", "auto").to_s.strip.downcase
      MODES.include?(m) ? m : "auto"
    end

    def enabled?
      mode != "omega"
    end

    def home
      ENV["BADA_ZETA_HOME"] || File.expand_path("../../../bada_zeta_shannon", __dir__)
    end

    def bridge_path
      File.join(home, "bridge.js")
    end

    def node
      ENV["BADA_NODE"] || "node"
    end

    # Is the engine installed and startable? Starts the child on first use.
    def available?
      return false unless enabled?
      LOCK.synchronize { !ensure_started.nil? }
    end

    # Which engine answers first on the local rung: "zeta-shannon" or "omega".
    def engine
      available? ? ENGINE : "omega"
    end

    # Raw reply Hash (symbol keys: :status :topic :confidence :entropy_bits
    # :grover :abstained :text), or nil when the engine is unavailable.
    def ask(question)
      res = request("op" => "ask", "text" => question.to_s)
      res && res[:ok] ? res : nil
    end

    # Append a fact to the engine's ledger. Returns the new fact count, or nil.
    def learn(text)
      res = request("op" => "learn", "text" => text.to_s)
      res && res[:ok] ? res[:facts] : nil
    end

    # The one-line answer for the local rung, or nil when the caller should
    # fall through to OmegaChat (engine off / unavailable / abstained in auto).
    def answer(question)
      r = ask(question)
      return nil unless r
      if r[:abstained]
        return mode == "zeta" ? "#{r[:text]} [#{ENGINE}: 棄権]" : nil
      end
      "#{r[:text]} [#{ENGINE} | 標識 #{r[:status]} | 出典 #{r[:topic]} | 確信度 #{format('%.2f', r[:confidence])}]"
    end

    # Stop the child (state is lost; the next call starts a fresh engine).
    def stop!
      LOCK.synchronize { shutdown }
    end

    # --- child process ------------------------------------------------------

    def request(payload)
      return nil unless enabled?
      LOCK.synchronize do
        io = ensure_started
        next nil unless io
        begin
          io.puts(JSON.generate(payload))
          io.flush
          line = read_line(io, CALL_TIMEOUT)
          line ? JSON.parse(line, symbolize_names: true) : fail_child
        rescue StandardError
          fail_child
        end
      end
    end
    private_class_method :request

    def ensure_started
      return @io if @io
      return nil if @failed_for == [node, bridge_path]
      unless File.file?(bridge_path)
        @failed_for = [node, bridge_path]
        return nil
      end
      io = IO.popen([node, bridge_path], "r+", err: File::NULL)
      io.set_encoding("UTF-8")
      ready = read_line(io, START_TIMEOUT)
      if ready && JSON.parse(ready)["ready"]
        at_exit { stop! } unless @exit_hook
        @exit_hook = true
        @io = io
      else
        @io = io
        fail_child
      end
    rescue StandardError
      @failed_for = [node, bridge_path]
      @io = nil
    end
    private_class_method :ensure_started

    def read_line(io, timeout)
      return nil unless IO.select([io], nil, nil, timeout)
      line = io.gets
      line && !line.strip.empty? ? line : nil
    end
    private_class_method :read_line

    # The child misbehaved: kill it and do not retry with the same settings.
    def fail_child
      @failed_for = [node, bridge_path]
      shutdown
      nil
    end
    private_class_method :fail_child

    def shutdown
      io = @io
      @io = nil
      return unless io
      pid = io.pid
      begin
        io.close_write
      rescue StandardError
        nil
      end
      begin
        Process.kill("TERM", pid)
      rescue StandardError
        nil
      end
      begin
        io.close
      rescue StandardError
        nil
      end
    end
    private_class_method :shutdown
  end
end
