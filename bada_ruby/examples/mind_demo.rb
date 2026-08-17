# encoding: UTF-8
# frozen_string_literal: true

# Bada::Mind — 思考の言語化シミュレーションのデモ。
#
#   ruby -Ilib examples/mind_demo.rb
#
# ⚠️ 生成シミュレーションです（実在の脳を読むものではありません）。
# 擬似量子計算機（Bada::QC）で量子サンプリング → 多様体ゲージ・トランスフォーマーで
# 言語化 → ViT で心像 → 脳内アプリの Bada ソース生成＆実行、まで一気に走らせます。

$LOAD_PATH.unshift(File.expand_path("../lib", __dir__))
require "bada"

reader = Bada::Mind::Reader.new

puts reader.render("光 と 音 の 記憶 が 波 の よう に 流れ 望み と 恐れ が 交錯 する", subject: "被験者A")
puts

%w[
  記憶と感情の波
  未来への意志と恐れ
  静寂の中の光と色
].each do |signal|
  r = reader.read(signal)
  puts format("signal=%-18s 思考=「%s」 precision=%.1f%%", signal, r[:verbalization], r[:precision] * 100)
end
