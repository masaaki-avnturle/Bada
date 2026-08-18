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
