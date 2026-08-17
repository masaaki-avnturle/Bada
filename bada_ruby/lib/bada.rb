# frozen_string_literal: true

# Bada — the Bada language and the OmegaChat ChatGPT branch (分派), rebuilt
# from scratch in pure Ruby on the Yamaguchi / TupleSpace framework.
#
#   require "bada"
#
#   chat = Bada::OmegaChat.new
#   chat.learn_file("corpus/caostics.txt")
#   puts chat.ask("このレポートから何ができるか？")
#
# Module map:
#   Bada::Special          gamma / beta / zeta / dalanversian circle operators
#   Bada::Entropy          Shannon entropy + tokenization
#   Bada::Manifold         global partial integral manifold entropy invariant Ξ
#   Bada::ErrorCorrection  complex-rotation / special-relativity integrable fix
#   Bada::TupleSpace       Omega::DATABASE (Akashic Record)
#   Bada::BadaNode         Bada operator runtime ( <-  -<  >- )
#   Bada::Interpreter      Bada language source evaluator
#   Bada::Knowledge        report/web ingestion -> measured corpus
#   Bada::Generator        entropy-driven text / equation / theory generation
#   Bada::QAEngine         entropy-driven question answering
#   Bada::Thurston         Thurston-Perelman manifold + Shannon entropy placement
#   Bada::Catastrophe      Thom catastrophe branch-point information generation
#   Bada::Millennium       7 Clay problems, gamma-manifold theory decomposition
#   Bada::InfoEngine       information-generation facade (the three above)
#   Bada::Penrose          Penrose graphical notation: draw -> compute -> paper/code
#   Bada::Quantum          entangled-pair Bell-test universal space telegraph
#   Bada::OmegaChat        the ChatGPT branch tying it all together
#   Bada::NN               from-scratch neural-network LLM (unknown engine)

require_relative "bada/version"
require_relative "bada/special"
require_relative "bada/entropy"
require_relative "bada/manifold"
require_relative "bada/error_correction"
require_relative "bada/tuplespace"
require_relative "bada/language"
require_relative "bada/knowledge"
require_relative "bada/generator"
require_relative "bada/qa_engine"
require_relative "bada/thurston"
require_relative "bada/catastrophe"
require_relative "bada/millennium"
require_relative "bada/info_engine"
require_relative "bada/penrose"
require_relative "bada/quantum"
require_relative "bada/qc"
require_relative "bada/transformer"
require_relative "bada/mind"
require_relative "bada/chat"
require_relative "bada/nn"

module Bada
end
