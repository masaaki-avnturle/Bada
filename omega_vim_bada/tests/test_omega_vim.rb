# frozen_string_literal: true

# Self-contained test harness (no gem dependencies) for Ω-Vim.
#   ruby -Ilib -I../bada_ruby/lib tests/test_omega_vim.rb

Encoding.default_external = Encoding::UTF_8
Encoding.default_internal = Encoding::UTF_8

require "tmpdir"
require "bada"
require "bada/code_fix"
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

puts
puts "#{$count - $fail}/#{$count} checks passed"
exit($fail.zero? ? 0 : 1)
