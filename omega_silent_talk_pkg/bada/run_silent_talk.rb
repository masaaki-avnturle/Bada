#!/usr/bin/env ruby
# frozen_string_literal: true
#
# run_silent_talk.rb — silent_talk.bada を Bada 量子拡張インタープリタで実行
#
#   cd omega_silent_talk_pkg/bada
#   ruby run_silent_talk.rb [script.bada]

Encoding.default_external = Encoding::UTF_8
Encoding.default_internal = Encoding::UTF_8

require "fileutils"

HERE = File.expand_path(__dir__)
$LOAD_PATH.unshift(File.expand_path("../../bada_ruby/lib", HERE))

require_relative "quantum_ext"

script = ARGV.shift || File.join(HERE, "silent_talk.bada")

puts "== Bada Quantum :: silent_talk =="
interp = Bada::Quantum::Interpreter.new(base_dir: File.dirname(File.expand_path(script)))
interp.run(File.read(script, encoding: "UTF-8")).each { |line| puts line }
