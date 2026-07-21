# encoding: UTF-8
# frozen_string_literal: true

require "minitest/autorun"
require_relative "../lib/bada"

include Bada::Penrose

class TestTensorEinsum < Minitest::Test
  def test_matrix_product
    a = Tensor.from_nested("A", [[1, 2], [3, 4]], %w[i k])
    b = Tensor.from_nested("B", [[5, 6], [7, 8]], %w[k j])
    r = Einsum.call([a, b], output: %w[i j])
    assert_equal [[19.0, 22.0], [43.0, 50.0]], r.to_nested
  end

  def test_trace
    a = Tensor.from_nested("A", [[1, 2], [3, 4]], %w[i i])
    assert_in_delta 5.0, Einsum.call([a], output: []).value, 1e-9
  end

  def test_dot_product
    v = Tensor.from_nested("v", [3, 4], %w[i])
    w = Tensor.from_nested("w", [3, 4], %w[i])
    assert_in_delta 25.0, Einsum.call([v, w], output: []).value, 1e-9
  end

  def test_outer_product
    v = Tensor.from_nested("v", [1, 2], %w[i])
    w = Tensor.from_nested("w", [3, 4], %w[j])
    r = Einsum.call([v, w], output: %w[i j])
    assert_equal [[3.0, 4.0], [6.0, 8.0]], r.to_nested
  end
end

class TestCanvas < Minitest::Test
  def test_parse_matrix_product
    d = Canvas.parse("i-[A]-[B]-j")
    assert_equal %w[A B], d.nodes.keys
    assert_equal 1, d.wires.length
    assert_equal 2, d.frees.length
    assert_match(/A_\{i k1\} B_\{k1 j\} → R_\{i j\}/, d.einsum_string)
  end

  def test_parse_and_compute
    d = Canvas.parse("i-[A]-[B]-j", values: { "A" => [[1, 2], [3, 4]], "B" => [[5, 6], [7, 8]] })
    e = Evaluator.evaluate(d)
    assert_equal [[19.0, 22.0], [43.0, 50.0]], e[:result]
  end

  def test_vertical_contraction
    drawing = "i-[A]\n   |\n  [B]-j"
    d = Canvas.parse(drawing, values: { "A" => [[1, 2], [3, 4]], "B" => [[1, 0], [0, 1]] })
    e = Evaluator.evaluate(d)
    # A_{i k} B_{j k} = A · Bᵀ = A · I = A
    assert_equal [[1.0, 2.0], [3.0, 4.0]], e[:result]
  end

  def test_integral_sums_index
    d = Canvas.parse("m-[A]\n(I m)", values: { "A" => [10, 20, 30] })
    e = Evaluator.evaluate(d)
    assert_in_delta 60.0, e[:scalar], 1e-9
  end

  def test_decorator_extraction
    d = Canvas.parse("i-[A]-j\nS{i j}")
    assert(d.decorators.any? { |x| x.type == :sym })
  end
end

class TestSymmetrize < Minitest::Test
  def test_symmetrize_result
    # A_{ij} symmetrised: 0.5(A + Aᵀ)
    d = Diagram.build do
      tensor "A", legs: 2, value: [[1, 2], [3, 4]]
      free ["A", 0], "i"
      free ["A", 1], "j"
      symmetrize "i", "j"
    end
    e = Evaluator.evaluate(d)
    assert_equal [[1.0, 2.5], [2.5, 4.0]], e[:result]
  end

  def test_antisymmetrize_result
    d = Diagram.build do
      tensor "A", legs: 2, value: [[1, 2], [3, 4]]
      free ["A", 0], "i"
      free ["A", 1], "j"
      antisymmetrize "i", "j"
    end
    e = Evaluator.evaluate(d)
    assert_equal [[0.0, -0.5], [0.5, 0.0]], e[:result]
  end
end

class TestPalette < Minitest::Test
  def test_palette_has_penrose_symbols
    s = Palette.render
    assert_match(/共変微分 ∇/, s)
    assert_match(/積分 ∫/, s)
    assert_match(/レヴィ・チヴィタ/, s)
  end
end

class TestDerivative < Minitest::Test
  def test_central_difference
    # f(x)=x^2 sampled at 0,1,2,3,4 (h=1) -> f'(x)=2x ; interior central diff exact
    f = [0, 1, 4, 9, 16]
    d = Evaluator.derivative_1d(f, h: 1.0)
    assert_in_delta 4.0, d[2], 1e-9 # f'(2)=4
    assert_in_delta 6.0, d[3], 1e-9 # f'(3)=6
  end
end

class TestStudioAndGenerators < Minitest::Test
  def setup
    @studio = Studio.new(seed: 1)
    @studio.draw("i-[A]-[B]-j", values: { "A" => [[1, 2], [3, 4]], "B" => [[5, 6], [7, 8]] })
  end

  def test_ask
    s = @studio.ask("これは何を計算している？")
    assert_match(/自動解答/, s)
    assert_match(/19/, s)
  end

  def test_paper_has_sections
    p = @studio.paper(question: "行列積の理論")
    assert_match(/要旨/, p)
    assert_match(/Einstein/, p)
    assert_match(/ミレニアム/, p)
    assert_match(/\$\$/, p) # LaTeX block
  end

  def test_generated_code_is_valid_ruby
    code = @studio.code
    assert_match(/Diagram\.build/, code)
    # must parse as valid Ruby
    assert RubyVM::InstructionSequence.compile(code)
  end

  def test_chat_penrose_integration
    chat = Bada::OmegaChat.new
    out = chat.penrose("i-[A]-[B]-j",
                       values: { "A" => [[1, 2], [3, 4]], "B" => [[5, 6], [7, 8]] },
                       question: "行列積")
    assert_match(/自動計算/, out)
    assert_match(/論文/, out)
    assert_match(/ソースコード/, out)
  end
end

# ---- Builder (palette + dialog application) --------------------------
class TestPenroseBuilder < Minitest::Test
  def build_matmul
    b = Builder.new
    b.place("A", legs: 2, value: [[1, 2], [3, 4]])
    b.place("B", legs: 2, value: [[5, 6], [7, 8]])
    b.wire("A.1", "B.0")
    b.free("A.0", "i")
    b.free("B.1", "j")
    b
  end

  def test_combine_computes_matrix_product
    r = build_matmul.combine
    assert_equal [[19.0, 22.0], [43.0, 50.0]], r[:result]
    assert_equal %w[i j], r[:output]
  end

  def test_combine_generates_fair_copy_latex
    r = build_matmul.combine
    # 清書した方程式: summation form with a dummy index and both factors.
    assert_match(/R_\{ij\}/, r[:latex])
    assert_match(/\\sum_\{k_\{1\}\}/, r[:latex])
    assert_match(/A_\{ik_\{1\}\}/, r[:latex])
    assert_match(/B_\{k_\{1\}j\}/, r[:latex])
    assert_match(/\A\$\$.*\$\$\z/m, r[:display])
  end

  def test_pretty_unicode_form
    r = build_matmul.combine
    assert_match(/Σ/, r[:pretty])
    assert_match(/k₁/, r[:pretty]) # subscripted dummy index
  end

  def test_trace_is_scalar
    b = Builder.new
    b.place("A", legs: 2, value: [[1, 2], [3, 4]])
    b.wire("A.0", "A.1")
    r = b.combine
    assert_in_delta 5.0, r[:scalar], 1e-9
  end

  def test_symmetrise_result
    b = Builder.new
    b.place("A", legs: 2, value: [[1, 2], [3, 4]])
    b.free("A.0", "i")
    b.free("A.1", "j")
    b.symmetrize("i", "j")
    r = b.combine
    assert_equal [[1.0, 2.5], [2.5, 4.0]], r[:result]
    assert_match(/R_\{\(ij\)\}/, r[:latex])
  end

  def test_decorators_render_symbolically
    b = Builder.new
    b.place("T", legs: 2)
    b.free("T.0", "μ")
    b.free("T.1", "ν")
    b.nabla("T", "ρ")
    b.integral("ν")
    r = b.combine
    assert_match(/\\nabla_\{ρ\}/, r[:latex])
    assert_match(/\\int/, r[:latex])
    assert_match(/∇/, r[:pretty])
    assert_match(/∫/, r[:pretty])
  end

  def test_bad_slot_raises
    b = Builder.new
    b.place("A", legs: 2)
    assert_raises(ArgumentError) { b.wire("A.5", "A.0") } # leg out of range
    assert_raises(ArgumentError) { b.wire("Z.0", "A.0") } # unknown node
  end

  def test_combined_report_has_both_equations
    out = build_matmul.combined_report
    assert_match(/清書した方程式/, out)
    assert_match(/計算した方程式/, out)
    assert_match(/\[\[19\.0, 22\.0\], \[43\.0, 50\.0\]\]/, out)
  end
end

# ---- WebApp (visual palette+dialog export) ---------------------------
class TestPenroseWebApp < Minitest::Test
  def test_render_is_self_contained_html
    html = WebApp.render
    assert_match(/<!DOCTYPE html>/, html)
    assert_match(/ペンローズ絵記号スタジオ/, html)
    # every palette symbol must be embedded as data for the page
    assert_match(/const PALETTE =/, html)
    Palette.glyphs.each_value { |g| assert_includes html, g[:name] }
    # no external resource references (offline / CSP-safe)
    refute_match(%r{https?://[^"']+\.(js|css)}, html)
  end

  def test_write_creates_file
    require "tempfile"
    dir = Dir.mktmpdir
    path = WebApp.write(File.join(dir, "app.html"))
    assert File.exist?(path)
    assert_operator File.size(path), :>, 1000
  ensure
    FileUtils.remove_entry(dir) if dir
  end

  def test_palette_embeds_faithful_svg_glyphs
    html = WebApp.render
    # each palette symbol carries an inline SVG in the embedded PALETTE data
    assert_includes html, "<svg viewBox=\\\"0 0 120 120"
    # the covariant-derivative hoop and the (anti)symmetriser must be present
    assert_includes html, "ellipse" # ∇ hoop
    assert_includes html, "行列 (matrix"
    assert_includes html, "積分"
  end

  def test_has_generator_button_and_drawing_canvas
    html = WebApp.render
    assert_includes html, "Generator"           # 描画→方程式 の生成ボタン
    assert_includes html, "id=\"canvas\""         # 描くキャンバス
    assert_includes html, "id=\"palette\""        # 絵記号を選ぶパレット
    assert_match(/clickLeg|makeFree/, html)       # 脚を結線/自由添字にする対話
  end

  def test_has_preset_equations_that_build_diagrams
    html = WebApp.render
    # ② 規定の方程式 → 絵記号 の逆方向
    assert_includes html, "const PRESETS"
    assert_includes html, "規定の方程式を選ぶ"
    # a few known equations must be offered
    ["行列積", "トレース", "内積", "共変微分", "積分"].each { |eq| assert_includes html, eq }
    # each preset builds picture-symbols (nodes) via mkNode
    assert_includes html, "function mkNode"
    assert_match(/loadPreset/, html)
  end

  def test_has_freehand_drawing_mode
    html = WebApp.render
    assert_includes html, "手描き"                 # freehand toggle
    assert_match(/function togglePen/, html)
    assert_match(/penStroke/, html)               # ink stroke capture
    assert_match(/polyline/, html)                # ink rendered as polylines
  end

  def test_placed_symbols_get_default_values_so_they_compute
    html = WebApp.render
    # a picture-symbol placed from the palette must carry a default numeric value
    # so drawing/selecting it computes immediately (no hand-typed JSON needed).
    assert_match(/function defaultValue/, html)
    assert_match(/val:defaultValue\(up\+down\)/, html)   # addNode assigns it
    refute_match(/x:70\+\(i%4\)\*195[^}]*val:null/, html) # no more null-valued placement
  end

  def test_has_arithmetic_add_sub_mul_div
    html = WebApp.render
    assert_includes html, "加減乗除"
    # the four operators must be offered
    ["＋", "−", "×", "÷"].each { |op| assert_includes html, op }
    # elementwise op with scalar broadcast + register save
    assert_match(/function ew\(/, html)
    assert_match(/saveReg|registers/, html)
  end

  def test_has_app_factory_meta_app
    html = WebApp.render
    assert_includes html, "アプリを作るアプリ"
    assert_match(/function generateApp/, html)      # 方程式ネットワーク → ソース
    assert_match(/未知事前予知エンジン/, html)         # 意味付け
    assert_match(/function meaning\(/, html)         # Ξ/geometry/theory engine
    assert_match(/function downloadApp/, html)       # 生成アプリのダウンロード
    # the generated app must not prematurely close the outer page script
    refute_includes html, "<script>${src}</script>"
  end

  def test_generated_app_download_works_in_packaged_apps
    html = WebApp.render
    # Android WebView / Electron cannot save a plain blob download, so the code
    # must branch: Capacitor Filesystem on native, blob anchor on browser/Electron.
    assert_match(/isNativePlatform/, html)
    assert_match(/Filesystem/, html)
    assert_match(/Blob/, html)                        # browser/Electron fallback kept
  end
end

# ---- AppFactory (アプリを作るアプリ — meta-application) ----------------
class TestPenroseAppFactory < Minitest::Test
  def net
    {
      name: "NetDemo",
      steps: [
        { name: "R1", equation: "R1_{ij} = A_{ik} B_{kj}", value: [[19, 22], [43, 50]] },
        { name: "R2", equation: "R2 = A_{ii}", value: 5 },
        { name: "R3", equation: "R3 = R1 ÷ R2", inputs: %w[R1 R2], op: "÷" }
      ]
    }
  end

  def test_generate_returns_source_html_meaning
    r = AppFactory.generate(net)
    assert_match(/STEPS/, r[:source])
    assert_match(/\A<!DOCTYPE html>/, r[:html])
    assert_equal 3, r[:meaning].length
  end

  def test_generated_source_is_runnable_ruby
    code = AppFactory.generate(net)[:source]
    # must compile as valid Ruby (the network program)
    assert RubyVM::InstructionSequence.compile(code)
    assert_match(/def ew/, code)                    # 加減乗除 kernel
    assert_match(/STEPS\["R3"\] = ew/, code)        # the network edge
  end

  def test_meaning_annotates_each_equation
    m = AppFactory.generate(net)[:meaning].first
    # 未知事前予知エンジン: invariant Ξ, Thurston geometry, dominant theory
    assert m[:invariant].is_a?(Float)
    assert m[:geometry].is_a?(String)
    assert m[:dominant].is_a?(String)
  end

  def test_generated_app_is_self_contained_html
    html = AppFactory.generate(net)[:html]
    assert_includes html, "生成アプリ"
    assert_includes html, "未知事前予知エンジン"
    refute_match(%r{https?://[^"']+\.(js|css)}, html)  # no external assets
  end
end

# ---- GlyphSVG (faithful Penrose picture-symbols) ---------------------
class TestPenroseGlyphSVG < Minitest::Test
  def test_every_palette_key_has_svg
    Palette::GLYPHS.each_key do |key|
      svg = GlyphSVG.for(key)
      assert_match(/\A<svg /, svg, "#{key} should render an SVG")
      assert_match(%r{</svg>\z}, svg)
    end
  end

  def test_new_real_notation_symbols_exist
    keys = Palette::GLYPHS.keys
    # matrix + integral supplements, plus real Penrose symbols from the notes
    %i[matrix matmul vector integral nabla riemann torsion swap symmetrize antisymmetrize].each do |k|
      assert_includes keys, k
    end
  end

  def test_glyphs_carry_svg_field
    g = Palette.glyphs
    assert g[:tensor][:svg].start_with?("<svg ")
    assert g[:nabla][:svg].include?("ellipse") # ∇ drawn as a hoop
    assert g[:integral][:svg].include?("∫")
  end

  def test_conventions_documented_upper_lower_legs
    # tensor meaning must state upper=top line, lower=bottom line
    assert_match(/上に出る線/, Palette::GLYPHS[:tensor][:meaning])
    assert_match(/下に出る線/, Palette::GLYPHS[:tensor][:meaning])
  end
end
