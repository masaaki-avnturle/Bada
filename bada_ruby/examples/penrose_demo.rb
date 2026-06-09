#!/usr/bin/env ruby
# Penrose graphical notation demo: draw -> compute -> answer -> paper -> code.
$LOAD_PATH.unshift(File.expand_path("../lib", __dir__))
require "bada"

studio = Bada::Penrose::Studio.new
puts studio.palette
puts
studio.draw("i-[A]-[B]-j", values: { "A" => [[1, 2], [3, 4]], "B" => [[5, 6], [7, 8]] })
puts studio.report(question: "この図式は何を計算しているか？")
