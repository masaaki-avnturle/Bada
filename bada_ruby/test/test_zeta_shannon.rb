# encoding: UTF-8
# frozen_string_literal: true

require "minitest/autorun"
require "stringio"
require_relative "../lib/bada"

# The ladder's `local` rung: the Bada-written Zeta-Shannon engine answers first
# and OmegaChat takes over when it abstains. No network and no API key is used.
# The engine runs under node; without node the engine tests are skipped and the
# fallback tests still run.
class TestZetaShannon < Minitest::Test
  ZS = Bada::ZetaShannon
  KEYS = %w[ANTHROPIC_API_KEY OPENAI_API_KEY BADA_LOCAL_ENGINE BADA_NODE BADA_ZETA_HOME BADA_LLM_MODEL].freeze

  def setup
    @saved = KEYS.to_h { |k| [k, ENV.delete(k)] }
    Bada::Lang::LLM.reset!
    ZS.stop!
  end

  def teardown
    ZS.stop!
    @saved.each { |k, v| v.nil? ? ENV.delete(k) : (ENV[k] = v) }
    Bada::Lang::LLM.reset!
  end

  def need_engine
    skip "node or the Zeta-Shannon engine is not installed" unless ZS.available?
  end

  def out(src) = Bada::Lang.run(src, out: StringIO.new).output

  def test_mode_defaults_to_auto_and_rejects_unknown_values
    assert_equal "auto", ZS.mode
    ENV["BADA_LOCAL_ENGINE"] = "ZETA"
    assert_equal "zeta", ZS.mode
    ENV["BADA_LOCAL_ENGINE"] = "nonsense"
    assert_equal "auto", ZS.mode
  end

  def test_grounded_answer_comes_from_the_ledger
    need_engine
    r = ZS.ask("リーマン予想は証明されましたか")
    refute r[:abstained]
    assert_equal "未解決", r[:status]
    assert_includes r[:text], "リーマン予想は未解決である"
    assert_operator r[:confidence], :>, 0.5
  end

  def test_abstains_without_evidence
    need_engine
    r = ZS.ask("明日の東京の天気を教えて")
    assert r[:abstained]
    assert_equal "無知", r[:status]
    assert_nil ZS.answer("明日の東京の天気を教えて") # auto: hand on to OmegaChat
  end

  def test_learned_fact_persists_across_questions
    need_engine
    before = ZS.ask("青い鯨はどこに登場しますか")
    assert before[:abstained]
    assert_kind_of Integer, ZS.learn("テスト用の事実として、青い鯨は第九十九巻に登場する。")
    after = ZS.ask("青い鯨はどこに登場しますか")
    assert_equal "学習", after[:status]
    assert_includes after[:text], "第九十九巻"
  end

  def test_chat_llm_uses_the_bada_engine_on_the_local_rung
    need_engine
    res = out(%(print Chat.llm("リーマン予想は証明されましたか")\nprint Chat.local_engine()))
    assert_includes res[0], "リーマン予想は未解決である"
    assert_includes res[0], "[zeta-shannon | 標識 未解決"
    assert_equal "zeta-shannon", res[1]
  end

  def test_pinned_local_version_uses_the_bada_engine_even_with_a_key
    need_engine
    ENV["ANTHROPIC_API_KEY"] = "sk-test-not-used"
    res = out(%(Chat.use("local")\nprint Chat.llm("零の保存とは何ですか")))
    assert_includes res.last, "零の保存とは"
    assert_includes res.last, "zeta-shannon"
  end

  def test_abstention_falls_through_to_omegachat_in_auto_mode
    res = out(%(print Chat.llm("意識とは何か")))
    assert_match(/Ξ=/, res.first)
  end

  def test_zeta_mode_returns_the_abstention_itself
    need_engine
    ENV["BADA_LOCAL_ENGINE"] = "zeta"
    res = out(%(print Chat.local("明日の東京の天気を教えて")))
    assert_includes res.first, "わかりません"
    assert_includes res.first, "棄権"
  end

  def test_omega_mode_skips_the_bada_engine
    ENV["BADA_LOCAL_ENGINE"] = "omega"
    refute ZS.available?
    res = out(%(print Chat.llm("リーマン予想は証明されましたか")\nprint Chat.local_engine()))
    assert_match(/Ξ=/, res[0])
    assert_equal "omega", res[1]
  end

  def test_missing_node_falls_back_without_raising
    ENV["BADA_NODE"] = "/nonexistent/node"
    refute ZS.available?
    assert_nil ZS.ask("リーマン予想は証明されましたか")
    res = out(%(print Chat.llm("リーマン予想は証明されましたか")\nprint str(Chat.teach("x"))))
    assert_match(/Ξ=/, res[0])
    assert_equal "0", res[1]
  end

  def test_missing_engine_directory_falls_back
    ENV["BADA_ZETA_HOME"] = "/nonexistent/dir"
    refute ZS.available?
    assert_match(/Ξ=/, out(%(print Chat.llm("零の保存とは何ですか"))).first)
  end
end
