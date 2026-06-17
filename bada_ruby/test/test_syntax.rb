# encoding: UTF-8
# frozen_string_literal: true

require "minitest/autorun"
require "stringio"
require_relative "../lib/bada"

class TestBadaSyntax < Minitest::Test
  def out(src) = Bada::Lang.run(src, out: StringIO.new).output

  # --- range / array ---
  def test_range_literal_array
    assert_equal ["[1, 2, 3, 4, 5]"], out("arr x <- [1..5]\nprint str(x)")
  end

  def test_array_indexing
    assert_equal ["10, 30"], out("arr x <- [10, 20, 30]\nprint str(x[0]) + \", \" + str(x[2])")
  end

  def test_array_slice_with_range
    assert_equal ["[20, 30, 40]"], out("arr x <- [10, 20, 30, 40, 50]\nprint str(x[1..3])")
  end

  def test_arr_validates_type
    assert_raises(RuntimeError) { out("arr x <- 5\nprint str(x)") }
  end

  # --- hash ---
  def test_hash_literal_and_index
    src = "has h <- {a: 1, b: 2}\nprint str(h[\"a\"]) + \",\" + str(h[\"b\"])"
    assert_equal ["1,2"], out(src)
  end

  def test_hash_display
    assert_equal ["{a: 1, b: 2}"], out("has h <- {a: 1, b: 2}\nprint str(h)")
  end

  def test_hash_keys_values
    assert_equal ["[a, b]"], out("has h <- {a: 1, b: 2}\nprint str(keys(h))")
  end

  # --- typed let ---
  def test_typed_let
    assert_equal ["42"], out("let int n <- 42\nprint str(n)")
  end

  def test_let_string_with_comma
    assert_equal ["hello,world"], out('let str s <- "hello,world"' + "\nprint s")
  end

  def test_let_arrow_binder
    assert_equal ["7"], out("let x <- 7\nprint str(x)")
  end

  # --- loop ---
  def test_loop_arrow_form
    assert_equal %w[1 2 3], out("loop i in [1..3] -> p(i)")
  end

  def test_loop_block_form
    src = <<~BADA
      let total <- 0
      loop i in [1..4]
        total = total + i
      end
      print str(total)
    BADA
    assert_equal ["10"], out(src)
  end

  def test_loop_over_hash
    src = <<~BADA
      has h <- {a: 1, b: 2}
      loop kv in h
        print str(kv[0]) + "=" + str(kv[1])
      end
    BADA
    assert_equal ["a=1", "b=2"], out(src)
  end

  # --- p builtin doesn't break params named p ---
  def test_p_builtin_and_param_shadow
    src = <<~BADA
      def f(p)
        return p * 2
      end
      print str(f(21))
      p(99)
    BADA
    assert_equal %w[42 99], out(src)
  end

  # --- directive-branch loop (the user's pattern) ---
  def test_directive_branch_then_loop
    src = <<~BADA
      arr r <- [1..5]
      let squared <- r -< def(x) return x * x end
      loop v in squared -> p(v)
    BADA
    assert_equal %w[1 4 9 16 25], out(src)
  end

  def test_array_branch_merge_directly
    # an array is a flow of its elements
    assert_equal ["55"], out("print str([1..5] -< def(x) return x * x end >- def(a, b) return a + b end)")
  end
end
