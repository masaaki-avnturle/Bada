# frozen_string_literal: true

# Bada::Transformer — a from-scratch Transformer (language + vision) whose
# attention is gauged by the gamma-function global partial integral manifold.
#
#   Bada::Transformer::Tensor    pure-Ruby matrix ops + seeded PRNG
#   Bada::Transformer::Encoder   manifold-gauge multi-head self-attention
#   Bada::Transformer::Vision    ViT-style image-processing head
#
# It is the engine under Bada::Mind (thought verbalization / mental image /
# source-code generation).

require_relative "transformer/tensor"
require_relative "transformer/model"
require_relative "transformer/vision"

module Bada
  module Transformer
  end
end
