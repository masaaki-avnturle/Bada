# frozen_string_literal: true

require_relative "../entropy"

module Bada
  module NN
    # Vocabulary: token <-> id with frequency capping and special tokens.
    class Vocab
      BOS = "<bos>"
      UNK = "<unk>"

      attr_reader :id_to_token, :token_to_id

      def initialize(tokens, max_size: 300)
        freq = Hash.new(0)
        tokens.each { |t| freq[t] += 1 }
        top = freq.sort_by { |(_, c)| -c }.first(max_size).map(&:first)
        @id_to_token = [BOS, UNK] + top
        @token_to_id = {}
        @id_to_token.each_with_index { |t, i| @token_to_id[t] = i }
      end

      def size
        @id_to_token.length
      end

      def id(token)
        @token_to_id.fetch(token, @token_to_id[UNK])
      end

      def token(id)
        @id_to_token[id] || UNK
      end

      def bos_id
        @token_to_id[BOS]
      end

      def encode(tokens)
        tokens.map { |t| id(t) }
      end

      def to_h
        { "id_to_token" => @id_to_token }
      end

      def self.from_h(h)
        v = allocate
        v.instance_variable_set(:@id_to_token, h["id_to_token"])
        map = {}
        h["id_to_token"].each_with_index { |t, i| map[t] = i }
        v.instance_variable_set(:@token_to_id, map)
        v
      end
    end

    # CorpusAdapter — Adapter: turns a Bada::Knowledge corpus (or raw text)
    # into the (vocab, id_stream, training_samples) shape the NN expects.
    class CorpusAdapter
      attr_reader :vocab, :id_stream

      # knowledge: Bada::Knowledge | String | Array<String tokens>
      def initialize(knowledge, context:, max_vocab: 300)
        tokens =
          case knowledge
          when Bada::Knowledge then knowledge.sentences.flat_map(&:tokens)
          when String then Bada::Entropy.tokenize(knowledge)
          when Array then knowledge
          else raise ArgumentError, "unsupported corpus"
          end
        @context = context
        @vocab = Vocab.new(tokens, max_size: max_vocab)
        @id_stream = @vocab.encode(tokens)
      end

      # Yields [context_ids(Array len C), target_id] sliding-window samples,
      # padded at the start with BOS so early positions are usable.
      def samples
        return enum_for(:samples) unless block_given?
        bos = @vocab.bos_id
        padded = Array.new(@context, bos) + @id_stream
        (@context...padded.length).each do |i|
          ctx = padded[(i - @context)...i]
          yield [ctx, padded[i]]
        end
      end

      def sample_array
        arr = []
        samples { |s| arr << s }
        arr
      end
    end
  end
end
