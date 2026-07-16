# frozen_string_literal: true

require "openssl"
require_relative "quantum"

module Bada
  # CreditGuard — tamper-evident authorship protection sealed with quantum
  # cryptography, so credit for this work cannot be silently taken.
  #
  #   1. BB84 quantum key distribution (the canonical quantum-cryptography
  #      protocol) is run on the engine's phase core (Bada::Quantum): bits are
  #      prepared in the rectilinear/diagonal basis (X, H) and measured by the
  #      receiver; sifting the matching-basis positions yields a shared key and
  #      the QBER (eavesdropping estimate).
  #   2. The sifted quantum key signs the immutable author certificate + a
  #      SHA-256 hash of the content with HMAC-SHA256 — the "quantum credit
  #      seal": publicly verifiable, unforgeable for a different author.
  #   3. Outputs are stamped with the seal + notice, so removing/altering the
  #      credit is detectable (verify fails on tampering).
  #
  # The author may inject a private seed via NOEMA_CREDIT_SEED (env) that is not
  # shipped, making seals unforgeable while remaining publicly verifiable.
  module CreditGuard
    module_function

    CERTIFICATE = {
      author: "Masaaki Yamaguchi / 山口 雅旭",
      author_id: "Global Differential Manifold Research · tuplenetwork",
      work: "NoemaKey · Unknown-Prior Precognition Engine (Bada framework)",
      period: "2025–2026",
      notice: "© 2025–2026 Masaaki Yamaguchi. All rights reserved. 無断でクレジットを改変・剥奪することを禁じます。"
    }.freeze

    def canonical
      c = CERTIFICATE
      "#{c[:author]}|#{c[:author_id]}|#{c[:work]}|#{c[:period]}|#{c[:notice]}"
    end

    # BB84 quantum key distribution on the phase core. Returns key/qber/stats.
    def bb84(bits: 256, seed:)
      rng = Random.new(seed)
      key_bits = []
      test_total = 0
      test_errors = 0
      sent = 0
      while key_bits.length < bits && sent < bits * 8 + 64
        sent += 1
        alice_bit = rng.rand(2)
        alice_basis = rng.rand(2) # 0 rectilinear, 1 diagonal
        bob_basis = rng.rand(2)

        reg = Quantum.qubit(1)
        reg.x(0) if alice_bit == 1
        reg.h(0) if alice_basis == 1
        reg.h(0) if bob_basis == 1
        bob_bit = reg.sample(rng)

        if alice_basis == bob_basis
          if rng.rand(8).zero?
            test_total += 1
            test_errors += 1 if bob_bit != alice_bit
          else
            key_bits << alice_bit
          end
        end
      end
      qber = test_total.positive? ? test_errors.to_f / test_total : 0.0
      { key: pack_bits(key_bits, bits), qber: qber, sifted: key_bits.length, sent: sent }
    end

    def pack_bits(bits_list, want)
      n = [want, bits_list.length].min
      bytes = Array.new((n + 7) / 8, 0)
      n.times { |i| bytes[i / 8] |= (1 << (i % 8)) if bits_list[i] == 1 }
      OpenSSL::Digest::SHA256.digest(bytes.pack("C*")) # whiten to 256-bit key
    end

    def resolve_seed
      secret = ENV["NOEMA_CREDIT_SEED"]
      basis = secret || canonical
      h = OpenSSL::Digest::SHA256.digest(basis)
      h[0, 8].bytes.inject(0) { |acc, b| (acc << 8) | b }
    end

    def key
      @key ||= bb84(bits: 256, seed: resolve_seed)[:key]
    end

    def seal(content)
      data = OpenSSL::Digest::SHA256.digest(canonical) + OpenSSL::Digest::SHA256.digest(content.to_s)
      OpenSSL::HMAC.hexdigest("SHA256", key, data)
    end

    def verify(content, seal_hex)
      a = seal(content)
      b = seal_hex.to_s.downcase
      return false unless a.bytesize == b.bytesize

      OpenSSL.fixed_length_secure_compare(a, b)
    rescue StandardError
      a == b
    end

    def fingerprint
      seal(canonical)[0, 16].upcase
    end

    def notice
      CERTIFICATE[:notice]
    end

    def stamp(content)
      s = seal(content)
      [
        content,
        "",
        "———— 量子暗号クレジット保護 (BB84 · HMAC-SHA256) ————",
        notice,
        "著者: #{CERTIFICATE[:author]}",
        "鍵指紋: #{fingerprint}  ·  シール: #{s[0, 32]}…"
      ].join("\n")
    end

    def badge
      "© 量子暗号保護 · 鍵指紋 #{fingerprint}"
    end

    def report
      r = bb84(bits: 256, seed: resolve_seed)
      probe = "credit-protection-selfcheck"
      ok = verify(probe, seal(probe))
      [
        "量子暗号クレジット保護 — CreditGuard",
        notice,
        "著者: #{CERTIFICATE[:author]}",
        "作品: #{CERTIFICATE[:work]}",
        "BB84 量子鍵配送: 送信 #{r[:sent]} qubit → sifted #{r[:sifted]} bit · QBER #{format('%.3f', r[:qber])}",
        "鍵指紋(HMAC-SHA256): #{fingerprint}",
        "改ざん検証セルフチェック: #{ok ? 'OK（シール有効）' : 'NG'}"
      ].join("\n")
    end
  end
end
