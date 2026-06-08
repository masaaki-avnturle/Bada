# frozen_string_literal: true

require_relative "sequential"
require_relative "optimizer"
require_relative "observer"

module Bada
  module NN
    # Trainer — Template Method: #train fixes the skeleton of the training
    # algorithm (epoch loop -> shuffle -> per-sample forward/loss/backward/step
    # -> notify observers), while individual steps are overridable hooks.
    class Trainer
      def initialize(model, optimizer: SGD.new(lr: 0.1, momentum: 0.9), seed: 0)
        @model = model
        @opt = optimizer
        @loss_fn = CrossEntropySoftmax.new
        @observers = []
        @rng = Random.new(seed)
      end

      def subscribe(observer)
        @observers << observer
        self
      end

      # The invariant skeleton — do not override.
      def train(samples, epochs: 5)
        samples = samples.to_a
        epochs.times do |e|
          order = (0...samples.length).to_a.shuffle(random: @rng)
          total = 0.0
          order.each do |idx|
            ctx, target = samples[idx]
            total += train_step(ctx, target)
          end
          avg = total / samples.length
          notify_epoch(e + 1, avg)
        end
        @observers.each { |o| o.on_train_end(@model) }
        @model
      end

      protected # hooks

      def train_step(ctx, target)
        @model.zero_grad!
        logits = @model.forward(ctx)
        loss = @loss_fn.forward(logits, target)
        @model.backward(@loss_fn.backward)
        @opt.step(@model.params)
        loss
      end

      def notify_epoch(epoch, avg_loss)
        @observers.each { |o| o.on_epoch_end(epoch, avg_loss, @model) }
      end
    end
  end
end
