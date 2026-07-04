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
end
