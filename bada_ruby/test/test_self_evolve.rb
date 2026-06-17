# encoding: UTF-8
# frozen_string_literal: true

require "minitest/autorun"
require "stringio"
require "tmpdir"
require_relative "../lib/bada"

class TestSelfEvolve < Minitest::Test
  def out(src) = Bada::Lang.run(src, out: StringIO.new).output

  def test_telomere_hayflick
    src = <<~BADA
      import "std/telomere.bada"
      print str(Telo.alive(1)) + "," + str(Telo.alive(0)) + "," + str(Telo.divide(3))
    BADA
    assert_equal ["true,false,2"], out(src)
  end

  def test_soc_verilog_has_all_modules
    src = <<~BADA
      import "std/quantum_npu.bada"
      print QNPU.soc(4, 8)
    BADA
    v = out(src).join("\n")
    assert_match(/module microtubule_array/, v)
    assert_match(/module quantum_bios/, v)
    assert_match(/module npu_mac/, v)
    assert_match(/module fpga_soc/, v)
    assert_equal 4, v.scan(/endmodule/).length
  end

  def test_evolver_organism_source_runnable_shape
    src = <<~BADA
      import "std/evolver.bada"
      print Evolver.organism_source(6, 12, 3, 1)
    BADA
    s = out(src).join("\n")
    assert_match(/import "std\/evolver.bada"/, s)
    assert_match(/Evolver\.live\(6, 12, 3, 1\)/, s)
  end

  def test_mutate_grows_and_shortens_telomere
    src = <<~BADA
      import "std/evolver.bada"
      arr m <- Evolver.mutate(4, 8, 5, 0, 0.02)
      print str(at(m, 0) > 4) + "," + str(at(m, 1) > 8) + "," + str(at(m, 2)) + "," + str(at(m, 3))
    BADA
    # qubits grew, width grew, telomere 5->4, gen 0->1
    assert_equal ["true,true,4,1"], out(src)
  end

  def test_end_to_end_bounded_lineage
    Dir.chdir(Dir.mktmpdir) do
      app = File.expand_path("../bada/app/self_evolve.bada", __dir__)
      lines = Bada::Lang.run_file(app, out: StringIO.new).output
      joined = lines.join("\n")
      # telomere = 5 -> exactly generations 0..5 of sources, senescence at the end
      assert_match(/世代 0\.\.5/, joined)
      assert_match(/ヘイフリック限界|senescence|老化/, joined)
      # the self-evolved source files exist
      assert File.exist?("organism_gen_0.v")
      assert File.exist?("organism_gen_5.bada")
      # a generated organism is itself runnable -> regenerates Verilog + next gen
      cand = File.read("organism_gen_2.bada", encoding: "UTF-8")
      assert_match(/Evolver\.live\(8, 16, 3, 2\)/, cand)
      Bada::Lang.run(cand, out: StringIO.new, base_dir: File.expand_path("../bada", __dir__))
      assert File.exist?("organism_gen_3.bada") # it spawned the next generation
      soc = File.read("organism_gen_2.v", encoding: "UTF-8")
      assert_equal 4, soc.scan(/endmodule/).length
    end
  end
end
