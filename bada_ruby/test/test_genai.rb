# encoding: UTF-8
# frozen_string_literal: true

require "minitest/autorun"
require "stringio"
require "tmpdir"
require_relative "../lib/bada"

class TestGenAI < Minitest::Test
  def out(src) = Bada::Lang.run(src, out: StringIO.new).output

  def test_chat_bridge_to_omegachat
    # Bada can reach the ChatGPT branch (分派)
    line = out('print Chat.line("FPGA回路から何が生成できるか")').first
    assert line.is_a?(String)
    refute_empty line
  end

  def test_genai_next_n_grows_with_xi
    src = <<~BADA
      import "std/genai.bada"
      print str(GenAI.next_n(12, 0.05))
    BADA
    # next_n = 12 + 4 + floor(0.05*60) = 12 + 4 + 3 = 19
    assert_equal ["19"], out(src)
  end

  def test_genai_next_candidate_record
    src = <<~BADA
      import "std/genai.bada"
      import "std/fpga.bada"
      let seed <- FPGA.verilog(12, 16)
      arr c <- GenAI.next_candidate(seed, 2, 12)
      print at(c, 0)
      print str(at(c, 1) > 12)
      print str(len(at(c, 2)) > 100)
    BADA
    res = out(src)
    assert_equal "candidate_2", res[0]
    assert_equal "true", res[1] # N grew
    assert_equal "true", res[2] # Verilog non-trivial
  end

  def test_testbench_well_formed
    src = <<~BADA
      import "std/fpga.bada"
      print FPGA.testbench(8, 16)
    BADA
    v = out(src).join("\n")
    assert_match(/module tb_microtubule/, v)
    assert_match(/microtubule_array #\(/, v)
    assert_match(/\$finish/, v)
  end

  def test_end_to_end_generates_candidate_sources
    Dir.chdir(Dir.mktmpdir) do
      app = File.expand_path("../bada/app/genai_fpga.bada", __dir__)
      lines = Bada::Lang.run_file(app, out: StringIO.new).output
      joined = lines.join("\n")
      assert_match(/ChatGPT 分派の解説/, joined)
      assert_match(/candidate_3/, joined)
      # the AI generated next-candidate SOURCE CODE files
      assert File.exist?("candidate_1.bada")
      assert File.exist?("candidate_2.v")
      assert File.exist?("candidate_2_tb.v")
      # the generated candidate Bada source is itself runnable -> valid Verilog
      cand = File.read("candidate_1.bada", encoding: "UTF-8")
      assert_match(/FPGA\.verilog/, cand)
      Bada::Lang.run(cand, out: StringIO.new, base_dir: File.expand_path("../bada", __dir__))
      assert File.exist?("candidate_1.v")
      assert_match(/endmodule/, File.read("candidate_1.v", encoding: "UTF-8"))
    end
  end
end
