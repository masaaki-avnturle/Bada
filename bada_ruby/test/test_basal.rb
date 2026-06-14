# encoding: UTF-8
# frozen_string_literal: true

require "minitest/autorun"
require_relative "../lib/bada"

include Bada::Basal

class TestNuclei < Minitest::Test
  def test_signs
    assert_equal(+1, StriatumD1.new(3).sign)
    assert_equal(-1, StriatumD2.new(3).sign)
    assert_equal(-1, GPi.new.sign)
    assert_equal(+1, Thalamus.new.sign)
  end

  def test_d1_facilitated_by_dopamine
    d1 = StriatumD1.new(2)
    base = d1.activate([1.0, 1.0])
    d1.on_dopamine(0.5, nil, nil) # raise DA
    hi = d1.activate([1.0, 1.0])
    assert_operator hi[0], :>, base[0] # more dopamine -> more Go
  end

  def test_d2_suppressed_by_dopamine
    d2 = StriatumD2.new(2)
    base = d2.activate([1.0, 1.0])
    d2.on_dopamine(0.5, nil, nil)
    lo = d2.activate([1.0, 1.0])
    assert_operator lo[0], :<, base[0] # more dopamine -> less NoGo
  end

  def test_thalamus_disinhibition
    # low GPi -> high thalamus (selected); high GPi -> zero (suppressed)
    thal = Thalamus.new(drive: 1.0).activate([0.0, 2.0])
    assert_in_delta 1.0, thal[0], 1e-9
    assert_in_delta 0.0, thal[1], 1e-9
  end
end

class TestThermal < Minitest::Test
  def test_diffusion_reduces_variance
    tf = ThermalField.new(diffusion_gain: 0.5)
    v = [4.0, 0.0, 0.0, 0.0]
    d = tf.diffuse(v)
    assert_operator variance(d), :<, variance(v) # heat spreads
    assert_in_delta v.sum, d.sum, 1e-6           # diffusion conserves heat
  end

  def test_temperature_cools
    tf = ThermalField.new(t0: 2.0)
    t1 = tf.temperature
    5.times { tf.gate([1.0, 2.0, 3.0]) }
    assert_operator tf.temperature, :<, t1
  end

  def test_argmax_gate
    assert_equal 2, ArgmaxGate.new.select([0.1, 0.2, 0.9], nil)
  end

  def variance(v)
    m = v.sum / v.length
    v.sum { |x| (x - m)**2 } / v.length
  end
end

class TestDopamineObserver < Minitest::Test
  def test_reward_notifies_and_learns
    da = Dopamine.new(baseline: 0.3)
    d1 = StriatumD1.new(3)
    da.subscribe(d1)
    before = d1.weights[1]
    da.reward(1.0, trace: [0.0, 1.0, 0.0]) # reward channel 1
    assert_operator d1.weights[1], :>, before    # Go weight strengthened
    assert_operator da.level, :>, 0.3            # phasic dopamine rose
  end

  def test_negative_rpe_lowers_level
    da = Dopamine.new(baseline: 0.3)
    da.reward(-1.0)
    assert_operator da.level, :<, 0.3
  end
end

class TestCircuit < Minitest::Test
  def test_selects_highest_salience_channel
    bg = CircuitFactory.build(4, gate: :argmax, diffusion_gain: 0.0)
    assert_equal 1, bg.select([0.2, 0.9, 0.1, 0.3]) # disinhibition picks the strongest
  end

  def test_evaluate_shapes
    bg = CircuitFactory.build(3, gate: :argmax)
    r = bg.evaluate([1.0, 0.5, 0.2])
    assert_equal 3, r[:thalamus].length
    assert_equal 7, bg.nuclei.length # cortex, D1, D2, STN, GPe, GPi, thalamus
  end
end

class TestBodySystemAndSampler < Minitest::Test
  def test_body_system_selects_item
    sys = BodyNeuralSystem.new(channels: 3, gate: :argmax)
    chosen = sys.select([[:a, 0.1], [:b, 0.9], [:c, 0.2]])
    assert_equal :b, chosen
  end

  def test_sampler_favours_top_logit
    s = BasalGangliaSampler.new(k: 5, seed: 3)
    logits = [0.1, 5.0, 0.2, 0.3, 0.4, -1.0, 0.0]
    picks = Array.new(40) { s.pick(logits) }
    # the strongest logit (index 1) should be the modal choice
    assert_equal 1, picks.tally.max_by { |_, c| c }[0]
    assert(picks.all? { |i| i >= 0 && i < logits.length })
  end
end

class TestAprioriEngine < Minitest::Test
  def test_deliberate_orders_and_proves
    eng = AprioriEngine.new(seed: 1)
    r = eng.deliberate("未解決問題を想像して証明", count: 5)
    assert_equal 5, r[:order].length
    statuses = r[:order].map { |e| e[:proof].status }
    assert_includes statuses, :proved
    # open problems must NOT be marked proved (soundness)
    r[:order].each do |e|
      refute(e[:proof].proved?) if e[:conjecture].kind == :open
    end
  end

  def test_render_mentions_basal_ganglia
    s = AprioriEngine.new(seed: 2).render("ガンマ関数の未解決問題", count: 5)
    assert_match(/大脳基底核/, s)
    assert_match(/ドーパミン/, s)
  end

  def test_chat_deliberate_integration
    out = Bada::OmegaChat.new.deliberate("未解決問題を想像して", count: 5)
    assert_match(/体内神経システム/, out)
  end
end
