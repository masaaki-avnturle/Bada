# frozen_string_literal: true

module Bada
  module NN
    # TrainingObserver — Observer: receives epoch events from the Trainer
    # without the Trainer knowing what is done with them.
    class TrainingObserver
      def on_epoch_end(_epoch, _avg_loss, _model); end
      def on_train_end(_model); end
    end

    # Logs loss per epoch to an IO.
    class LossLogger < TrainingObserver
      def initialize(io: $stdout, every: 1)
        @io = io
        @every = every
        @history = []
      end

      attr_reader :history

      def on_epoch_end(epoch, avg_loss, _model)
        @history << avg_loss
        @io.puts(format("epoch %3d  loss=%.4f  ppl=%.2f", epoch, avg_loss, Math.exp(avg_loss))) if (epoch % @every).zero?
      end
    end

    # Keeps the best (lowest-loss) model state via the Memento.
    class Checkpointer < TrainingObserver
      attr_reader :best_loss, :best_memento

      def initialize
        @best_loss = Float::INFINITY
        @best_memento = nil
      end

      def on_epoch_end(_epoch, avg_loss, model)
        if avg_loss < @best_loss
          @best_loss = avg_loss
          @best_memento = model.to_memento
        end
      end

      def on_train_end(model)
        model.load_memento(deep_stringify(@best_memento)) if @best_memento
      end

      private

      # to_memento uses symbol keys; load_memento reads "weights" string key.
      def deep_stringify(m)
        { "meta" => m[:meta], "weights" => m[:weights] }
      end
    end
  end
end
