# encoding: utf-8
# frozen_string_literal: true

require "minitest/autorun"
require "bada/agi"

class TestAGI < Minitest::Test
  def test_chat_returns_reply_above_silent_talk
    r = Bada::AGI.chat("量子もつれとは何ですか", generations: 6, population: 10, nonce: 0)
    refute_empty r[:reply]
    assert_operator r[:precision], :>, Bada::AGI::BASELINE
    assert r[:exceeds_silent_talk]
    assert_equal 6, r[:trace].length
  end

  def test_self_evolution_is_monotonic
    r = Bada::AGI.chat("光 と 記憶 の 波", generations: 8, population: 12, nonce: 3)
    fits = r[:trace].map { |t| t[:best_fitness] }
    assert fits.each_cons(2).all? { |a, b| b >= a }, "best fitness must be non-decreasing (elitism)"
  end

  def test_deterministic_in_nonce
    a = Bada::AGI.chat("entangle bell measure", generations: 6, population: 10, nonce: 7)
    b = Bada::AGI.chat("entangle bell measure", generations: 6, population: 10, nonce: 7)
    assert_equal a[:reply], b[:reply]
    assert_equal a[:trace], b[:trace]
    # a different nonce evolves a different trajectory
    c = Bada::AGI.chat("entangle bell measure", generations: 6, population: 10, nonce: 8)
    refute_equal a[:trace], c[:trace]
  end

  def test_jones_polynomial_drives_fitness
    r = Bada::AGI.chat("quantum wave", generations: 5, population: 8, nonce: 1)
    j = r[:jones]
    assert_operator j[:crossings], :>=, 2
    assert_operator j[:crossings], :<=, Bada::AGI::MAX_CROSS
    assert_includes 0.0..1.0, j[:correlation]
    # winner braid word matches its crossing count
    assert_equal j[:crossings], r[:braid].split.length
  end

  def test_english_prompt_replies_in_english
    r = Bada::AGI.chat("what is quantum entanglement", generations: 6, population: 10, nonce: 1)
    assert_match(/[A-Za-z]/, r[:reply])
    assert_includes r[:reply], "self-evolution"
  end

  def test_render_shows_evolution_curve
    out = Bada::AGI.render("多様体 と ゲージ", generations: 6, population: 10, nonce: 2)
    assert_includes out, "自己進化"
    assert_includes out, "Jones"
    assert_includes out, "ChatΩ>"
    assert_includes out, "coherence precision"
  end
end
