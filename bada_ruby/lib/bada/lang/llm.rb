# frozen_string_literal: true

require "json"

module Bada
  module Lang
    # LLM — an optional bridge to a *real* large-language-model API (Anthropic
    # Messages API, or an OpenAI-compatible endpoint), using only the Ruby
    # standard library (Net::HTTP, JSON). No external gems.
    #
    # This is the honest answer to "is the Bada ChatGPT a real LLM?": by itself
    # the repo's `Chat` is the local `Bada::OmegaChat` engine. When an API key is
    # present in the environment, `LLM.ask` reaches a real model; otherwise it
    # returns nil so callers gracefully fall back to the local engine.
    #
    # The model used is chosen from a *version ladder* (most → least capable,
    # ending in the local 分派). You can DOWNGRADE to a previous version, upgrade
    # again, or pin a specific one — at runtime from Ruby, from Bada (`Chat.*`),
    # or via the CLI. Downgrading to the bottom rung ("local") forces the local
    # engine even when an API key is configured.
    #
    # Configuration (all via environment, never stored in the repo):
    #   ANTHROPIC_API_KEY     -> use the Anthropic Messages API
    #   OPENAI_API_KEY        -> use an OpenAI-compatible /chat/completions API
    #   BADA_LLM_MODEL        -> initial version selection (ladder id, see below)
    #   BADA_LLM_MAX_TOKENS   -> override max output tokens (default 1024)
    #   OPENAI_BASE_URL       -> override the OpenAI-compatible base URL
    module LLM
      module_function

      # Build / system codename for the Bada ChatGPT.
      CODENAME = "Bada XP"

      DEFAULT_MAX_TOKENS = 1024
      ANTHROPIC_VERSION = "2023-06-01"
      ANTHROPIC_DEFAULT_MODEL = "claude-opus-4-8"
      OPENAI_DEFAULT_MODEL = "gpt-4o-mini"
      OPEN_TIMEOUT = 10
      READ_TIMEOUT = 60
      LOCAL = "local"
      DEFAULT_VERSION_ID = "mythos"

      # The version ladder for the Bada XP "ChatGPT" line, ordered from most to
      # least capable. Each entry has a selection `id`, a display `label`, the
      # underlying API `model` id, and a note. The default is ムートス (Mythos),
      # which is equivalent to Opus 4.8 (same underlying model). The final rung
      # is the local OmegaChat 分派 (no key needed). Downgrade walks toward the
      # bottom; upgrade walks back up.
      LADDER = [
        { id: "claude-fable-5",    label: "Fable 5",        model: "claude-fable-5",    note: "最上位（最も高性能）" },
        { id: "mythos",            label: "ムートス",        model: "claude-opus-4-8",   note: "既定・Opus 4.8 と同等（Project Glasswing）" },
        { id: "claude-opus-4-7",   label: "Opus 4.7",       model: "claude-opus-4-7",   note: "前世代" },
        { id: "claude-opus-4-6",   label: "Opus 4.6",       model: "claude-opus-4-6",   note: "前々世代" },
        { id: "claude-sonnet-4-6", label: "Sonnet 4.6",     model: "claude-sonnet-4-6", note: "軽量・高速" },
        { id: "claude-haiku-4-5",  label: "Haiku 4.5",      model: "claude-haiku-4-5",  note: "最小・最速" },
        { id: LOCAL,               label: "OmegaChat 分派", model: nil,                 note: "ローカル（鍵不要）" }
      ].freeze

      def codename
        CODENAME
      end

      # --- version selection (mutable, in-process) -------------------------

      def ladder
        LADDER.map { |e| e[:id] }
      end

      # Index in LADDER that BADA_LLM_MODEL points at (by id or model), else the
      # default version (ムートス).
      def default_index
        want = ENV["BADA_LLM_MODEL"]
        (want && LADDER.index { |e| e[:id] == want || e[:model] == want }) ||
          LADDER.index { |e| e[:id] == DEFAULT_VERSION_ID }
      end

      # Lazily initialise selection + history together so the starting version
      # is always the first entry in the change history.
      def ensure_state!
        return if @selected_index
        @selected_index = default_index
        @history = [LADDER[@selected_index][:id]]
      end
      private_class_method :ensure_state!

      def selected_index
        ensure_state!
        @selected_index
      end

      def current
        LADDER[selected_index]
      end

      # The selection id of the current version, e.g. "mythos".
      def version_id
        current[:id]
      end

      # The underlying API model id of the current version (nil when local),
      # e.g. ムートス -> "claude-opus-4-8".
      def current_model
        current[:model]
      end

      # Human label, e.g. "ムートス".
      def version_label
        current[:label]
      end

      # Is the current version the local (no-API) rung?
      def local?
        current[:id] == LOCAL
      end

      # Move toward a *previous* (less capable) version. Clamped at "local".
      def downgrade(steps = 1)
        @selected_index = (selected_index + steps.to_i).clamp(0, LADDER.length - 1)
        record!
        current
      end

      # Move back toward a newer (more capable) version. Clamped at the top.
      def upgrade(steps = 1)
        @selected_index = (selected_index - steps.to_i).clamp(0, LADDER.length - 1)
        record!
        current
      end

      # Pin a specific version by ladder id, (case-insensitive) label, or
      # underlying model id. Returns the entry, or nil if unknown.
      def use(id_or_label)
        key = id_or_label.to_s
        i = LADDER.index { |e| e[:id] == key || e[:label].casecmp?(key) }
        i ||= LADDER.index { |e| e[:model] == key }
        return nil unless i
        @selected_index = i
        record!
        current
      end

      # Reset selection to the environment default and restart history.
      def reset!
        @selected_index = default_index
        @history = [version_id]
        current
      end

      def history
        ensure_state!
        @history.dup
      end

      def record!
        @history << version_id unless @history.last == version_id
      end
      private_class_method :record!

      # --- capability flags ------------------------------------------------

      # Is a real-LLM backend key configured? (cheap; no network)
      def available?
        !backend.nil?
      end

      # Will an `ask` actually reach a real model? (key configured AND not
      # downgraded to the local rung)
      def live?
        available? && !local?
      end

      # Which backend would be used: :anthropic, :openai, or nil.
      def backend
        return :anthropic if env_present?("ANTHROPIC_API_KEY")
        return :openai if env_present?("OPENAI_API_KEY")
        nil
      end

      # The concrete model id sent to the API for the active backend.
      def model
        if backend == :openai
          # The ladder is the Anthropic line; for OpenAI honour BADA_LLM_MODEL.
          ENV.fetch("BADA_LLM_MODEL", OPENAI_DEFAULT_MODEL)
        else
          current_model
        end
      end

      def max_tokens
        Integer(ENV.fetch("BADA_LLM_MAX_TOKENS", DEFAULT_MAX_TOKENS))
      rescue ArgumentError, TypeError
        DEFAULT_MAX_TOKENS
      end

      # --- the call --------------------------------------------------------

      # Ask the real LLM at the currently-selected version. Returns the answer
      # String, or nil if downgraded to local, no backend is configured, or the
      # call/parse failed (so callers can fall back to the local engine).
      def ask(prompt, system: nil)
        return nil if local?
        case backend
        when :anthropic then anthropic(prompt.to_s, system: system)
        when :openai then openai(prompt.to_s, system: system)
        end
      rescue StandardError
        nil
      end

      # --- Anthropic Messages API ------------------------------------------
      def anthropic(prompt, system: nil)
        body = {
          "model" => model,
          "max_tokens" => max_tokens,
          "messages" => [{ "role" => "user", "content" => prompt }]
        }
        body["system"] = system if system
        resp = post_json(
          "https://api.anthropic.com/v1/messages",
          body,
          "content-type" => "application/json",
          "x-api-key" => ENV["ANTHROPIC_API_KEY"].to_s,
          "anthropic-version" => ANTHROPIC_VERSION
        )
        return nil unless resp
        # A safety classifier may decline: stop_reason "refusal" has no usable text.
        return nil if resp["stop_reason"] == "refusal"
        parts = resp["content"]
        return nil unless parts.is_a?(Array)
        text = parts.select { |b| b.is_a?(Hash) && b["type"] == "text" }
                    .map { |b| b["text"] }.join
        text.empty? ? nil : text
      end

      # --- OpenAI-compatible Chat Completions ------------------------------
      def openai(prompt, system: nil)
        messages = []
        messages << { "role" => "system", "content" => system } if system
        messages << { "role" => "user", "content" => prompt }
        base = ENV.fetch("OPENAI_BASE_URL", "https://api.openai.com/v1")
        resp = post_json(
          "#{base}/chat/completions",
          { "model" => model, "max_tokens" => max_tokens, "messages" => messages },
          "content-type" => "application/json",
          "authorization" => "Bearer #{ENV['OPENAI_API_KEY']}"
        )
        return nil unless resp
        choice = resp.dig("choices", 0, "message", "content")
        choice && !choice.to_s.empty? ? choice.to_s : nil
      end

      # --- transport (pure stdlib) -----------------------------------------
      # Lazily require Net::HTTP so merely loading the language has no cost.
      def post_json(url, body, headers)
        require "net/http"
        require "uri"
        uri = URI(url)
        http = Net::HTTP.new(uri.host, uri.port)
        http.use_ssl = (uri.scheme == "https")
        http.open_timeout = OPEN_TIMEOUT
        http.read_timeout = READ_TIMEOUT
        req = Net::HTTP::Post.new(uri.request_uri)
        headers.each { |k, v| req[k] = v }
        req.body = JSON.generate(body)
        resp = http.request(req)
        return nil unless resp.is_a?(Net::HTTPSuccess)
        JSON.parse(resp.body)
      rescue StandardError
        nil
      end

      def env_present?(key)
        v = ENV[key]
        !v.nil? && !v.strip.empty?
      end
    end
  end
end
