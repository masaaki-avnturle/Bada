# encoding: UTF-8
# frozen_string_literal: true

require "minitest/autorun"
require "tmpdir"
require_relative "../lib/bada"

class TestQuantumCrypto < Minitest::Test
  QC = Bada::QuantumCrypto

  def test_encrypt_decrypt_round_trip
    pt = "USB上の機密データ — quantum locked.\n\x00\x01\x02binary".b
    blob = QC.encrypt(pt, "correct-pass")
    assert blob.start_with?(QC::MAGIC)
    assert_equal pt, QC.decrypt(blob, "correct-pass")
  end

  def test_wrong_passphrase_fails_cleanly
    blob = QC.encrypt("secret".b, "right")
    assert_raises(QC::DecryptError) { QC.decrypt(blob, "wrong") }
  end

  def test_tamper_is_detected
    blob = QC.encrypt("secret data here".b, "pw").dup
    blob[-1] = (blob.getbyte(-1) ^ 0xFF).chr # flip a ciphertext byte
    assert_raises(QC::DecryptError) { QC.decrypt(blob, "pw") }
  end

  def test_bb84_is_deterministic_from_passphrase
    a = QC.bb84("same-seed")[:sifted]
    b = QC.bb84("same-seed")[:sifted]
    assert_equal a, b
    assert_equal QC::SIFTED_BITS, a.length
    refute_equal a, QC.bb84("different-seed")[:sifted]
  end

  def test_qkd_detects_eavesdropper
    r = QC.qkd_channel_report("passphrase")
    assert_operator r[:clean_qber], :<=, 0.11
    assert_operator r[:eavesdrop_qber], :>, 0.11
    assert r[:eavesdropper_detected]
    assert r[:secure]
  end

  def test_diagram_key_material_changes_key
    Dir.mktmpdir do |d|
      dia = File.join(d, "trefoil.txt")
      File.write(dia, "1 0 1 2 3 1\n2 2 3 4 5 1\n3 4 5 0 1 1\n")
      fp_plain = QC.key_fingerprint("pw")
      fp_dia = QC.key_fingerprint("pw", diagram: dia)
      refute_equal fp_plain, fp_dia, "the Jones diagram must change the key"
      # and a file encrypted WITH the diagram needs the diagram to decrypt
      blob = QC.encrypt("x".b, "pw", diagram: dia)
      assert_raises(QC::DecryptError) { QC.decrypt(blob, "pw") }
      assert_equal "x".b, QC.decrypt(blob, "pw", diagram: dia)
    end
  end

  def test_usb_lock_unlock_cycle
    Dir.mktmpdir do |usb|
      Dir.mkdir(File.join(usb, "docs"))
      File.write(File.join(usb, "a.txt"), "alpha")
      File.binwrite(File.join(usb, "docs", "b.bin"), "\x00\xFF\x10bravo".b)

      locked = QC.lock_usb(usb, "pw", remove_original: true)
      assert_equal 2, locked.count { |r| r[:ok] }
      # plaintext gone, .qenc present
      refute File.exist?(File.join(usb, "a.txt"))
      assert File.exist?(File.join(usb, "a.txt#{QC::ENC_SUFFIX}"))

      unlocked = QC.unlock_usb(usb, "pw", remove_encrypted: true)
      assert_equal 2, unlocked.count { |r| r[:ok] }
      assert_equal "alpha", File.read(File.join(usb, "a.txt"))
      assert_equal "\x00\xFF\x10bravo".b, File.binread(File.join(usb, "docs", "b.bin"))
    end
  end

  def test_kauffman_bracket_unknot_is_one
    # a diagram with zero crossings evaluates to the empty-state bracket 1.0
    assert_equal 1.0, QC.kauffman_bracket([], 1.0)
  end

  def test_check_digit_is_stable_and_verifiable
    a = QC.check_digit("pw")
    b = QC.check_digit("pw")
    assert_equal a[:code], b[:code]
    assert_match(/\A[0-9a-f]{6}-\d{2}-\d\z/, a[:code])
    assert QC.verify_check_digit("pw", a[:code])
    assert QC.verify_check_digit("pw", a[:code].upcase) # case-insensitive
    refute QC.verify_check_digit("different", a[:code])
  end

  def test_check_digit_changes_with_diagram
    Dir.mktmpdir do |d|
      dia = File.join(d, "k.txt")
      File.write(dia, "1 0 1 2 3 1\n2 2 3 4 5 1\n3 4 5 0 1 1\n")
      refute_equal QC.check_digit("pw")[:code], QC.check_digit("pw", diagram: dia)[:code]
      assert QC.jones_check_digit(dia)
      assert_nil QC.jones_check_digit(File.join(d, "missing.txt"))
    end
  end

  def test_wrong_passphrase_reports_check_digit_mismatch
    blob = QC.encrypt("data".b, "right")
    err = assert_raises(QC::DecryptError) { QC.decrypt(blob, "wrong") }
    assert_match(/チェックデジット/, err.message)
  end

  def test_jones_polynomial_only_keyfile
    Dir.mktmpdir do |d|
      trefoil = File.join(d, "trefoil.txt")
      fig8 = File.join(d, "fig8.txt")
      File.write(trefoil, "1 0 1 2 3 1\n2 2 3 4 5 1\n3 4 5 0 1 1\n")
      File.write(fig8, "1 0 1 2 3 1\n2 2 3 4 5 -1\n3 4 5 6 7 1\n4 6 7 0 1 -1\n")

      # lock with the knot's Jones polynomial alone (no passphrase)
      blob = QC.encrypt("解読 with the knot".b, "", diagram: trefoil)
      # the correct knot decrypts (解読)
      assert_equal "解読 with the knot".b, QC.decrypt(blob, "", diagram: trefoil)
      # a different knot does not
      assert_raises(QC::DecryptError) { QC.decrypt(blob, "", diagram: fig8) }
      # and neither does no key at all
      assert_raises(ArgumentError) { QC.decrypt(blob, "") }
    end
  end

  def test_requires_passphrase_or_diagram
    assert_raises(ArgumentError) { QC.encrypt("x".b, "") }
  end

  def test_luhn_and_mod97_are_self_consistent
    assert_equal QC.luhn_digit("123456"), QC.luhn_digit("123456")
    assert (0..9).include?(QC.luhn_digit("7890"))
    assert_match(/\A\d{2}\z/, QC.mod97_digits("123456789"))
  end
end
