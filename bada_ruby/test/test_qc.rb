# frozen_string_literal: true

require "minitest/autorun"
require "tmpdir"
require_relative "../lib/bada"

class TestQCLogic < Minitest::Test
  L = Bada::QC::Logic

  def test_nand_truth_table
    assert_equal L::VDD, L.nand(0, 0)
    assert_equal L::VDD, L.nand(1, 0)
    assert_equal L::VDD, L.nand(0, 1)
    assert_equal 0.0,     L.nand(1, 1)
  end

  def test_derived_gates
    assert L.high?(L.and_(1, 1))
    refute L.high?(L.and_(1, 0))
    assert L.high?(L.or_(1, 0))
    assert L.high?(L.xor_(1, 0))
    refute L.high?(L.xor_(1, 1))
  end

  def test_decoder_is_one_hot_and_correct
    (0...16).each do |v|
      out = L.decode(v, 4)
      highs = out.each_index.select { |i| L.high?(out[i]) }
      assert_equal [v], highs, "decoder must fire exactly line #{v}"
      assert_equal v, L.decode_index(v, 4)
    end
  end
end

class TestQCDiskMemory < Minitest::Test
  def test_roundtrip_and_persistence
    Dir.mktmpdir do |dir|
      path = File.join(dir, "m.bin")
      mem = Bada::QC::DiskMemory.new(path: path, words: 8)
      mem.write(0, 3.5)
      mem.write_amp(2, 0, Complex(0.6, -0.8))
      mem.close
      # reopen from disk — data must persist (it really lived on the HDD)
      mem2 = Bada::QC::DiskMemory.new(path: path, words: 8)
      assert_in_delta 3.5, mem2.read(0), 1e-12
      amp = mem2.read_amp(2, 0)
      assert_in_delta 0.6, amp.real, 1e-12
      assert_in_delta(-0.8, amp.imaginary, 1e-12)
      mem2.close
      assert File.size(path) >= 8 * Bada::QC::DiskMemory::WORD
    end
  end
end

class TestQCMachine < Minitest::Test
  def test_bell_state
    m = Bada::QC::Machine.bell
    p = m.probabilities
    assert_in_delta 0.5, p[0], 1e-9
    assert_in_delta 0.0, p[1], 1e-9
    assert_in_delta 0.0, p[2], 1e-9
    assert_in_delta 0.5, p[3], 1e-9
    m.close
  end

  def test_ghz_state
    m = Bada::QC::Machine.ghz
    p = m.probabilities
    assert_in_delta 0.5, p[0], 1e-9   # |000>
    assert_in_delta 0.5, p[7], 1e-9   # |111>
    (1..6).each { |i| assert_in_delta 0.0, p[i], 1e-9 }
    m.close
  end

  def test_x_gate_flips
    m = Bada::QC::Machine.new(n_qubits: 1).load("X 0\nHALT\n").run
    assert_in_delta 1.0, m.probabilities[1], 1e-9
    m.close
  end

  def test_rz_is_phase_only
    m = Bada::QC::Machine.new(n_qubits: 1).load("H 0\nRZ 0 1.5708\nHALT\n").run
    # RZ keeps measurement probabilities of an X-basis-neutral state at 0.5/0.5
    p = m.probabilities
    assert_in_delta 0.5, p[0], 1e-6
    assert_in_delta 0.5, p[1], 1e-6
    m.close
  end

  def test_measure_collapses_and_records
    m = Bada::QC::Machine.new(n_qubits: 1, seed: 1).load("H 0\nMEASURE 0\nHALT\n").run
    bit = m.classical_bits[0]
    assert_includes [0, 1], bit
    # after collapse the state is a definite basis state
    p = m.probabilities
    assert_in_delta 1.0, p[bit], 1e-9
    m.close
  end

  def test_program_and_state_share_disk_memory
    m = Bada::QC::Machine.bell
    assert m.disk_bytes.positive?
    # von Neumann: header + program records + state amplitudes in one image
    expected = (Bada::QC::CPU::HEADER + 3 * Bada::QC::ISA::RECORD_WORDS + 2 * 4) *
               Bada::QC::DiskMemory::WORD
    assert_equal expected, m.disk_bytes
    m.close
  end

  def test_monitor_projection_contains_datapath_and_circuit
    m = Bada::QC::Machine.bell
    out = m.monitor
    assert_includes out, "DISK  MEMORY"
    assert_includes out, "SEMICONDUCTOR"
    assert_includes out, "q0"
    assert_includes out, "[H]"
    m.close
  end

  def test_verilog_semiconductor_source
    m = Bada::QC::Machine.bell
    v = m.verilog
    assert_includes v, "module nand2"          # the MOSFET primitive
    assert_includes v, "module opcode_decoder" # decoder from NAND
    assert_includes v, "module bada_qc_control"
    assert_includes v, "rom_op[0]=4'd1"        # H opcode baked into ROM
    m.close
  end
end
