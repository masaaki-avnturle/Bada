# frozen_string_literal: true

# Bada::NN — a from-scratch neural-network LLM (Bengio-style MLP language model
# with full backprop) wired into the Bada manifold/entropy theory to form the
# "unknown engine" ChatGPT. Pure Ruby, no external dependencies.
#
# Design patterns used (one concern per file):
#   Composite          Sequential  (a stack of layers acts as one layer)
#   Strategy           Layer.forward/backward, Optimizer, Sampler
#   Factory Method     LayerFactory
#   Builder            LanguageModelBuilder
#   Template Method    Trainer#train
#   Observer           TrainingObserver / LossLogger / Checkpointer
#   Adapter            CorpusAdapter (Bada::Knowledge -> training data)
#   Decorator          UnknownEngineSampler (manifold/entropy steering)
#   Chain of Resp.     MeasureHandler -> Retrieve -> Generate -> Correct -> Record
#   Singleton          Akashic (process-wide Omega::DATABASE)
#   Memento            Sequential#to_memento / load_memento, NeuralOmegaChat.save/load
#   Facade             NeuralOmegaChat

require_relative "nn/linalg"
require_relative "nn/param"
require_relative "nn/layers"
require_relative "nn/sequential"
require_relative "nn/factory"
require_relative "nn/optimizer"
require_relative "nn/observer"
require_relative "nn/vocab"
require_relative "nn/trainer"
require_relative "nn/sampler"
require_relative "nn/generator"
require_relative "nn/pipeline"
require_relative "nn/chat"

module Bada
  module NN
  end
end
