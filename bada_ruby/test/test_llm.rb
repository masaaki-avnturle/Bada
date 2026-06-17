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

  def setup
    # version selection is process-global; isolate each test
    ENV.delete("BADA_LLM_MODEL")
    LLM.reset!
  end

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
      LLM.reset! # BADA_LLM_MODEL sets the initial version selection
      assert_equal "claude-sonnet-4-6", LLM.model
      assert_equal "claude-sonnet-4-6", LLM.current_model
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

  # --- version ladder (downgrade / upgrade) ---------------------------

  def test_default_version_is_opus_48
    assert_equal "claude-opus-4-8", LLM.current_model
    assert_equal "Opus 4.8", LLM.version_label
  end

  def test_downgrade_walks_to_previous_versions
    assert_equal "claude-opus-4-7", LLM.downgrade[:id]
    assert_equal "claude-opus-4-6", LLM.downgrade[:id]
    assert_equal "claude-sonnet-4-6", LLM.downgrade[:id]
  end

  def test_downgrade_clamps_at_local
    LLM.downgrade(100)
    assert_equal "local", LLM.current_model
    # cannot go below local
    assert_equal "local", LLM.downgrade[:id]
  end

  def test_upgrade_clamps_at_top
    LLM.upgrade(100)
    assert_equal "claude-fable-5", LLM.current_model
  end

  def test_use_by_id_and_label
    assert_equal "claude-opus-4-6", LLM.use("claude-opus-4-6")[:id]
    assert_equal "claude-haiku-4-5", LLM.use("Haiku 4.5")[:id]
    assert_nil LLM.use("no-such-model")
  end

  def test_env_sets_initial_version
    with_env("BADA_LLM_MODEL" => "claude-opus-4-7") do
      LLM.reset!
      assert_equal "claude-opus-4-7", LLM.current_model
    end
  end

  def test_ask_returns_nil_when_downgraded_to_local_even_with_key
    with_env("ANTHROPIC_API_KEY" => "sk-test") do
      LLM.use("local")
      refute LLM.live?           # key present but pinned to local
      assert LLM.available?      # ...the key is still configured
      assert_nil LLM.ask("hi")   # so no network call is attempted
    end
  end

  def test_chat_version_controls_from_bada
    without_keys do
      assert_equal ["Opus 4.8"], out(%(print Chat.version()))
      assert_equal ["Opus 4.7"], out(%(print Chat.downgrade()))
      assert_equal ["Opus 4.8"], out(%(print Chat.upgrade()))
      assert_equal ["Sonnet 4.6"], out(%(print Chat.use("claude-sonnet-4-6")))
      assert_equal ["7"], out(%(print str(len(Chat.versions()))))
    end
  end

  def test_history_records_changes
    LLM.reset!
    LLM.downgrade
    LLM.downgrade
    assert_equal %w[claude-opus-4-8 claude-opus-4-7 claude-opus-4-6], LLM.history
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
