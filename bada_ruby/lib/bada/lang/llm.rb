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
    # returns nil so callers gracefully fall back to the local engine. Network
    # and parse failures are caught and also yield nil — the language never
    # breaks just because a remote call did.
    #
    # Configuration (all via environment, never stored in the repo):
    #   ANTHROPIC_API_KEY     -> use the Anthropic Messages API
    #   OPENAI_API_KEY        -> use an OpenAI-compatible /chat/completions API
    #   BADA_LLM_MODEL        -> override the model id
    #   BADA_LLM_MAX_TOKENS   -> override max output tokens (default 1024)
    #   OPENAI_BASE_URL       -> override the OpenAI-compatible base URL
    module LLM
      module_function

      DEFAULT_MAX_TOKENS = 1024
      ANTHROPIC_VERSION = "2023-06-01"
      ANTHROPIC_DEFAULT_MODEL = "claude-opus-4-8"
      OPENAI_DEFAULT_MODEL = "gpt-4o-mini"
      OPEN_TIMEOUT = 10
      READ_TIMEOUT = 60

      # Is a real-LLM backend configured? (cheap; no network)
      def available?
        !backend.nil?
      end

      # Which backend would be used: :anthropic, :openai, or nil.
      def backend
        return :anthropic if env_present?("ANTHROPIC_API_KEY")
        return :openai if env_present?("OPENAI_API_KEY")
        nil
      end

      def model
        ENV.fetch("BADA_LLM_MODEL") do
          backend == :openai ? OPENAI_DEFAULT_MODEL : ANTHROPIC_DEFAULT_MODEL
        end
      end

      def max_tokens
        Integer(ENV.fetch("BADA_LLM_MAX_TOKENS", DEFAULT_MAX_TOKENS))
      rescue ArgumentError, TypeError
        DEFAULT_MAX_TOKENS
      end

      # Ask the real LLM. Returns the answer String, or nil if no backend is
      # configured or the call/parse failed (so callers can fall back locally).
      def ask(prompt, system: nil)
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
