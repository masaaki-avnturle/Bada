# frozen_string_literal: true

# codefix_demo.rb — the source-code error-fixing application driven by the
# integrable system of a complex rotational body (the spinning-top / koma
# geometry of special relativity), with multi-submission (複数投稿).
#
#   ruby -Ilib examples/codefix_demo.rb

$LOAD_PATH.unshift(File.expand_path("../lib", __dir__))
require "bada"

repo = Bada::CodeFix::Repository.new

# Post several deliberately-broken sources at once — the "orbit" of each has
# fallen off its closed condition (a syntax error).
repo.submit(<<~'RB', name: "greeter.rb", language: :ruby)
  def greet(name
    puts "hello, #{name}
  end
RB

repo.submit(<<~'RB', name: "counter.rb", language: :ruby)
  class Counter
    def initialize
      @n = 0

    def tick
      @n += 1
    end
  end
RB

repo.submit(<<~'PY', name: "geometry.py", language: :python)
  def top_energy(m, r, omega):
      I = (m * r ** 2
      return 0.5 * I * omega ** 2
PY

repo.submit(<<~'RB', name: "already_ok.rb", language: :ruby)
  def spin(theta)
    Math.cos(theta) - Complex(0, 1) * Math.sin(theta)
  end
RB

puts repo.report
puts
puts "── 修正後ソース（保存量を戻して軌道を再び閉じる）─────────────"
repo.submissions.each do |s|
  next unless s.result.changed
  puts
  puts "### #{s.name}"
  puts s.result.fixed
end
