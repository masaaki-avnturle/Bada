# frozen_string_literal: true

# Self-contained test harness (no gem dependencies) for Ω-Vim.
#   ruby -Ilib -I../bada_ruby/lib tests/test_omega_vim.rb

Encoding.default_external = Encoding::UTF_8
Encoding.default_internal = Encoding::UTF_8

require "tmpdir"
require "bada"
require "bada/code_fix"
require "bada/grammar"
require "bada/omega_vim"
require "bada/vim_interpreter"

$fail = 0
$count = 0
def check(desc)
  $count += 1
  ok = yield
  if ok
    puts "  ok  #{desc}"
  else
    $fail += 1
    puts "FAIL  #{desc}"
  end
rescue => e
  $fail += 1
  puts "ERR   #{desc}: #{e.class}: #{e.message}"
end

include Bada

puts "== Bada::CodeFix — spinning-top integrable code correction =="

check("Python: appends missing closing parens, orbit closes") do
  r = CodeFix.fix("def f(x:\n    return (x*2\n")
  r[:report][:orbit_closed] && r[:report][:winding] == 0 && r[:changed]
end

check("C: appends missing closing brace") do
  r = CodeFix.fix("int main(void) {\n    return 0;\n")
  r[:source].include?("}") && r[:report][:orbit_closed]
end

check("JS: replaces mismatched ')' with ']'") do
  r = CodeFix.fix("const a = [1,2,3);\n")
  r[:source].include?("[1,2,3]") && r[:report][:orbit_closed]
end

check("Ruby: closes unterminated string") do
  r = CodeFix.fix("puts \"hello\nputs 42\n")
  r[:report][:orbit_closed]
end

check("Lisp: balances parentheses") do
  r = CodeFix.fix("(defun f (x) (+ x 1)\n")
  r[:source].count("(") == r[:source].count(")") && r[:report][:orbit_closed]
end

check("stray closer is removed") do
  r = CodeFix.fix("x = 1)\n")
  r[:report][:orbit_closed] && !r[:source].include?(")")
end

check("already-correct code is a structural no-op") do
  src = "def ok():\n    return [1, (2), {3: 4}]\n"
  r = CodeFix.fix(src)
  r[:report][:orbit_closed] && r[:report][:winding] == 0
end

check("comments and string delimiters are not miscounted") do
  # a ')' inside a string / comment must not be treated as structure
  src = "s = \"a ) b\"  # ) not real\nt = (1 + 2)\n"
  r = CodeFix.analyze(src)
  r[:orbit_closed] && r[:winding] == 0
end

check("Xi invariant is conserved by the fix (integrable guarantee)") do
  r = CodeFix.fix("foo(bar[baz\n")
  r[:invariant_conserved]
end

check("block comment /* */ unterminated is closed") do
  r = CodeFix.fix("int x = 1; /* oops\n")
  r[:report][:orbit_closed]
end

puts "== Bada::OmegaVim — modal editor =="

check("insert mode types text then ESC returns to normal") do
  b = OmegaVim::Buffer.new("", filename: nil)
  ed = OmegaVim::Editor.new(b, rows: 10, cols: 40)
  ed.run_script("ihello\e")
  b.text == "hello" && ed.mode == :normal
end

check("o opens a line below and enters insert") do
  b = OmegaVim::Buffer.new("line1", filename: nil)
  ed = OmegaVim::Editor.new(b, rows: 10, cols: 40)
  ed.run_script("otwo\e")
  b.lines == ["line1", "two"]
end

check("x deletes the character under the cursor") do
  b = OmegaVim::Buffer.new("abc", filename: nil)
  ed = OmegaVim::Editor.new(b, rows: 10, cols: 40)
  ed.run_script("x")
  b.line == "bc"
end

check("dd deletes the current line") do
  b = OmegaVim::Buffer.new("a\nb\nc", filename: nil)
  ed = OmegaVim::Editor.new(b, rows: 10, cols: 40)
  ed.run_script("jdd")
  b.lines == ["a", "c"]
end

check("gg and G jump to first / last line") do
  b = OmegaVim::Buffer.new("1\n2\n3\n4", filename: nil)
  ed = OmegaVim::Editor.new(b, rows: 10, cols: 40)
  ed.run_script("G")
  bottom = b.row
  ed.run_script("gg")
  bottom == 3 && b.row == 0
end

check("= (normal) runs the integrable fix on a buggy buffer") do
  b = OmegaVim::Buffer.new("f(x[1\n", filename: nil)
  ed = OmegaVim::Editor.new(b, rows: 10, cols: 40)
  r = ed.run_script("=").last_fix
  CodeFix.analyze(b.text)[:orbit_closed] && r[:invariant_conserved]
end

check(":fix (command) corrects and :w writes to disk") do
  path = File.join(Dir.tmpdir, "ov_cmd_#{Process.pid}.js")
  File.write(path, "x = [1,2,3);\n")
  b = OmegaVim::Buffer.open(path)
  ed = OmegaVim::Editor.new(b, rows: 10, cols: 40)
  ed.run_script(":fix\r:w\r")
  CodeFix.analyze(File.read(path))[:orbit_closed]
ensure
  File.delete(path) if path && File.exist?(path)
end

check(":q on a clean buffer quits; dirty buffer is protected") do
  b = OmegaVim::Buffer.new("hi", filename: nil)
  ed = OmegaVim::Editor.new(b, rows: 10, cols: 40)
  ed.run_script("x")          # make it dirty
  ed.run_script(":q\r")       # should be refused
  refused = !ed.quit?
  ed.run_script(":q!\r")      # force quit
  refused && ed.quit?
end

puts "== Bada language program (omega_vim.bada via VimInterpreter) =="

check("the .bada program opens a buffer, fixes it, and runs headless") do
  src = File.join(File.expand_path("..", __dir__), "examples", "buggy.py")
  tmp = File.join(Dir.tmpdir, "ov_bada_#{Process.pid}.py")
  File.write(tmp, File.read(src))
  prog = File.join(File.expand_path("..", __dir__), "src", "omega_vim.bada")
  interp = VimInterpreter.new(arg: tmp, headless: true, script: ":q\r")
  interp.run(File.read(prog))
  buf = interp.buffer("main")
  CodeFix.analyze(buf.text)[:orbit_closed]
ensure
  File.delete(tmp) if defined?(tmp) && tmp && File.exist?(tmp)
end

check("base Bada operators still work through VimInterpreter") do
  interp = VimInterpreter.new
  out = interp.run("set g = 2.5\nprint g\n")
  out.include?("2.5")
end

puts "== Bada::Grammar — checker / parser completion / indent =="

check("grammar check flags an unclosed Ruby block (missing end)") do
  chk = Grammar.check("def f\n  puts 1\n", lang: :ruby)
  !chk[:ok] && chk[:diagnostics].any? { |d| d[:kind] == :unclosed_block }
end

check("grammar check passes clean code") do
  Grammar.check("def f\n  puts 1\nend\n", lang: :ruby)[:ok]
end

check("parser completion returns expected closers innermost-first (Ruby)") do
  c = Grammar.complete("def f(x)\n  if x > 0\n    g(a[1", lang: :ruby)[:candidates]
  c == ["]", ")", "end", "end"]
end

check("parser completion suggests block terminator keyword") do
  s = Grammar.complete("def f\n  x = 1\n", lang: :ruby)[:suggestion]
  s && s[:type] == :keyword && s[:text] == "end"
end

check("strings/comments are masked — inner brackets not counted") do
  c = Grammar.complete("a = \"(\" + foo(bar", lang: :ruby)[:candidates]
  c == [")"]   # only the real foo( is open; the "(" in the string is ignored
end

check("reindent normalises C nesting") do
  src = "int main(){\nprintf(1);\nif(x){\ny=1;\n}\n}\n"
  out = Grammar.reindent(src, lang: :c, width: 4)
  out == "int main(){\n    printf(1);\n    if(x){\n        y=1;\n    }\n}\n"
end

check("reindent handles Ruby keyword blocks incl. else/do") do
  src = "def f\nif x\na\nelse\nb\nend\nend\n"
  out = Grammar.reindent(src, lang: :ruby, width: 2)
  out == "def f\n  if x\n    a\n  else\n    b\n  end\nend\n"
end

check("reindent leaves Python indentation semantic (trim only)") do
  src = "def f():\n        return 1\n"   # weird indent, but semantic
  out = Grammar.reindent(src, lang: :python)
  out == "def f():\n        return 1\n"   # unchanged except trailing ws
end

check("indent_for_new_line adds a level after a block opener") do
  Grammar.indent_for_new_line(["def f(x)", "  if x"], 1, lang: :ruby, width: 2) == "    "
end

check("indent_for_new_line keeps level when no block opens") do
  Grammar.indent_for_new_line(["  x = 1"], 0, lang: :ruby, width: 2) == "  "
end

puts "== editor: grammar / completion / indent wiring =="

check("auto-indent on 'o' after a Ruby block opener") do
  b = OmegaVim::Buffer.new("def f(x)", filename: "t.rb")
  ed = OmegaVim::Editor.new(b, rows: 20, cols: 60)
  ed.run_script("oputs x\e")
  b.lines == ["def f(x)", "  puts x"]
end

check("auto-indent chains through Enter in insert mode (C)") do
  b = OmegaVim::Buffer.new("", filename: "t.c")
  ed = OmegaVim::Editor.new(b, rows: 20, cols: 60)
  ed.run_script("iif (x) {\rreturn 0;\e")
  b.lines[0] == "if (x) {" && b.lines[1] == "    return 0;"
end

check("Tab parser-completes the expected closer (JS)") do
  b = OmegaVim::Buffer.new("", filename: "t.js")
  ed = OmegaVim::Editor.new(b, rows: 20, cols: 60)
  ed.run_script("ifoo(bar[1\t\t")
  b.line == "foo(bar[1])"
end

check(":check reports grammar issues in the message line") do
  b = OmegaVim::Buffer.new("def f\n  puts 1\n", filename: "t.rb")
  ed = OmegaVim::Editor.new(b, rows: 20, cols: 60)
  ed.run_script(":check\r")
  ed.last_check && !ed.last_check[:ok]
end

check(":indent reindents the whole buffer") do
  b = OmegaVim::Buffer.new("int main(){\nprintf(1);\n}\n", filename: "t.c")
  ed = OmegaVim::Editor.new(b, rows: 20, cols: 60)
  ed.run_script(":indent\r")
  b.lines[1] == "    printf(1);"
end

check("= performs fix AND indent completion together") do
  b = OmegaVim::Buffer.new("int main(){\nprintf(1);\nreturn 0;\n", filename: "t.c")
  ed = OmegaVim::Editor.new(b, rows: 20, cols: 60)
  ed.run_script("=")
  CodeFix.analyze(b.text)[:orbit_closed] && b.lines[1] == "    printf(1);"
end

puts "== Bada program: grammar statements =="

check("omega_vim.bada 'check' + 'reindent' + 'complete' statements run") do
  tmp = File.join(Dir.tmpdir, "ov_gram_#{Process.pid}.c")
  File.write(tmp, "int main(){\nprintf(1);\nreturn 0;\n")
  prog = File.join(File.expand_path("..", __dir__), "src", "omega_vim.bada")
  interp = VimInterpreter.new(arg: tmp, headless: true, script: ":q\r")
  out = interp.run(File.read(prog))
  out.any? { |l| l.start_with?("check main:") } &&
    out.any? { |l| l.start_with?("complete main:") } &&
    out.any? { |l| l.start_with?("reindent main:") } &&
    CodeFix.analyze(interp.buffer("main").text)[:orbit_closed]
ensure
  File.delete(tmp) if defined?(tmp) && tmp && File.exist?(tmp)
end

puts
puts "#{$count - $fail}/#{$count} checks passed"
exit($fail.zero? ? 0 : 1)
