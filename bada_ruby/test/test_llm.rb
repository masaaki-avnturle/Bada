# encoding: UTF-8
# frozen_string_literal: true

require "minitest/autorun"
require "stringio"
require_relative "../lib/bada"

# These tests exercise the *graceful-fallback* path of the real-LLM bridge.
# We never make a network call here: with no API key in the environment,
# LLM.ask returns nil and Chat.llm must fall back to the local OmegaChat 分派.
class TestLLM < Minitest::Test
  LLM = Bada::Lang::LLM

  def without_keys
    saved = {}
    %w[ANTHROPIC_API_KEY OPENAI_API_KEY].each { |k| saved[k] = ENV.delete(k) }
    yield
  ensure
    saved.each { |k, v| ENV[k] = v unless v.nil? }
  end

  def with_env(pairs)
    saved = {}
    pairs.each { |k, v| saved[k] = ENV[k]; ENV[k] = v }
    yield
  ensure
    saved.each { |k, v| v.nil? ? ENV.delete(k) : (ENV[k] = v) }
  end

  def out(src) = Bada::Lang.run(src, out: StringIO.new).output

  def test_not_available_without_keys
    without_keys do
      refute LLM.available?
      assert_nil LLM.backend
      assert_nil LLM.ask("hello")
    end
  end

  def test_backend_selection_prefers_anthropic
    with_env("ANTHROPIC_API_KEY" => "sk-test", "OPENAI_API_KEY" => "sk-openai") do
      assert_equal :anthropic, LLM.backend
      assert LLM.available?
      assert_equal "claude-opus-4-8", LLM.model
    end
  end

  def test_backend_selection_openai_when_only_openai
    without_keys do
      with_env("OPENAI_API_KEY" => "sk-openai") do
        assert_equal :openai, LLM.backend
        assert_equal "gpt-4o-mini", LLM.model
      end
    end
  end

  def test_model_override
    with_env("ANTHROPIC_API_KEY" => "x", "BADA_LLM_MODEL" => "claude-sonnet-4-6") do
      assert_equal "claude-sonnet-4-6", LLM.model
    end
  end

  def test_blank_key_is_not_available
    without_keys do
      with_env("ANTHROPIC_API_KEY" => "   ") do
        # a present-but-blank key must be treated as "not configured"
        refute LLM.available?
        assert_nil LLM.backend
      end
    end
  end

  def test_max_tokens_default_and_override
    assert_equal 1024, LLM.max_tokens
    with_env("BADA_LLM_MAX_TOKENS" => "256") do
      assert_equal 256, LLM.max_tokens
    end
    with_env("BADA_LLM_MAX_TOKENS" => "garbage") do
      assert_equal 1024, LLM.max_tokens
    end
  end

  def test_chat_llm_falls_back_to_local_engine
    without_keys do
      res = out(%(print Chat.llm("意識とは何か")))
      refute_empty res
      assert_match(/Ξ=/, res.first) # local 分派 output carries the invariant tag
    end
  end

  def test_chat_backend_reports_local_without_keys
    without_keys do
      assert_equal ["local"], out(%(print Chat.backend()))
      assert_equal ["false"], out(%(print str(Chat.live())))
    end
  end

  def test_multigpt_chat_uses_fallback
    without_keys do
      src = <<~BADA
        import "std/multigpt.bada"
        arr r <- MultiGPT.respond("意識とは何か")
        print at(r, 0)
        print str(len(at(r, 1)) > 0)
        print MultiGPT.engine()
      BADA
      res = out(src)
      assert_equal "chat", res[0]
      assert_equal "true", res[1]
      assert_equal "local", res[2]
    end
  end
end
