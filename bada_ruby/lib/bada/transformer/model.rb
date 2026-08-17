# frozen_string_literal: true

require_relative "tensor"
require_relative "../manifold"
require_relative "../special"

module Bada
  module Transformer
    # A from-scratch Transformer encoder whose attention is gauged by the
    # *global partial integral manifold* of the gamma function
    # (∬ 1/(x log x)^2). The manifold line element becomes a distance kernel on
    # the attention scores, so context mixing follows the report's geometry
    # rather than a plain dot-product. Deterministic (seeded) weights, pure Ruby.
    class Encoder
      T = Tensor

      attr_reader :d_model, :n_heads, :n_blocks, :vocab, :last_attention

      def initialize(vocab:, d_model: 24, n_heads: 4, n_blocks: 2, d_ff: 48, seed: 0xBADA5EED)
        @vocab = vocab
        @d_model = d_model
        @n_heads = n_heads
        @d_head = d_model / n_heads
        @n_blocks = n_blocks
        @d_ff = d_ff
        rng = T::PRNG.new(seed)

        @embed = T.randmat(vocab, d_model, rng, scale: 0.6)
        @blocks = Array.new(n_blocks) do
          {
            wq: T.randmat(d_model, d_model, rng),
            wk: T.randmat(d_model, d_model, rng),
            wv: T.randmat(d_model, d_model, rng),
            wo: T.randmat(d_model, d_model, rng),
            w1: T.randmat(d_model, d_ff, rng),
            b1: Array.new(d_ff, 0.0),
            w2: T.randmat(d_ff, d_model, rng),
            b2: Array.new(d_model, 0.0)
          }
        end
        # effective Planck scale of attention from the beta/zeta gauge
        @hbar_eff = 1.0 / Math.sqrt(@d_head)
      end

      def embedding
        @embed
      end

      # Look up token ids -> n x d embeddings (a copy).
      def embed(token_ids)
        token_ids.map { |t| @embed[t % @vocab].dup }
      end

      # Sinusoidal positional encoding.
      def positional(n)
        Array.new(n) do |pos|
          Array.new(@d_model) do |i|
            angle = pos / (10_000.0**((2 * (i / 2)) / @d_model.to_f))
            i.even? ? Math.sin(angle) : Math.cos(angle)
          end
        end
      end

      # Manifold gauge bias: additive score bias b(i,j) = log(element(|i-j|+2)),
      # the (log of the) global partial integral manifold line element as a
      # distance kernel — near tokens couple strongly, far tokens decay.
      def gauge_bias(n)
        Array.new(n) do |i|
          Array.new(n) do |j|
            Math.log(Manifold.element((i - j).abs + 2) + 1e-12)
          end
        end
      end

      # Forward pass from token ids -> contextual hidden states (n x d).
      def forward(token_ids)
        run(T.add(embed(token_ids), positional(token_ids.length)))
      end

      # Run the encoder blocks on already-embedded inputs (n x d). Used by the
      # vision head, which supplies continuous patch embeddings instead of a
      # token lookup.
      def run(x)
        bias = gauge_bias(x.length)
        @last_attention = nil
        @blocks.each do |blk|
          attn = attention(x, blk, bias)
          x = x.each_index.map { |i| T.layernorm(x[i].each_index.map { |k| x[i][k] + attn[i][k] }) }
          ff = ffn(x, blk)
          x = x.each_index.map { |i| T.layernorm(x[i].each_index.map { |k| x[i][k] + ff[i][k] }) }
        end
        x
      end

      # Language head with weight tying: logits = hidden · embedding^T.
      def logits(hidden)
        T.matmul(hidden, T.transpose(@embed))
      end

      private

      def attention(x, blk, bias)
        n = x.length
        q = T.matmul(x, blk[:wq])
        k = T.matmul(x, blk[:wk])
        v = T.matmul(x, blk[:wv])
        context = T.zeros(n, @d_model)
        avg_attn = T.zeros(n, n)

        @n_heads.times do |h|
          off = h * @d_head
          n.times do |i|
            scores = Array.new(n) do |j|
              dot = 0.0
              @d_head.times { |d| dot += q[i][off + d] * k[j][off + d] }
              dot * @hbar_eff + bias[i][j]
            end
            w = T.softmax(scores)
            n.times do |j|
              avg_attn[i][j] += w[j] / @n_heads
              @d_head.times { |d| context[i][off + d] += w[j] * v[j][off + d] }
            end
          end
        end
        @last_attention = avg_attn
        T.matmul(context, blk[:wo])
      end

      def ffn(x, blk)
        h = T.gelu_mat(T.add_bias(T.matmul(x, blk[:w1]), blk[:b1]))
        T.add_bias(T.matmul(h, blk[:w2]), blk[:b2])
      end
    end
  end
end
