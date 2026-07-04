# frozen_string_literal: true

require "openssl"
require "securerandom"
require "digest"

module Bada
  # QuantumCrypto — the Bada quantum-cryptography file vault for a USB stick.
  #
  #   ┌───────────────────────────────────────────────────────────────────┐
  #   │ SCOPE / 安全に関する注意                                            │
  #   │ This is a PERSONAL file vault. It encrypts (locks) your OWN files  │
  #   │ on a USB stick and decrypts (unlocks / 解く) files that THIS tool  │
  #   │ encrypted, using the passphrase YOU hold. It does NOT and can NOT  │
  #   │ break BitLocker / LUKS / VeraCrypt / hardware-encrypted drives, or │
  #   │ recover unknown keys. "解読" here = decrypt-with-your-own-key.      │
  #   └───────────────────────────────────────────────────────────────────┘
  #
  # It follows the Yamaguchi / TupleSpace framework's own quantum-crypto scheme
  # (cf. omega_jones_crypto_pkg):
  #
  #   1. BB84 quantum key distribution (QKD) is *simulated* from the passphrase
  #      to produce a sifted key + let us measure the QBER, so an eavesdropper
  #      on the "quantum channel" is detectable (Bada::QuantumCrypto.bb84).
  #   2. A Jones / Kauffman-bracket knot invariant optionally adds key material
  #      (kauffman_key), exactly as jones_key.c derives a key from a diagram.
  #   3. The BB84 sifted bits + Kauffman samples + passphrase are stretched with
  #      PBKDF2-HMAC-SHA256 into a 256-bit key, and the file is sealed with
  #      authenticated AES-256-GCM. A wrong passphrase fails the GCM tag, so
  #      "unlock" cleanly reports failure instead of emitting garbage.
  #
  # Everything is pure Ruby stdlib (openssl), so it runs anywhere Bada runs.
  module QuantumCrypto
    module_function

    MAGIC = "BQC2"          # Bada Quantum Crypto, format v2 (with KCV)
    ENC_SUFFIX = ".qenc"
    PBKDF2_ITERS = 200_000
    KEY_LEN = 32
    SIFTED_BITS = 256       # target length of the BB84 sifted key
    KCV_LEN = 3             # embedded Key Check Value (check-digit source)

    # ---- BB84 quantum key distribution (simulation) ---------------------
    #
    # Deterministic from a seed so both lock and unlock derive the same sifted
    # key. Returns the sifted bits (as a binary string) and the QBER measured
    # against an optional simulated eavesdropper (Eve).
    #
    #   * Alice picks random bits and random bases (rectilinear/diagonal).
    #   * Bob picks random bases and measures.
    #   * They keep only positions where the bases match (sifting).
    #   * If Eve intercept-resends, mismatched bases corrupt ~25% of sifted
    #     bits -> a nonzero QBER reveals her.
    def bb84(seed, length: SIFTED_BITS, eavesdrop: false)
      rng = seeded_rng(seed)
      sifted = +""
      errors = 0
      total = 0
      # generate until we have `length` sifted bits
      while sifted.length < length
        a_bit  = rng.rand(2)
        a_base = rng.rand(2)
        b_base = rng.rand(2)

        measured = a_bit
        if eavesdrop
          e_base = rng.rand(2)
          # Eve measures in her basis; if it differs from Alice's she randomizes
          measured = rng.rand(2) if e_base != a_base
        end
        # Bob measures; if his basis differs from the (possibly Eve-disturbed)
        # sender basis, his result is random.
        b_bit = (b_base == a_base) ? measured : rng.rand(2)

        next unless a_base == b_base # sift: keep only matching-basis positions
        total += 1
        errors += 1 if b_bit != a_bit
        sifted << a_bit.to_s
      end
      qber = total.zero? ? 0.0 : errors.to_f / total
      { sifted: sifted[0, length], qber: qber, eavesdrop: eavesdrop }
    end

    # A small deterministic PRNG (SplitMix64) seeded by a string, so BB84 is
    # reproducible from the passphrase across machines/runs.
    def seeded_rng(seed)
      h = Digest::SHA256.digest(seed.to_s)
      state = h[0, 8].unpack1("Q>")
      Random.new(state)
    end

    # ---- Jones / Kauffman-bracket key material (optional) ----------------
    #
    # Port of jones_key.c: evaluate the Kauffman bracket of a knot diagram at
    # several A values; the numeric samples become extra key material.
    # Diagram format (per line): "id e0 e1 e2 e3 sign".
    def kauffman_key(diagram_path)
      crossings = load_diagram(diagram_path)
      return "" if crossings.empty?
      [0.8, 1.0, 1.2, 1.5, 2.0].map { |a| kauffman_bracket(crossings, a) }
        .pack("E*")
    end

    def load_diagram(path)
      out = []
      File.foreach(path) do |line|
        s = line.strip
        next if s.empty? || s.start_with?("#")
        parts = s.split(/\s+/).map(&:to_i)
        next if parts.length < 6
        out << { e: parts[1, 4], sign: parts[5] >= 0 ? 1 : -1 }
      end
      out
    rescue SystemCallError
      []
    end

    # State-sum Kauffman bracket over 2^n smoothings (n = number of crossings).
    def kauffman_bracket(cross, a)
      n = cross.length
      return 1.0 if n.zero?
      max_lbl = cross.flat_map { |c| c[:e] }.max
      u = max_lbl + 1
      d = -(a * a) - 1.0 / (a * a)
      sum = 0.0
      (0...(1 << n)).each do |s|
        parent = Array.new(u, -1)
        a_cnt = 0
        b_cnt = 0
        cross.each_with_index do |c, i|
          e = c[:e]
          if (s >> i) & 1 == 0
            uf_union(parent, e[0], e[1]); uf_union(parent, e[2], e[3]); a_cnt += 1
          else
            uf_union(parent, e[1], e[2]); uf_union(parent, e[3], e[0]); b_cnt += 1
          end
        end
        loops = (0...u).map { |lbl| uf_find(parent, lbl) }.uniq.length
        sum += (a**(a_cnt - b_cnt)) * (d**(loops.positive? ? loops - 1 : 0))
      end
      sum
    end

    def uf_find(p, a)
      a = p[a] while p[a] >= 0 # follow parents; a root stores negative -size
      a
    end

    def uf_union(p, a, b)
      a = uf_find(p, a); b = uf_find(p, b)
      return if a == b
      if p[a] < p[b] then p[a] += p[b]; p[b] = a else p[b] += p[a]; p[a] = b end
    end

    # ---- key derivation --------------------------------------------------

    # The QKD seed: the passphrase if given, otherwise the Jones polynomial of
    # the knot diagram alone (keyfile mode — the diagram *is* the key). At least
    # one of the two must identify the key.
    def key_seed(passphrase, diagram)
      return passphrase.to_s unless passphrase.to_s.empty?
      if diagram && File.file?(diagram.to_s)
        jk = kauffman_key(diagram)
        return "JONES:#{Digest::SHA256.hexdigest(jk)}" unless jk.empty?
      end
      raise ArgumentError, "パスフレーズまたは有効な結び目図（Jones多項式）が必要です"
    end

    # Derive the 256-bit AES key from (passphrase and/or the Jones polynomial) +
    # BB84 sifted bits, stretched with PBKDF2-HMAC-SHA256 over `salt`.
    #
    # Keyed three ways:
    #   * passphrase only            (BB84 seeded by the passphrase)
    #   * Jones polynomial only      (the knot diagram file is the keyfile)
    #   * passphrase + Jones polynomial (both required to decrypt)
    def derive_key(passphrase, salt, diagram: nil)
      seed = key_seed(passphrase, diagram)
      qkd = bb84(seed)[:sifted]
      material = +"#{passphrase}\x00#{qkd}"
      material << "\x00" << kauffman_key(diagram) if diagram && File.file?(diagram.to_s)
      OpenSSL::PKCS5.pbkdf2_hmac(material, salt, PBKDF2_ITERS, KEY_LEN, OpenSSL::Digest::SHA256.new)
    end

    def key_fingerprint(passphrase, diagram: nil)
      # a stable, non-secret fingerprint of the key (fixed salt) for display
      k = derive_key(passphrase, "BQC-fingerprint", diagram: diagram)
      Digest::SHA256.hexdigest(k)[0, 16]
    end

    # ---- check digit / Key Check Value (KCV) ----------------------------
    #
    # A short, non-reversible verification value. It lets you confirm that a
    # passphrase (+ knot diagram) is the RIGHT one BEFORE running a long unlock,
    # and detects a corrupted key/diagram — WITHOUT revealing the key and
    # WITHOUT any ability to recover an unknown key. This is the standard
    # "Key Check Value" idea, here rendered as human-readable check digits.

    # KCV bytes from a concrete AES key (used inside the file header).
    def kcv_bytes(key)
      Digest::SHA256.digest(key.b + "\x00KCV")[0, KCV_LEN]
    end

    # Luhn (mod-10) check digit over a decimal string.
    def luhn_digit(num)
      sum = 0
      alt = true
      num.to_s.reverse.each_char do |c|
        d = c.to_i
        if alt
          d *= 2
          d -= 9 if d > 9
        end
        sum += d
        alt = !alt
      end
      (10 - (sum % 10)) % 10
    end

    # ISO 7064 MOD 97-10 two-digit check over a decimal string.
    def mod97_digits(num)
      r = 0
      num.to_s.each_char { |c| r = (r * 10 + c.to_i) % 97 }
      format("%02d", (r * 100) % 97)
    end

    # Human-verifiable check code for a passphrase (+ diagram), independent of
    # any file (fixed salt). Returns { kcv:, luhn:, mod97:, code: }.
    def check_digit(passphrase, diagram: nil)
      key = derive_key(passphrase, "BQC-KCV", diagram: diagram)
      b = kcv_bytes(key)
      hex = b.unpack1("H*")           # 6 hex chars
      dec = b.unpack1("H*").to_i(16).to_s
      { kcv: hex, luhn: luhn_digit(dec), mod97: mod97_digits(dec),
        code: "#{hex}-#{mod97_digits(dec)}-#{luhn_digit(dec)}" }
    end

    # Verify a passphrase (+ diagram) against a previously shown check code.
    def verify_check_digit(passphrase, code, diagram: nil)
      check_digit(passphrase, diagram: diagram)[:code].casecmp?(code.to_s.strip)
    end

    # Check digit of the Jones polynomial (Kauffman bracket) of a knot diagram
    # alone — verifies the diagram key file's integrity.
    def jones_check_digit(diagram)
      material = kauffman_key(diagram)
      return nil if material.empty?
      b = Digest::SHA256.digest(material)[0, KCV_LEN]
      dec = b.unpack1("H*").to_i(16).to_s
      { kcv: b.unpack1("H*"), luhn: luhn_digit(dec), mod97: mod97_digits(dec) }
    end

    # ---- authenticated encryption (lock / unlock) ------------------------

    # Encrypt (lock) a file. Output layout:
    #   MAGIC(4) | kcv(3) | salt_len(1) | salt | iv(12) | tag(16) | ciphertext
    def encrypt(plaintext, passphrase, diagram: nil)
      salt = SecureRandom.random_bytes(16)
      key = derive_key(passphrase, salt, diagram: diagram)
      kcv = kcv_bytes(key)
      cipher = OpenSSL::Cipher.new("aes-256-gcm").encrypt
      cipher.key = key
      iv = cipher.random_iv
      cipher.auth_data = MAGIC + kcv
      ct = cipher.update(plaintext.b) + cipher.final
      tag = cipher.auth_tag
      "#{MAGIC}#{kcv}#{[salt.bytesize].pack('C')}#{salt}#{iv}#{tag}#{ct}".b
    end

    # Decrypt (unlock / 解く). Raises on wrong passphrase or tampering. The
    # embedded KCV (check digit) is verified first, so a wrong passphrase is
    # reported as a check-digit mismatch before the AES-GCM step.
    def decrypt(blob, passphrase, diagram: nil)
      blob = blob.b
      raise ArgumentError, "not a Bada quantum-crypto file (bad magic)" unless blob[0, 4] == MAGIC
      i = 4
      kcv = blob[i, KCV_LEN]; i += KCV_LEN
      salt_len = blob[i].unpack1("C"); i += 1
      salt = blob[i, salt_len]; i += salt_len
      iv = blob[i, 12]; i += 12
      tag = blob[i, 16]; i += 16
      ct = blob[i..] || ""
      key = derive_key(passphrase, salt, diagram: diagram)
      unless kcv_bytes(key) == kcv
        raise DecryptError, "解読失敗: チェックデジット不一致（パスフレーズ/結び目図が違います）"
      end
      cipher = OpenSSL::Cipher.new("aes-256-gcm").decrypt
      cipher.key = key
      cipher.iv = iv
      cipher.auth_tag = tag
      cipher.auth_data = MAGIC + kcv
      cipher.update(ct) + cipher.final
    rescue OpenSSL::Cipher::CipherError
      raise DecryptError, "解読失敗: パスフレーズが違うか、ファイルが破損/改竄されています"
    end

    class DecryptError < StandardError; end

    def encrypt_file(in_path, passphrase, out_path: nil, diagram: nil)
      out_path ||= in_path + ENC_SUFFIX
      File.binwrite(out_path, encrypt(File.binread(in_path), passphrase, diagram: diagram))
      out_path
    end

    def decrypt_file(in_path, passphrase, out_path: nil, diagram: nil)
      out_path ||= in_path.end_with?(ENC_SUFFIX) ? in_path[0...-ENC_SUFFIX.length] : in_path + ".dec"
      File.binwrite(out_path, decrypt(File.binread(in_path), passphrase, diagram: diagram))
      out_path
    end

    # ---- USB stick: lock / unlock a whole mount path ---------------------

    # Lock every regular file under `path` (a USB mount), writing <name>.qenc
    # and (by default) removing the plaintext original.
    def lock_usb(path, passphrase, diagram: nil, remove_original: false)
      results = []
      each_target(path, encrypted: false) do |f|
        out = encrypt_file(f, passphrase, diagram: diagram)
        File.delete(f) if remove_original
        results << { file: f, output: out, ok: true }
      rescue StandardError => e
        results << { file: f, error: e.message, ok: false }
      end
      results
    end

    # Unlock (解く) every <name>.qenc under `path`, restoring the plaintext.
    # Only files this tool produced, and only with the correct passphrase.
    def unlock_usb(path, passphrase, diagram: nil, remove_encrypted: false)
      results = []
      each_target(path, encrypted: true) do |f|
        out = decrypt_file(f, passphrase, diagram: diagram)
        File.delete(f) if remove_encrypted
        results << { file: f, output: out, ok: true }
      rescue DecryptError => e
        results << { file: f, error: e.message, ok: false }
      rescue StandardError => e
        results << { file: f, error: e.message, ok: false }
      end
      results
    end

    def each_target(path, encrypted:)
      if File.file?(path)
        yield path
        return
      end
      Dir.glob(File.join(path, "**", "*")).sort.each do |f|
        next unless File.file?(f)
        is_enc = f.end_with?(ENC_SUFFIX)
        next if encrypted != is_enc
        yield f
      end
    end

    # ---- eavesdropper detection demo ------------------------------------
    #
    # Show that the QKD channel detects an eavesdropper: a clean channel sifts
    # to QBER≈0, while intercept-resend pushes QBER toward the ~25% BB84 bound.
    def qkd_channel_report(passphrase, length: SIFTED_BITS)
      clean = bb84(passphrase, length: length, eavesdrop: false)
      tapped = bb84(passphrase, length: length, eavesdrop: true)
      {
        clean_qber: clean[:qber],
        eavesdrop_qber: tapped[:qber],
        # standard BB84 rule of thumb: reject the key if QBER exceeds ~11%
        eavesdropper_detected: tapped[:qber] > 0.11,
        secure: clean[:qber] <= 0.11
      }
    end
  end
end
