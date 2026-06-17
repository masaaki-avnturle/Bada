# encoding: UTF-8
# frozen_string_literal: true

require "minitest/autorun"
require "stringio"
require "tmpdir"
require_relative "../lib/bada"

class TestMultiGPT < Minitest::Test
  def out(src) = Bada::Lang.run(src, out: StringIO.new).output

  def classify(req)
    out(%(import "std/multigpt.bada"\nprint MultiGPT.classify("#{req}"))).first
  end

  def test_classification_routes
    assert_equal "equation", classify("ガンマ関数の方程式を生成して")
    assert_equal "paper", classify("論文を書いて")
    assert_equal "proof", classify("予想を証明して")
    assert_equal "circuit", classify("FPGA回路を生成")
    assert_equal "application", classify("アプリのソースコードを書いて")
    assert_equal "chat", classify("意識とは何か")
  end

  def test_respond_equation
    src = <<~BADA
      import "std/multigpt.bada"
      arr r <- MultiGPT.respond("ガンマ関数の方程式")
      print at(r, 0)
      print str(len(at(r, 1)) > 0)
    BADA
    res = out(src)
    assert_equal "equation", res[0]
    assert_equal "true", res[1]
  end

  def test_respond_circuit_is_soc_verilog
    src = <<~BADA
      import "std/multigpt.bada"
      arr r <- MultiGPT.respond("FPGA回路")
      print at(r, 0)
      print str(contains(at(r, 1), "module fpga_soc"))
    BADA
    res = out(src)
    assert_equal "circuit", res[0]
    assert_equal "true", res[1]
  end

  def test_generated_application_is_runnable
    src = <<~BADA
      import "std/multigpt.bada"
      print MultiGPT.application("テストアプリ")
    BADA
    app_src = out(src).join("\n")
    assert_match(/import "std\/special.bada"/, app_src)
    # the generated app source actually runs
    res = Bada::Lang.run(app_src, out: StringIO.new,
                         base_dir: File.expand_path("../bada", __dir__)).output.join("\n")
    assert_match(/Γ\(5\) = 24/, res)
    assert_match(/完了/, res)
  end

  def test_paper_has_sections
    src = <<~BADA
      import "std/multigpt.bada"
      print MultiGPT.paper("量子振動の意識")
    BADA
    p = out(src).join("\n")
    assert_match(/## 要旨/, p)
    assert_match(/## 方程式/, p)
    assert_match(/\$\$/, p) # LaTeX
    assert_match(/## 理論的分解/, p)
  end

  def test_end_to_end_app_runs
    Dir.chdir(Dir.mktmpdir) do
      app = File.expand_path("../bada/app/multigpt.bada", __dir__)
      joined = Bada::Lang.run_file(app, out: StringIO.new).output.join("\n")
      assert_match(/マルチ ChatGPT/, joined)
      assert_match(/種別: equation/, joined)
      assert_match(/種別: proof/, joined)
      assert_match(/種別: circuit/, joined)
      assert File.exist?("multigpt_paper.md")
    end
  end
end
