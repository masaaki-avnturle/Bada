# frozen_string_literal: true

module Bada
  module EVOS
    # BadaOS real-time kernel — the operating-system core of the electric
    # vehicle. A cooperative, priority-driven, period-scheduled task runner.
    #
    # An EV OS is a soft-real-time control loop: many subsystems (battery
    # management, motor control, thermal, charging, diagnostics) must each run
    # at their own rate and in a deterministic order every control cycle. The
    # Bada kernel models exactly that — tasks declare a period (in ticks) and a
    # priority; on each tick the scheduler runs every task that is due, highest
    # priority first, so safety-critical work (BMS, traction) always pre-empts
    # housekeeping (range estimate, logging).
    class Task
      attr_reader :name, :period, :priority
      attr_accessor :last_run, :runs

      def initialize(name, period:, priority:, &body)
        @name = name
        @period = [period.to_i, 1].max
        @priority = priority
        @body = body
        @last_run = nil
        @runs = 0
      end

      # Has enough time elapsed since the last run for this task to fire again?
      def due?(tick)
        @last_run.nil? || (tick - @last_run) >= @period
      end

      def call(ctx, tick)
        @last_run = tick
        @runs += 1
        @body.call(ctx, tick)
      end
    end

    # The scheduler holds the task table and advances the system clock.
    class Scheduler
      attr_reader :tasks, :tick

      def initialize
        @tasks = []
        @tick = 0
      end

      # Register a periodic task. Higher priority runs first within a tick.
      def every(name, period: 1, priority: 0, &body)
        @tasks << Task.new(name, period: period, priority: priority, &body)
        self
      end

      # Advance one control cycle: run every due task by priority, then tick.
      # Returns the names of the tasks that ran (the cycle's run-list).
      def step(ctx)
        due = @tasks.select { |t| t.due?(@tick) }.sort_by { |t| [-t.priority, t.name] }
        due.each { |t| t.call(ctx, @tick) }
        @tick += 1
        due.map(&:name)
      end

      # Run a fixed number of control cycles.
      def run(ctx, ticks:)
        ticks.times { step(ctx) }
        @tick
      end
    end
  end
end
