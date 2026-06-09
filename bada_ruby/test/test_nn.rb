# frozen_string_literal: true

require "minitest/autorun"
require "stringio"
require_relative "../lib/bada"

include Bada::NN

class TestLinalg < Minitest::Test
  def test_matvec
    w = [[1.0, 2.0], [3.0, 4.0]]
    assert_equal [5.0, 11.0], Linalg.matvec(w, [1.0, 2.0])
  end

  def test_matvec_t
    w = [[1.0, 2.0], [3.0, 4.0]] # 2x2
    # W^T g, g=[1,1] -> col sums = [4,6]
    assert_equal [4.0, 6.0], Linalg.matvec_t(w, [1.0, 1.0])
  end

  def test_softmax_sums_to_one
    p = Linalg.softmax([1.0, 2.0, 3.0])
    assert_in_delta 1.0, p.sum, 1e-9
  end
end

class TestLayersGrad < Minitest::Test
  # Finite-difference gradient check on a Linear layer.
  def test_linear_gradient_check
    rng = Random.new(1)
    lin = Linear.new(3, 2, rng)
    x = [0.5, -0.2, 0.1]
    upstream = [1.0, -1.0]

    lin.forward(x)
    dx = lin.backward(upstream)

    eps = 1e-5
    (0...3).each do |j|
      xp = x.dup; xp[j] += eps
      xm = x.dup; xm[j] -= eps
      yp = lin.forward(xp); ym = lin.forward(xm)
      num = (0...2).sum { |o| upstream[o] * (yp[o] - ym[o]) } / (2 * eps)
      assert_in_delta num, dx[j], 1e-4
    end
  end

  def test_tanh_forward_backward
    t = Tanh.new
    y = t.forward([0.0, 100.0])
    assert_in_delta 0.0, y[0], 1e-9
    assert_in_delta 1.0, y[1], 1e-6
    g = t.backward([1.0, 1.0])
    assert_in_delta 1.0, g[0], 1e-9 # derivative at 0 is 1
  end
end

class TestTrainingLearns < Minitest::Test
  def test_overfits_repeating_pattern
    corpus = (%w[a b c d] * 50).join(" ")
    adapter = CorpusAdapter.new(corpus, context: 2, max_vocab: 20)
    model = LanguageModelBuilder.mlp_lm(vocab: adapter.vocab.size, dim: 8, context: 2, hidden: 16, seed: 1)
    tr = Trainer.new(model, optimizer: SGD.new(lr: 0.3, momentum: 0.9), seed: 1)
    lg = LossLogger.new(io: StringIO.new)
    tr.subscribe(lg)
    tr.train(adapter.sample_array, epochs: 8)
    assert_operator lg.history.last, :<, lg.history.first # loss decreased
    assert_operator lg.history.last, :<, 0.5             # essentially memorised

    gen = NeuralGenerator.new(model, adapter.vocab, context: 2)
    out = gen.generate(prompt: "a", length: 8, sampler: GreedySampler.new)
    assert_includes out[:text], "b c d" # learned the cycle
  end

  def test_adam_decreases_loss
    adapter = CorpusAdapter.new((%w[x y z] * 40).join(" "), context: 2, max_vocab: 20)
    model = LanguageModelBuilder.mlp_lm(vocab: adapter.vocab.size, dim: 6, context: 2, hidden: 12, seed: 2)
    tr = Trainer.new(model, optimizer: Adam.new(lr: 0.02), seed: 2)
    lg = LossLogger.new(io: StringIO.new)
    tr.subscribe(lg)
    tr.train(adapter.sample_array, epochs: 6)
    assert_operator lg.history.last, :<, lg.history.first
  end
end

class TestSamplers < Minitest::Test
  def test_greedy_is_argmax
    assert_equal 2, GreedySampler.new.pick([0.1, 0.2, 5.0, 0.3])
  end

  def test_entropy_target_temperature_monotone
    s = EntropyTargetSampler.new
    logits = [3.0, 1.0, 0.5, -1.0, 2.0]
    t_low = s.temperature_for(logits, 0.5)
    t_high = s.temperature_for(logits, 2.0)
    assert_operator t_high, :>, t_low # higher target entropy -> higher temp
  end

  def test_unknown_engine_decorator_runs
    vocab = Vocab.new(%w[gamma beta zeta manifold entropy], max_size: 10)
    base = GreedySampler.new
    eng = UnknownEngineSampler.new(base, vocab: vocab, xi_target: 0.05, seed: 1)
    id = eng.pick(Array.new(vocab.size) { |i| i * 0.1 },
                  generated: %w[gamma beta], target_h: 2.0)
    assert id.is_a?(Integer)
    assert_operator id, :>=, 0
  end
end

class TestMemento < Minitest::Test
  def test_model_memento_roundtrip
    adapter = CorpusAdapter.new((%w[a b c] * 20).join(" "), context: 2, max_vocab: 10)
    model = LanguageModelBuilder.mlp_lm(vocab: adapter.vocab.size, dim: 6, context: 2, hidden: 10, seed: 3)
    Trainer.new(model, optimizer: Adam.new(lr: 0.02), seed: 3)
      .train(adapter.sample_array, epochs: 3)
    before = model.forward([adapter.vocab.bos_id, adapter.vocab.id("a")])

    m = model.to_memento
    model2 = LanguageModelBuilder.mlp_lm(vocab: adapter.vocab.size, dim: 6, context: 2, hidden: 10, seed: 99)
    model2.load_memento({ "weights" => m[:weights] })
    after = model2.forward([adapter.vocab.bos_id, adapter.vocab.id("a")])
    assert_equal before, after # restored state reproduces outputs
  end
end

class TestNeuralChatFacade < Minitest::Test
  def test_end_to_end
    Akashic.reset!
    chat = NeuralOmegaChat.new(dim: 10, context: 2, hidden: 16, max_vocab: 60, seed: 5)
    chat.learn("ガンマ関数 から ベータ関数 が 現れる。 ζ(s) = β(p,q)/log x。 大域 多様体 エントロピー 不変量。", source: "t")
    chat.train!(epochs: 4, lr: 0.02, log: false, max_samples: 400)
    assert chat.trained?
    r = chat.reply("ベータ関数とは？", length: 8)
    assert r[:question_entropy].finite?
    assert r[:certified_invariant].finite?
    assert r[:generated][:text].is_a?(String)
    assert_operator Akashic.instance.size, :>=, 2
  end
end
