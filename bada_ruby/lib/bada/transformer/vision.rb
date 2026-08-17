# frozen_string_literal: true

require_relative "tensor"
require_relative "model"

module Bada
  module Transformer
    # Vision head — an image-processing Transformer (ViT-style) on top of the
    # same manifold-gauge Encoder. A grid of intensities is cut into patches,
    # each patch is linearly projected to a token embedding, the encoder mixes
    # them under the gamma-manifold gauge, and each patch is projected back to an
    # intensity — the reconstructed "mental image" (対象の脳内に浮かぶ画像).
    class Vision
      T = Tensor

      def initialize(encoder:, grid: 8, patch: 2, seed: 0x71501)
        @encoder = encoder
        @grid = grid
        @patch = patch
        @per_side = grid / patch
        @n_patches = @per_side * @per_side
        @patch_dim = patch * patch
        rng = T::PRNG.new(seed)
        @proj_in = T.randmat(@patch_dim, encoder.d_model, rng)   # patch -> token
        @proj_out = T.randmat(encoder.d_model, 1, rng)           # token -> intensity
      end

      attr_reader :grid, :n_patches

      # image: grid x grid array of floats in [0,1]. Returns a reconstructed
      # grid x grid array in [0,1] (the transformer's rendered mental image).
      def process(image)
        patches = patchify(image)                 # n_patches x patch_dim
        tokens = T.matmul(patches, @proj_in)       # n_patches x d
        hidden = @encoder.run(tokens)              # contextual patches
        raw = T.matmul(hidden, @proj_out).map { |r| r[0] }
        # z-score across patches so the rendered image always keeps contrast
        mean = raw.sum / raw.length
        var = raw.sum { |v| (v - mean)**2 } / raw.length
        std = Math.sqrt(var) + 1e-9
        outs = raw.map { |v| sigmoid((v - mean) / std) }
        unpatch(outs)
      end

      # Render a grid (values in [0,1]) as ASCII shades.
      def self.ascii(grid_vals)
        shades = " .:-=+*#%@"
        grid_vals.map do |row|
          row.map { |v| shades[(v.clamp(0.0, 1.0) * (shades.length - 1)).round] }.join
        end.join("\n")
      end

      private

      def patchify(image)
        rows = []
        @per_side.times do |py|
          @per_side.times do |px|
            vec = []
            @patch.times do |dy|
              @patch.times do |dx|
                vec << image[py * @patch + dy][px * @patch + dx]
              end
            end
            rows << vec
          end
        end
        rows
      end

      def unpatch(outs)
        out = Array.new(@grid) { Array.new(@grid, 0.0) }
        idx = 0
        @per_side.times do |py|
          @per_side.times do |px|
            val = outs[idx]
            @patch.times do |dy|
              @patch.times do |dx|
                out[py * @patch + dy][px * @patch + dx] = val
              end
            end
            idx += 1
          end
        end
        out
      end

      def sigmoid(x)
        1.0 / (1.0 + Math.exp(-x))
      end
    end
  end
end
