# frozen_string_literal: true

module Bada
  module Web
    # A lightweight schema / migration layer. Because the ORM stores rows in
    # memory (and mirrors them into the Ω::DATABASE TupleSpace), a "migration"
    # declares the columns a model table should have and records the schema in
    # the global Schema registry — the same shape as a Rails migration:
    #
    #   class CreatePosts < Bada::Web::Migration
    #     def change
    #       create_table :posts do |t|
    #         t.string :title
    #         t.text   :body
    #         t.timestamps
    #       end
    #     end
    #   end
    #
    #   CreatePosts.new.migrate
    class Migration
      # Global schema registry: table name => [ {name:, type:}, ... ]
      def self.schema
        @@schema ||= {}
      end

      def migrate
        change if respond_to?(:change)
        self
      end

      def create_table(name)
        table = TableDefinition.new
        table.column(:id, :integer)
        yield table if block_given?
        Migration.schema[name.to_sym] = table.columns
        table
      end

      def drop_table(name)
        Migration.schema.delete(name.to_sym)
      end

      # Collects column definitions inside `create_table`.
      class TableDefinition
        attr_reader :columns

        def initialize
          @columns = []
        end

        def column(name, type)
          @columns << { name: name.to_sym, type: type.to_sym }
          self
        end

        # Rails-style column type shortcuts.
        %i[string text integer float boolean datetime].each do |type|
          define_method(type) { |name| column(name, type) }
        end

        def timestamps
          column(:created_at, :datetime)
          column(:updated_at, :datetime)
        end
      end
    end
  end
end
