# frozen_string_literal: true

# Bada::QC — ノイマン型・擬似量子計算機のデモ。
#
#   ruby -Ilib examples/qc_demo.rb
#
# 制御回路をモニタに投射 → HDD 内蔵メモリで状態ベクトルを計算 → 半導体（Verilog）
# ソースを生成、までを一気に走らせます。

$LOAD_PATH.unshift(File.expand_path("../lib", __dir__))
require "bada"

puts "==== Bell（H 0 ; CX 0 1）===="
bell = Bada::QC::Machine.bell
puts bell.report
puts

puts "==== GHZ（3量子ビット）===="
ghz = Bada::QC::Machine.ghz
ghz.probabilities.each_with_index do |p, i|
  next if p < 1e-9
  puts format("  |%s> : P = %.4f", i.to_s(2).rjust(3, "0"), p)
end
puts

puts "==== 半導体（Verilog）制御回路ソース（先頭 24 行）===="
puts bell.verilog.lines.first(24).join
bell.close
ghz.close

puts
puts "==== 電子回路（MOSFET NAND）デコーダの検証 ===="
(0...12).each do |op|
  idx = Bada::QC::Logic.decode_index(op, 4)
  puts format("  opcode %2d -> decoder one-hot line %2d  (%s)", op, idx, Bada::QC::ISA.mnemonic(idx))
end
