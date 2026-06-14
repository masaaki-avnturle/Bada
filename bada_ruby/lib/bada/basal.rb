# frozen_string_literal: true

# Bada::Basal — an in-body neural system that simulates the basal ganglia as a
# thermal network: small, modular Ruby classes (one per nucleus), each
# isomorphic to a layer of neurons, wired with classic design patterns and
# gated by a thermal field whose lateral conductances come from the gamma-
# function global partial integral manifold. It is the action-selection
# controller for the LLM decoder and the unknown a-priori (conjecture) engine.
#
# Design patterns:
#   Strategy   Nucleus#activate, gating (Argmax/Boltzmann)
#   Composite  BasalGanglia as a network of nuclei
#   Mediator   BasalGanglia coordinates inter-nucleus signalling
#   Observer   Dopamine (SNc) broadcasts RPE to the striatum (learning)
#   Factory    CircuitFactory builds the wired circuit
#   Facade     BodyNeuralSystem / AprioriEngine
#   Flyweight  Synapse value objects
#
#   require "bada/basal"
#   puts Bada::Basal::AprioriEngine.new(seed: 1).render("未解決問題を想像して証明")

require_relative "basal/synapse"
require_relative "basal/nucleus"
require_relative "basal/thermal"
require_relative "basal/dopamine"
require_relative "basal/circuit"
require_relative "basal/factory"
require_relative "basal/engine"
require_relative "basal/sampler"

module Bada
  module Basal
  end
end
