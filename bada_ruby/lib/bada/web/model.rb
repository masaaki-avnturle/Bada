# frozen_string_literal: true

require_relative "../tuplespace"

module Bada
  module Web
    # ActiveRecord-style ORM, rebuilt from scratch on top of the Bada
    # Ω::DATABASE (TupleSpace / Akashic Record). Each model class owns an
    # in-memory table; every persisted row is *also* written into the shared
    # Akashic TupleSpace as a manifold point, so the whole database is queryable
    # by keyword or by entropy invariant (see Bada::TupleSpace).
    #
    #   class Post < Bada::Web::Model
    #     attribute :title
    #     attribute :body
    #     validates :title, presence: true
    #   end
    #
    #   Post.create(title: "Hello", body: "world")
    #   Post.all            # => [#<Post id=1 ...>]
    #   Post.find(1)
    #   Post.where(title: "Hello")
    #
    class Model
      # Process-wide Akashic store shared by every model (the Ω::DATABASE).
      def self.akashic
        @@akashic ||= TupleSpace.new
      end

      class << self
        # --- schema --------------------------------------------------------
        def attribute(name)
          name = name.to_sym
          attribute_names << name unless attribute_names.include?(name)
          define_method(name) { @attributes[name] }
          define_method("#{name}=") { |v| @attributes[name] = v }
          name
        end

        def attributes(*names)
          names.each { |n| attribute(n) }
        end

        def attribute_names
          @attribute_names ||= []
        end

        # --- validations ---------------------------------------------------
        def validations
          @validations ||= []
        end

        # validates :title, presence: true
        # validates :title, length: { minimum: 2 }
        def validates(name, presence: false, length: nil)
          validations << { name: name.to_sym, presence: presence, length: length }
        end

        # --- persistence / querying ---------------------------------------
        def table
          @table ||= []
        end

        def reset!
          @table = []
          @sequence = 0
        end

        def next_id
          @sequence ||= 0
          @sequence += 1
        end

        def create(attrs = {})
          record = new(attrs)
          record.save
          record
        end

        def all
          table.dup
        end

        def count = table.length

        def first = table.first
        def last  = table.last

        def find(id)
          id = id.to_i
          table.find { |r| r.id == id } ||
            raise(RecordNotFound, "#{name} id=#{id} not found")
        end

        def find_by(conditions)
          where(conditions).first
        end

        def where(conditions)
          conditions = conditions.transform_keys(&:to_sym)
          table.select do |r|
            conditions.all? { |k, v| r.public_send(k).to_s == v.to_s }
          end
        end

        def destroy_all
          table.each(&:_remove_from_akashic)
          reset!
        end

        # Name used for Akashic keys and form params (e.g. "post").
        def model_key
          name.to_s.split("::").last.downcase
        end
      end

      class RecordNotFound < StandardError; end

      attr_reader :id, :errors

      def initialize(attrs = {})
        @attributes = {}
        @id         = nil
        @errors     = []
        assign(attrs)
      end

      def assign(attrs)
        (attrs || {}).each do |k, v|
          setter = "#{k}="
          public_send(setter, v) if respond_to?(setter)
        end
        self
      end
      alias attributes= assign

      def attributes
        @attributes.dup
      end

      def persisted?
        !@id.nil?
      end

      def valid?
        @errors = []
        self.class.validations.each do |rule|
          value = public_send(rule[:name])
          if rule[:presence] && (value.nil? || value.to_s.strip.empty?)
            @errors << "#{rule[:name]} can't be blank"
          end
          if (len = rule[:length]) && (min = len[:minimum]) && value.to_s.length < min
            @errors << "#{rule[:name]} is too short (minimum is #{min})"
          end
        end
        @errors.empty?
      end

      def save
        return false unless valid?

        @id ||= self.class.next_id
        self.class.table.delete_if { |r| r.id == @id }
        self.class.table << self
        _write_to_akashic
        true
      end

      def update(attrs)
        assign(attrs)
        save
      end

      def destroy
        self.class.table.delete_if { |r| r.id == @id }
        _remove_from_akashic
        freeze
        self
      end

      def to_param = @id.to_s

      def to_s
        "#<#{self.class.name} id=#{@id} #{@attributes.inspect}>"
      end
      alias inspect to_s

      # --- Akashic (Ω::DATABASE) integration -------------------------------

      def akashic_key
        "#{self.class.model_key}:#{@id}"
      end

      def _write_to_akashic
        _remove_from_akashic
        text = @attributes.values.map(&:to_s).join(" ")
        Model.akashic.push(text, key: akashic_key,
                                 tags: { model: self.class.model_key, id: @id })
      end

      def _remove_from_akashic
        Model.akashic.store.delete_if { |t| t.key == akashic_key }
      end
    end
  end
end
