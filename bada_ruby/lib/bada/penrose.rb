# frozen_string_literal: true

# Bada::Penrose — Roger Penrose graphical (diagrammatic) notation as a working
# system: a palette of his differential/integral/tensor picture-symbols, a
# canvas you "draw" on that auto-computes (real Einstein-summation tensor
# engine), and ChatGPT integration that answers from a drawn diagram and
# generates a paper and source code. Pure Ruby.
#
#   studio = Bada::Penrose::Studio.new
#   studio.draw("i-[A]-[B]-j", values: { "A" => [[1,2],[3,4]], "B" => [[5,6],[7,8]] })
#   studio.compute   #=> matrix product, auto-contracted
#   puts studio.ask("これは何を計算している？")
#   puts studio.paper(question: "...")   # 論文
#   puts studio.code                     # ソースコード

require_relative "penrose/tensor"
require_relative "penrose/glyph_svg"
require_relative "penrose/palette"
require_relative "penrose/diagram"
require_relative "penrose/canvas"
require_relative "penrose/evaluator"
require_relative "penrose/latex"
require_relative "penrose/builder"
require_relative "penrose/paper"
require_relative "penrose/codegen"
require_relative "penrose/webapp"
require_relative "penrose/studio"

module Bada
  module Penrose
  end
end
