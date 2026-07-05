# frozen_string_literal: true

require_relative "lib/bada/version"

Gem::Specification.new do |spec|
  spec.name        = "bada"
  spec.version     = Bada::VERSION
  spec.authors     = ["Masaaki Yamaguchi"]
  spec.summary     = "Bada language + OmegaChat (ChatGPT branch) in pure Ruby"
  spec.description = <<~DESC
    Bada is the Yamaguchi / TupleSpace operator-algebra language rebuilt from
    scratch in pure Ruby, together with OmegaChat — a ChatGPT branch (分派) that
    answers and generates language, equations, and theory using the Shannon
    entropy / global partial integral manifold entropy invariant, error-corrected
    on the complex-rotation special-relativity integrable system.
  DESC
  spec.homepage = "https://masaaki-avnturle.github.io/Bada/"
  spec.license  = "MIT"
  spec.required_ruby_version = ">= 3.0"

  spec.files = Dir[
    "lib/**/*.rb",
    "lib/bada_src/*.bada",
    "bin/*",
    "corpus/*.txt",
    "examples/*",
    "README.md",
    "LICENSE"
  ]
  spec.bindir      = "bin"
  spec.executables = ["bada"]
  spec.require_paths = ["lib"]
end
