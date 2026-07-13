# frozen_string_literal: true

require_relative "qubit"
require_relative "semiconductor"
require_relative "../error_correction"

module Bada
  module Quantum
    # The entanglement-assisted classical channel: superdense coding.
    #
    # Alice and Bob pre-share Bell pairs. To send two classical bits, Alice
    # applies one of the four Bell rotations {I, X, Z, ZX} to *her* qubit and
    # ships it to Bob; Bob's Bell measurement recovers both bits. That is 2
    # classical bits carried per pair — the correlation of the pair *is* the
    # channel. Crucially this obeys no-signaling (Bob's marginal never changes
    # until Alice's qubit physically arrives), so it is a legitimate telegraph,
    # not a faster-than-light one.
    #
    # Physical noise comes from the semiconductor bath (thermal bit flips); we
    # protect the payload with a repetition code and stabilise the recovered
    # statistics with Bada's complex-rotation error corrector.
    module Channel
      module_function

      # --- text <-> bit helpers --------------------------------------------

      def text_to_bits(text)
        text.bytes.flat_map { |byte| (0...8).map { |i| (byte >> (7 - i)) & 1 } }
      end

      def bits_to_text(bits)
        bytes = bits.each_slice(8).map do |chunk|
          chunk = chunk + [0] * (8 - chunk.length) if chunk.length < 8
          chunk.reduce(0) { |acc, b| (acc << 1) | b }
        end
        bytes.pack("C*").force_encoding("UTF-8")
      end

      # --- one superdense pair, with optional physical noise ---------------

      # Transmit one 2-bit symbol through a fresh Bell pair. With probability
      # `flip_prob` the traveling (Alice) qubit suffers a random Pauli error in
      # the semiconductor channel.
      def send_symbol(bit_hi, bit_lo, flip_prob:, rng:)
        pair = Qubit2.prepare_bell
        pair.encode(bit_hi, bit_lo)
        if rng.rand < flip_prob
          case rng.rand(3)
          when 0 then pair.x_a
          when 1 then pair.y_a
          else pair.z_a
          end
        end
        pair.bell_decode
        pair.readout_bits
      end

      # Repetition-coded symbol: send `redundancy` copies, majority-vote each bit.
      def send_symbol_protected(bit_hi, bit_lo, flip_prob:, rng:, redundancy: 3)
        his = []
        los = []
        redundancy.times do
          h, l = send_symbol(bit_hi, bit_lo, flip_prob: flip_prob, rng: rng)
          his << h
          los << l
        end
        [majority(his), majority(los)]
      end

      def majority(bits)
        bits.sum >= (bits.length / 2.0) ? 1 : 0
      end

      # --- full message transmission ---------------------------------------

      # Transmit a text message across the space telegraph.
      #
      #   material / temp_k  -> semiconductor bit-flip probability
      #   redundancy         -> repetition-code strength
      #
      # Returns the recovered text plus channel statistics (BER, fidelity), with
      # the fidelity stream stabilised by Bada::ErrorCorrection (the complex
      # rotational-body integrable corrector).
      def transmit(message, material: "GaAs", temp_k: 4.0, redundancy: 3, seed: 7)
        rng = Random.new(seed)
        flip = Semiconductor.thermal_flip(material, temp_k)
        # give the demo a visible, correctable error rate even in a cold dot
        flip = [flip, 0.04].max

        bits = text_to_bits(message)
        bits += [0] if bits.length.odd?
        recovered = []
        symbol_fidelity = []

        bits.each_slice(2) do |hi, lo|
          rh, rl = send_symbol_protected(hi, lo, flip_prob: flip, rng: rng, redundancy: redundancy)
          recovered << rh << rl
          symbol_fidelity << ((rh == hi ? 1.0 : 0.0) + (rl == lo ? 1.0 : 0.0)) / 2.0
        end

        errors = bits.each_index.count { |i| bits[i] != recovered[i] }
        ber = errors.to_f / bits.length
        corrected = Bada::ErrorCorrection.correct(symbol_fidelity)

        {
          message: message,
          recovered: bits_to_text(recovered),
          bits: bits.length,
          pairs_used: (bits.length / 2) * redundancy,
          flip_prob: flip,
          bit_errors: errors,
          ber: ber,
          raw_fidelity: symbol_fidelity.empty? ? 1.0 : symbol_fidelity.sum / symbol_fidelity.length,
          certified_fidelity: corrected[:value],
          fidelity_residual: corrected[:residual],
          lossless: recovered == bits
        }
      end
    end
  end
end
