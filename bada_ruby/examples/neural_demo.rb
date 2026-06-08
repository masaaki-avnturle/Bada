#!/usr/bin/env ruby
# Neural OmegaChat — from-scratch neural LLM (pure Ruby) demo.
#   ruby examples/neural_demo.rb
$LOAD_PATH.unshift(File.expand_path("../lib", __dir__))
require "bada"

chat = Bada::NN::NeuralOmegaChat.new(dim: 16, context: 2, hidden: 32, max_vocab: 150, seed: 42)
Dir[File.expand_path("../corpus/*.txt", __dir__)].sort.each { |f| chat.learn_file(f) }

puts "training neural network (backprop, pure Ruby)…"
chat.train!(epochs: 6, lr: 0.01, max_samples: 2500)

puts
puts chat.ask("大域的部分積分多様体のエントロピー不変量から何が言えるか？", length: 20)
chat.save("model.json")
puts "\nsaved checkpoint -> model.json"
