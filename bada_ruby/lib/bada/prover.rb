# frozen_string_literal: true

# Bada::Prover — the Unknown A-priori Engine (未知事前エンジン): imagine
# unsolved-style mathematical problems (seeded by the Bada manifold/entropy
# machinery) and decide them with *sound* automated reasoning.
#
# Soundness contract:
#   :proved    — established by a complete, checkable method
#                (polynomial-sum induction, modular exhaustion, finite cases)
#   :disproved — a concrete counterexample was found (sound)
#   :open      — undecided by our methods; computational evidence only,
#                NEVER claimed as a proof
#
#   engine = Bada::Prover::Engine.new
#   puts engine.render("大域的部分積分多様体の未解決問題を想像して証明して")

require "set"
require_relative "prover/polynomial"
require_relative "prover/proof"
require_relative "prover/conjecture"
require_relative "prover/engine"

module Bada
  module Prover
  end
end
