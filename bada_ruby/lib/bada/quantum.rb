# frozen_string_literal: true

# Bada::Quantum — the quantum-entanglement Bell-test *universal space telegraph*.
#
# A Bada-language application that turns the reports' physics into a working
# telecommunication device:
#
#   Bada::Quantum::Qubit2         two-qubit state-vector simulator (the pair)
#   Bada::Quantum::Bell           CHSH inequality + spooky-action certificate
#   Bada::Quantum::Quintic        5th-degree solution-formula / period carrier
#   Bada::Quantum::Jones          Jones-polynomial correlation of a pair
#   Bada::Quantum::Uncertainty    Robertson uncertainty + Born statistics
#   Bada::Quantum::Semiconductor  Fermi-Dirac / tunnelling buildability
#   Bada::Quantum::Channel        superdense-coding message transmission
#   Bada::Quantum::SpaceTelegraph facade: prove + transmit + render
#
#   require "bada"
#   puts Bada::Quantum::SpaceTelegraph.new.render("HELLO SPACE")

require_relative "quantum/qubit"
require_relative "quantum/bell"
require_relative "quantum/quintic"
require_relative "quantum/jones"
require_relative "quantum/uncertainty"
require_relative "quantum/semiconductor"
require_relative "quantum/channel"
require_relative "quantum/telegraph"

module Bada
  module Quantum
  end
end
