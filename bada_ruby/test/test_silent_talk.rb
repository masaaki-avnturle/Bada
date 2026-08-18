# encoding: UTF-8
# frozen_string_literal: true

require "minitest/autorun"
require_relative "../lib/bada"

class TestSilentTalkSession < Minitest::Test
  def setup
    @s = Bada::SilentTalk::Session.new
  end

  def test_starts_empty_in_text_mode
    assert_equal :text, @s.mode
    assert @s.empty?
    assert_equal "", @s.text
    assert_equal 0.0, @s.precision
  end

  def test_text_cue_is_verbalized_and_appended
    r = @s.feed("光 記憶 波")
    assert_equal :text, r[:kind]
    refute_empty r[:verbalization]
    refute @s.empty?
    assert_includes @s.text, r[:verbalization]
    assert_operator r[:precision], :>=, 0.90
  end

  def test_empty_line_is_noop
    r = @s.feed("   ")
    assert_equal :noop, r[:kind]
    assert @s.empty?
  end

  def test_code_mode_generates_source
    assert_equal :command, @s.feed(":code")[:kind]
    assert_equal :code, @s.mode
    r = @s.feed("fibonacci 8")
    assert_equal :code, r[:kind]
    refute_empty r[:code]
    assert_includes @s.text, r[:code].split("\n").first
  end

  def test_lang_command_pins_language
    @s.feed(":code")
    @s.feed(":lang python")
    assert_equal "python", @s.language
    r = @s.feed("print hello 3 times")
    assert_equal "python", r[:language]
  end

  def test_completion_in_text_mode_matches_prefix
    @s.feed("光 と 音 の 記憶")
    hits = @s.complete("光")
    assert(hits.all? { |w| w.start_with?("光") })
  end

  def test_completion_in_code_mode_uses_reserved_words
    @s.feed(":code")
    @s.feed(":lang ruby")
    hits = @s.complete("de")
    assert_includes hits, "def"
  end

  def test_completion_empty_prefix_returns_nothing
    assert_equal [], @s.complete("")
  end

  def test_undo_removes_last_block
    @s.feed("光 記憶")
    @s.feed("波 と 静寂")
    before = @s.blocks.length
    out = @s.feed(":undo")
    assert_equal :command, out[:kind]
    assert_equal before - 1, @s.blocks.length
  end

  def test_undo_on_empty_is_safe
    out = @s.feed(":undo")
    assert_equal :command, out[:kind]
    assert @s.empty?
  end

  def test_clear_empties_document
    @s.feed("光 記憶")
    @s.feed(":clear")
    assert @s.empty?
    assert_equal "", @s.text
  end

  def test_show_returns_document
    @s.feed("光 記憶")
    out = @s.feed(":show")
    assert_equal :command, out[:kind]
    assert_equal @s.text, out[:output]
  end

  def test_precision_command_reports_running_mean
    @s.feed("光 記憶")
    out = @s.feed(":precision")
    assert_match(/precision = \d+\.\d%/, out[:output])
  end

  def test_help_and_unknown_commands
    assert_match(/:code/, @s.feed(":help")[:output])
    assert_match(/unknown/, @s.feed(":nope")[:output])
  end

  def test_mode_toggle_between_text_and_code
    @s.feed(":code")
    assert_equal :code, @s.mode
    @s.feed(":text")
    assert_equal :text, @s.mode
  end

  def test_running_precision_exceeds_silent_talk_baseline
    @s.feed("光 と 音 の 記憶")
    @s.feed("波 が 静寂 に 溶ける")
    assert_operator @s.precision, :>, Bada::SilentTalk::SILENT_TALK_BASELINE
    assert @s.exceeds_silent_talk?
  end

  def test_render_formats_each_kind
    assert_includes @s.render(@s.feed("光 記憶")), "＋"
    @s.feed(":code")
    assert_includes @s.render(@s.feed("factorial 5")), "["
    assert_equal "", @s.render(@s.feed("  "))
  end

  def test_deterministic_document_for_same_input
    a = Bada::SilentTalk::Session.new
    b = Bada::SilentTalk::Session.new
    %w[光 記憶].each { |c| a.feed(c); b.feed(c) }
    assert_equal a.text, b.text
  end

  # ---- engine modes: every function driven by silent text ----------------

  def test_qc_mode_generates_source_and_runs
    assert_equal :command, @s.feed(":qc")[:kind]
    assert_equal :qc, @s.mode
    r = @s.feed("bell")
    assert_equal :qc, r[:kind]
    assert_equal 2, r[:qubits]
    assert_includes r[:source], "CX 0 1"
    assert_includes r[:code], "state vector"          # actually ran on disk memory
    assert_includes @s.text, "MONITOR"
    assert_operator r[:precision], :>, Bada::SilentTalk::SILENT_TALK_BASELINE
  end

  def test_qc_mode_accepts_raw_qasm
    @s.feed(":qc")
    r = @s.feed("H 0; CX 0 1; MEASURE 0")
    assert_equal 2, r[:qubits]
    assert_includes r[:source], "MEASURE 0"
    assert(r[:source].strip.end_with?("HALT"))
  end

  def test_verilog_mode_generates_semiconductor_source
    assert_equal :command, @s.feed(":verilog")[:kind]
    assert_equal :verilog, @s.mode
    r = @s.feed("ghz")
    assert_equal :verilog, r[:kind]
    assert_equal 3, r[:qubits]
    assert_includes r[:code], "module"
    assert_includes r[:code], "NAND"                  # simulated MOSFET decoder
    assert_includes @s.text, "default_nettype"
  end

  def test_semi_alias_switches_to_verilog
    @s.feed(":semi")
    assert_equal :verilog, @s.mode
  end

  def test_telegraph_mode_sends_message
    assert_equal :command, @s.feed(":telegraph")[:kind]
    assert_equal :telegraph, @s.mode
    r = @s.feed("HELLO SPACE")
    assert_equal :telegraph, r[:kind]
    assert_includes r[:code], "Space Telegraph"
  end

  def test_completion_in_qc_mode_uses_mnemonics
    @s.feed(":qc")
    hits = @s.complete("H")
    assert_includes hits, "H"
    assert_includes hits, "HALT"
  end

  def test_all_engine_modes_reachable_by_command
    Bada::SilentTalk::MODES.each do |m|
      @s.feed(":#{m}")
      assert_equal m, @s.mode
    end
  end

  def test_mixed_document_across_engines_exceeds_baseline
    @s.feed("光 と 音 の 記憶")
    @s.feed(":qc"); @s.feed("bell")
    @s.feed(":verilog"); @s.feed("ghz")
    @s.feed(":telegraph"); @s.feed("QUANTUM HELLO")
    assert_equal 4, @s.blocks.length
    assert @s.exceeds_silent_talk?
  end

  # ---- thought-input button (思考入力) ------------------------------------

  def test_thought_fill_text_verbalizes_above_baseline
    t = Bada::SilentTalk.thought_fill("光 記憶 波", kind: :text)
    refute_empty t.text
    assert_operator t.precision, :>, Bada::SilentTalk::SILENT_TALK_BASELINE
  end

  def test_thought_fill_qasm_returns_program
    t = Bada::SilentTalk.thought_fill("bell", kind: :qasm)
    assert_includes t.text, "CX 0 1"
    assert(t.text.end_with?("HALT"))
    assert_operator t.precision, :>, Bada::SilentTalk::SILENT_TALK_BASELINE
  end

  def test_thought_fill_intent_is_usable_by_coder
    t = Bada::SilentTalk.thought_fill("数 を 表示", kind: :intent)
    refute_empty t.text
    # the verbalized intent can be fed straight to the code engine
    r = Bada::Coder.generate(t.text)
    refute_empty r[:code]
  end

  def test_thought_fill_empty_cue_is_safe
    t = Bada::SilentTalk.thought_fill("", kind: :text)
    refute_empty t.text
    assert_operator t.precision, :>, Bada::SilentTalk::SILENT_TALK_BASELINE
  end

  # ---- thought CAPTURE: no typed/spoken input at all -----------------------

  def test_thought_capture_needs_no_input_and_exceeds_baseline
    t = Bada::SilentTalk.thought_capture(kind: :text, nonce: 0)
    refute_empty t.text
    assert_operator t.precision, :>, Bada::SilentTalk::SILENT_TALK_BASELINE
  end

  def test_thought_capture_varies_per_press
    texts = (0..3).map { |n| Bada::SilentTalk.thought_capture(kind: :text, nonce: n).text }
    assert_operator texts.uniq.length, :>=, 3
  end

  def test_thought_capture_is_deterministic_for_same_nonce
    a = Bada::SilentTalk.thought_capture(kind: :text, nonce: 7).text
    b = Bada::SilentTalk.thought_capture(kind: :text, nonce: 7).text
    assert_equal a, b
  end

  def test_thought_capture_qasm_cycles_programs
    prog = Bada::SilentTalk.thought_capture(kind: :qasm, nonce: 1).text
    assert(prog.end_with?("HALT"))
    assert_includes prog, "CX"
  end

  def test_capture_cue_draws_from_lexicon
    cue = Bada::SilentTalk.capture_cue(3)
    cue.split(/\s+/).each { |w| assert_includes Bada::Mind::LEXICON, w }
  end

  # ---- Bada-language silent syntax input (:bada) ---------------------------

  def test_bada_mode_generates_runnable_program
    assert_equal :command, @s.feed(":bada")[:kind]
    assert_equal :bada, @s.mode
    r = @s.feed("光 記憶 波")
    assert_equal :bada, r[:kind]
    assert r[:valid], "generated Bada must run in the interpreter"
    # the cue becomes the string literal
    assert_includes r[:code], '"光 記憶 波"'
    # it really runs
    out = Bada::Interpreter.new.run(r[:code])
    refute_empty out
  end

  def test_bada_program_uses_reserved_and_syntax_words
    @s.feed(":bada")
    r = @s.feed("波")
    assert_includes r[:reserved_used], "set"
    assert_includes r[:reserved_used], "print"
    assert(%w[<- -< >-].any? { |op| r[:reserved_used].include?(op) })
  end

  def test_bada_completion_offers_reserved_words
    @s.feed(":bada")
    assert_equal ["set"], @s.complete("se")
    assert_includes @s.complete("<"), "<-"
    assert_includes @s.complete("pr"), "print"
  end

  def test_reserved_command_lists_bada_words
    @s.feed(":bada")
    out = @s.feed(":reserved")[:output]
    %w[set print as push <- -< >-].each { |w| assert_includes out, w }
  end

  def test_bada_capture_needs_no_input_and_runs
    t = Bada::SilentTalk.thought_capture(kind: :bada, nonce: 2)
    assert_includes t.text, "set"
    assert_operator t.precision, :>, Bada::SilentTalk::SILENT_TALK_BASELINE
    refute_empty Bada::Interpreter.new.run(t.text)
  end

  def test_bada_syntax_reserved_recognition
    line = 'g <- "x"'
    assert_includes Bada::SilentTalk::BadaSyntax.reserved_words(line), "<-"
  end

  def test_bada_is_a_declared_mode
    assert_includes Bada::SilentTalk::MODES, :bada
  end

  # ---- whispered / unknown-language verbalization (:whisper) ---------------

  def test_whisper_reconstructs_vowel_dropped_english
    assert_equal :command, @s.feed(":whisper")[:kind]
    assert_equal :whisper, @s.mode
    r = @s.feed("hll wrld")
    assert_equal :whisper, r[:kind]
    assert_equal "hello world", r[:text]
    assert_equal "en", r[:source_lang]
    assert_operator r[:precision], :>, Bada::SilentTalk::SILENT_TALK_BASELINE
  end

  def test_whisper_expands_domain_words
    @s.feed(":whisper")
    r = @s.feed("qntm lght wv sgnl")
    assert_equal "quantum light wave signal", r[:text]
  end

  def test_whisper_decodes_unknown_language
    @s.feed(":whisper")
    r = @s.feed("φωτ μνημη κυμα")   # non-Latin, non-Japanese script
    assert_equal "unknown", r[:source_lang]
    assert(r[:text].split(/\s+/).all? { |w| Bada::SilentTalk::Whisper::VOCAB.include?(w) })
    assert_operator r[:precision], :>, Bada::SilentTalk::SILENT_TALK_BASELINE
  end

  def test_whisper_unknown_decode_is_deterministic
    a = Bada::SilentTalk::Whisper.decode_unknown("φωτ κυμα")[:text]
    b = Bada::SilentTalk::Whisper.decode_unknown("φωτ κυμα")[:text]
    assert_equal a, b
  end

  def test_whisper_completion_offers_english_vocab
    @s.feed(":whisper")
    assert_includes @s.complete("qu"), "quantum"
    assert_includes @s.complete("li"), "light"
  end

  def test_unknown_language_detection
    assert Bada::SilentTalk::Whisper.unknown_language?("φωτ")
    refute Bada::SilentTalk::Whisper.unknown_language?("hll wrld")
    refute Bada::SilentTalk::Whisper.unknown_language?("光 記憶")
  end

  def test_whisper_is_a_declared_mode
    assert_includes Bada::SilentTalk::MODES, :whisper
  end

  def test_whisper_english_mode_always_returns_english
    # the per-tab 🔉 ウィスパード英語 button forces English mode
    r = Bada::SilentTalk::Whisper.verbalize_en("hll wrld")
    assert_equal "en", r[:lang]
    assert_equal "hello world", r[:text]
    assert_operator r[:precision], :>, Bada::SilentTalk::SILENT_TALK_BASELINE
    # even unknown script is coerced to English (never labelled unknown)
    r2 = Bada::SilentTalk::Whisper.verbalize_en("φωτ κυμα")
    assert_equal "en", r2[:lang]
  end

  # ---- long-form: report (:report) + long Bada source (:bada) --------------

  def test_report_mode_writes_multi_sentence_document
    assert_equal :command, @s.feed(":report")[:kind]
    assert_equal :report, @s.mode
    r = @s.feed("qntm lght mmry wv sgnl")
    assert_equal :report, r[:kind]
    assert_operator r[:sentences], :>=, 4
    lines = r[:text].split("\n")
    assert_equal "Report:", lines.first
    assert_operator lines.length, :>=, 5          # a long document
    assert(lines[1..].all? { |l| l.end_with?(".") })
  end

  def test_report_decodes_unknown_language_into_report
    @s.feed(":report")
    r = @s.feed("φωτ μνημη κυμα σημα")
    assert_equal "unknown", r[:source_lang]
    assert_includes r[:text], "Report:"
    assert_operator r[:precision], :>, Bada::SilentTalk::SILENT_TALK_BASELINE
  end

  def test_bada_long_source_scales_with_tokens
    @s.feed(":bada")
    r = @s.feed("光 記憶 波 音 場")     # 5 thought-tokens
    assert r[:valid]
    assert_operator r[:blocks], :>=, 2
    assert_operator r[:code].split("\n").length, :>=, 10   # long program
    refute_empty Bada::Interpreter.new.run(r[:code])
    assert_includes r[:code], '"光 記憶 波"'                # cue kept in 1st block
  end

  def test_bada_single_token_stays_short
    @s.feed(":bada")
    r = @s.feed("波")
    assert r[:valid]
    assert_equal 1, (r[:blocks] || 1)
  end

  def test_build_long_program_runs
    r = Bada::SilentTalk::BadaSyntax.build_long("光", blocks: 4, nonce: 3)
    assert r[:valid]
    assert_equal 4, r[:blocks]
    refute_empty Bada::Interpreter.new.run(r[:code])
  end

  def test_report_and_bada_are_declared_modes
    assert_includes Bada::SilentTalk::MODES, :report
  end

  # ---- 長長文 (very long) whisper report + Bada source ----------------------

  def test_long_report_is_not_short
    r = Bada::SilentTalk::Whisper.long_report("qntm lght mmry wv sgnl")
    assert_operator r[:sentences], :>=, 10        # 長長文, not a single line
    assert_operator r[:text].split("\n").length, :>=, 11
  end

  def test_long_report_on_unknown_language
    r = Bada::SilentTalk::Whisper.long_report("φωτ μνημη κυμα σημα")
    assert_equal "unknown", r[:lang]
    assert_operator r[:sentences], :>=, 10
  end

  def test_report_mode_now_outputs_long_long_form
    @s.feed(":report")
    r = @s.feed("qntm lght mmry wv sgnl")
    assert_operator r[:sentences], :>=, 10
  end

  def test_build_very_long_bada_program
    r = Bada::SilentTalk::BadaSyntax.build_very_long("光 記憶 波 音 場", nonce: 0)
    assert r[:valid]
    assert_operator r[:blocks], :>=, 8            # 長長文ソース
    assert_operator r[:code].split("\n").length, :>=, 40
    refute_empty Bada::Interpreter.new.run(r[:code])
  end

  # ---- pLaTeX 論文作成 (:latex) --------------------------------------------

  def test_latex_mode_writes_long_platex_paper
    assert_equal :command, @s.feed(":latex")[:kind]
    assert_equal :latex, @s.mode
    r = @s.feed("多様体 量子 もつれ")
    assert_equal :latex, r[:kind]
    assert r[:valid]
    assert_operator r[:sections], :>=, 6
    assert_operator r[:code].split("\n").length, :>=, 30   # 長長文
    assert_includes r[:code], "\\documentclass[a4paper,11pt]{jsarticle}"
    assert_includes r[:code], "\\begin{document}"
    assert_includes r[:code], "\\end{document}"
    assert_includes r[:code], "\\begin{equation}"
  end

  def test_latex_begin_end_balanced
    @s.feed(":latex")
    code = @s.feed("光 記憶 波")[:code]
    assert_equal code.scan(/\\begin\{/).length, code.scan(/\\end\{/).length
  end

  def test_latex_title_uses_cue
    @s.feed(":latex")
    r = @s.feed("光 音 記憶")
    assert_includes r[:title], "光"
    assert_includes r[:code], "\\title{"
  end

  def test_latex_completion_offers_latex_commands
    @s.feed(":latex")
    assert_includes @s.complete("\\sec"), "\\section"
    assert_includes @s.complete("\\begin"), "\\begin"
  end

  def test_latex_paper_is_deterministic
    a = Bada::SilentTalk::Platex.paper("多様体", nonce: 5)[:code]
    b = Bada::SilentTalk::Platex.paper("多様体", nonce: 5)[:code]
    assert_equal a, b
  end

  def test_latex_is_a_declared_mode
    assert_includes Bada::SilentTalk::MODES, :latex
  end

  def test_repl_reads_lines_and_prints_document
    require "stringio"
    input = StringIO.new("光 記憶\n:code\nfibonacci 6\n:quit\n")
    output = StringIO.new
    Bada::SilentTalk::Session.new.repl(io_in: input, io_out: output)
    dump = output.string
    assert_includes dump, "入力結果"
    assert_includes dump, "precision"
  end
end
