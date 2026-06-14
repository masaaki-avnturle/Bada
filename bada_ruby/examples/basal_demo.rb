#!/usr/bin/env ruby
# Basal-ganglia in-body thermal neural system demo: small modular nuclei classes
# gate action selection over imagined math conjectures, proving each soundly.
$LOAD_PATH.unshift(File.expand_path("../lib", __dir__))
require "bada"

# 1) the LLM decoder gated by the basal ganglia (Go/NoGo + thermal annealing)
sampler = Bada::Basal::BasalGangliaSampler.new(k: 5, seed: 7)
logits = [0.1, 5.0, 0.2, 0.3, 0.4]
puts "basal-ganglia token picks: #{Array.new(20) { sampler.pick(logits) }.tally.sort.to_h}"
puts

# 2) the unknown a-priori engine deliberating via the in-body neural system
puts Bada::Basal::AprioriEngine.new(seed: 7)
  .render("大脳基底核の熱ネットワークで未解決問題を想像して証明する", count: 5)
