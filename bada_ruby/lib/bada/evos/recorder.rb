# frozen_string_literal: true

require_relative "../tuplespace"

module Bada
  module EVOS
    # The flight-recorder / black box, backed by the Bada Ω::DATABASE
    # (TupleSpace / Akashic Record).
    #
    # Every notable event (boot, fault, charge start, telemetry snapshot) is
    # pushed as a tuple. Because TupleSpace measures each entry's manifold
    # entropy invariant Ξ on the way in, the log is searchable not only by
    # keyword but by *information content* — a sudden Ξ excursion in the event
    # stream is itself an anomaly signal the diagnostics subsystem reads back.
    class Recorder
      attr_reader :db

      def initialize(db: Bada::TupleSpace.new)
        @db = db
        @seq = 0
      end

      # Record an event. Returns the stored tuple.
      def log(text, tags: {})
        @seq += 1
        key = format("Ω::ev%05d", @seq)
        @db.push(text, key: key, tags: { seq: @seq }.merge(tags))
      end

      def size
        @db.size
      end

      # Mean manifold entropy invariant Ξ over the most recent `n` events —
      # the "information temperature" of the system's behaviour.
      def recent_invariant(n: 10)
        recent = @db.store.last(n)
        return 0.0 if recent.empty?
        recent.sum { |t| t.stats[:invariant] } / recent.length
      end

      # Replay the last n events as human-readable lines.
      def tail(n: 10)
        @db.store.last(n).map { |t| "#{t.key} #{t.text}" }
      end
    end
  end
end
