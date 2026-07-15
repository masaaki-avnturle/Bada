#!/usr/bin/env ruby
# encoding: UTF-8
# Penrose 絵記号ビルダーのデモ:
#   パレットから部品を選び、組み合わせて、清書方程式＋計算方程式を生成する。
$LOAD_PATH.unshift(File.expand_path("../lib", __dir__))
require "bada"

include Bada::Penrose

# --- 例1: 行列積（縮約） ------------------------------------------------
b = Builder.new
b.place("A", legs: 2, value: [[1, 2], [3, 4]])   # テンソル箱 A
b.place("B", legs: 2, value: [[5, 6], [7, 8]])   # テンソル箱 B
b.wire("A.1", "B.0")                             # 縮約線でつなぐ
b.free("A.0", "i")                               # 自由添字 i
b.free("B.1", "j")                               # 自由添字 j
puts "【例1: 行列積】"
puts b.combined_report
puts

# --- 例2: トレース（スカラー） -----------------------------------------
t = Builder.new
t.place("A", legs: 2, value: [[1, 2], [3, 4]])
t.wire("A.0", "A.1")                             # 両脚を結ぶ = トレース
puts "【例2: トレース】"
puts t.combined_report
puts

# --- 例3: 微分・積分の絵記号（記号のみ） --------------------------------
s = Builder.new
s.place("T", legs: 2)
s.free("T.0", "μ")
s.free("T.1", "ν")
s.nabla("T", "ρ")                                # 共変微分 ∇_ρ
s.integral("ν")                                  # ∫ d ν
puts "【例3: ∇ と ∫ の絵記号】"
puts s.combine[:latex]
puts s.combine[:pretty]

# ブラウザGUIも書き出せます:
#   ruby -Ilib bin/bada html app.html
