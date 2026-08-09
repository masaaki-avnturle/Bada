# frozen_string_literal: true

require "minitest/autorun"
require_relative "../lib/bada"

class TestUsbResume < Minitest::Test
  U = Bada::UsbResume

  def test_base_n_roundtrip
    # to_base / from_base must be inverse for every byte in a few bases.
    [2, 8, 10, 16].each do |base|
      w = U.byte_width(base)
      [0, 1, 42, 127, 200, 255].each do |v|
        assert_equal v, U.from_base(U.to_base(v, base, width: w), base),
                     "base-#{base} roundtrip failed for #{v}"
      end
    end
  end

  def test_recover_byte_from_drifted_reads
    # Many contact-faulted reads of the same byte must recover the true value
    # via the complex-rotation-body integrable corrector.
    truth = 0x40
    samples = (0...15).map { |t| U.drift([truth], base: 16, p: 0.4, seed: 3, trial: t).first }
    r = U.recover_byte(samples)
    assert_equal truth, r[:value]
    assert_equal 15, r[:samples]
  end

  def test_recover_descriptor_reduces_bit_errors
    # The corrected descriptor must have no more bit errors than a raw noisy
    # read, and should recover the checksum on a clean-enough channel.
    dev = U.synthetic_fleet.last
    rec = U.recover_descriptor(dev.descriptor, base: 16, reads: 11, p: 0.3, seed: 7)
    assert rec[:bit_errors_out] <= rec[:bit_errors_in],
           "correction increased bit errors (#{rec[:bit_errors_in]} -> #{rec[:bit_errors_out]})"
    assert_equal dev.descriptor.length, rec[:corrected].length
    assert rec[:bytes_recovered] >= rec[:bytes_total] - 1,
           "recovered only #{rec[:bytes_recovered]}/#{rec[:bytes_total]} bytes"
  end

  def test_per_digit_recovery_handles_every_base
    # Per-digit base-n correction must fully recover the descriptor for coarse
    # and fine bases alike (this is the "fix the n進数のズレ" guarantee).
    dev = U.synthetic_fleet.last
    [2, 8, 10, 16].each do |base|
      rec = U.recover_descriptor_adaptive(dev.descriptor, base: base, reads: 9, p: 0.35, seed: 7)
      assert rec[:checksum_ok], "base-#{base} failed to checksum (#{rec[:bytes_recovered]}/#{rec[:bytes_total]})"
      assert_equal 0, rec[:bit_errors_out], "base-#{base} left #{rec[:bit_errors_out]} bit errors"
    end
  end

  def test_scan_returns_devices
    devices = U.scan
    refute_empty devices
    assert devices.all? { |d| d.is_a?(U::Device) }
  end

  def test_resume_brings_faulted_device_to_resumed
    faulted = U.synthetic_fleet.last
    assert_equal "UNAUTHORIZED", faulted.status
    result = U.resume(faulted, reads: 11, p: 0.3)
    assert result[:resumed], "device was not resumed: #{result[:steps].inspect}"
    assert_equal "RESUMED", result[:after]
    assert_equal 1, faulted.authorized
    assert faulted.bound
    refute result[:applied] # simulation by default
  end

  def test_resume_conserves_entropy_invariant
    # The integrable-system certificate: Ξ conserved on the rotation orbit.
    faulted = U.synthetic_fleet.last
    result = U.resume(faulted)
    assert result[:certificate][:conserved]
  end

  def test_resume_all_skips_healthy_devices
    results = U.resume_all(U.synthetic_fleet)
    skipped = results.count { |r| r[:skipped] }
    assert skipped >= 2, "healthy devices should be skipped"
    assert(results.any? { |r| r[:resumed] && !r[:skipped] })
  end

  def test_no_sysfs_writes_in_simulation
    # Simulation must never touch the filesystem; resume returns applied=false.
    faulted = U.synthetic_fleet.last
    faulted.sysfs = "/sys/bus/usb/devices/does-not-exist"
    result = U.resume(faulted, apply: false)
    refute result[:applied]
    assert result[:resumed]
  end
end
