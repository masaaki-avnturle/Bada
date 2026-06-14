#!/usr/bin/env ruby
# Unknown a-priori engine demo: imagine unsolved-style problems and soundly
# prove / disprove / flag-open them, then emit a proof paper.
$LOAD_PATH.unshift(File.expand_path("../lib", __dir__))
require "bada"

engine = Bada::Prover::Engine.new
puts engine.render("大域的部分積分多様体の未解決問題を想像して証明して", count: 5)
puts
puts "──────── 証明論文（最初の命題） ────────"
puts engine.paper(engine.imagine("ガンマ関数の未解決問題", count: 5).first)
