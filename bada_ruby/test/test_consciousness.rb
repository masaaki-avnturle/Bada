# encoding: UTF-8
# frozen_string_literal: true

require "minitest/autorun"
require "stringio"
require "fileutils"
require_relative "../lib/bada"

class TestConsciousness < Minitest::Test
  def out(src) = Bada::Lang.run(src, out: StringIO.new).output

  def test_microtubule_coherence_in_range
    src = <<~BADA
      import "std/microtubule.bada"
      arr mt <- MT.make(8)
      print str(MT.coherence(mt))
    BADA
    c = out(src).first.to_f
    assert_operator c, :>=, 0.0
    assert_operator c, :<=, 1.0001
  end

  def test_microtubule_step_changes_state
    src = <<~BADA
      import "std/microtubule.bada"
      arr mt <- MT.make(6)
      let c0 <- MT.coherence(mt)
      mt = MT.step(mt, 0.6, 0.2, 2.5)
      let c1 <- MT.coherence(mt)
      print str(c0) + "|" + str(c1)
    BADA
    a, b = out(src).first.split("|").map(&:to_f)
    refute_in_delta a, b, 1e-9 # the oscillation changed coherence
  end

  def test_thermal_energy_finite_positive
    src = <<~BADA
      import "std/microtubule.bada"
      print str(MT.thermal_energy(MT.make(10)))
    BADA
    e = out(src).first.to_f
    assert e.finite?
    assert_operator e, :>, 0.0
  end

  def test_fpga_verilog_is_well_formed
    src = <<~BADA
      import "std/fpga.bada"
      print FPGA.verilog(12, 16)
    BADA
    v = out(src).join("\n")
    assert_match(/module microtubule_array/, v)
    assert_match(/always @\(posedge clk\)/, v)
    assert_match(/endmodule/, v)
    assert_match(/phase\[i\] <= phase\[i\] \+ omega\[i\]/, v) # the oscillator
  end

  def test_consciousness_app_generates_moments_and_circuit
    Dir.chdir(Dir.mktmpdir) do
      app = File.expand_path("../bada/app/consciousness.bada", __dir__)
      lines = Bada::Lang.run_file(app, out: StringIO.new).output
      joined = lines.join("\n")
      # conscious moments occurred
      m = joined[/意識モーメント数\s*=\s*(\d+)/, 1].to_i
      assert_operator m, :>, 0
      # a non-trivial consciousness language stream was generated
      assert_match(/量子振動からの意識の言語生成/, joined)
      # the FPGA central-intelligence source was emitted and written
      assert_match(/module microtubule_array/, joined)
      assert File.exist?("microtubule_array.v")
      assert_match(/endmodule/, File.read("microtubule_array.v", encoding: "UTF-8"))
    end
  end
end
