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
