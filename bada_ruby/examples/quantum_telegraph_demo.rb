# frozen_string_literal: true

# Bada::Quantum — 量子もつれのベルの実験に基づく宇宙・汎用電信通信機のデモ。
#
#   ruby -Ilib examples/quantum_telegraph_demo.rb
#
# 量子もつれ（ペアー）→ ベルの実験（不気味な遠隔作用）→ 5次方程式の周期に
# 合わせた非線形カリア → Jones多項式の相関 → 不確定性・確率統計 → 半導体で
# 使える原理 → 証明する機能 → 宇宙での汎用電信通信、を一つのアプリで走らせます。

$LOAD_PATH.unshift(File.expand_path("../lib", __dir__))
require "bada"

telegraph = Bada::Quantum::SpaceTelegraph.new(material: "GaAs", temp_k: 4.0, redundancy: 3)

# 1) 端から端まで（証明 + 送信）のレポート
puts telegraph.render("QUANTUM HELLO FROM EARTH")
puts

# 2) 証明だけを構造化データとして
proof = telegraph.prove
puts "証明の各証明書 (proof certificates):"
proof[:certificates].each { |name, ok| puts format("  %-16s %s", name, ok ? "✓" : "✗") }
puts "  QED = #{proof[:qed]}"
puts

# 3) いくつかのメッセージを実際に宇宙チャネルで送る
%w[SOS ACK 42 こんにちは].each do |msg|
  r = telegraph.transmit(msg)
  puts format("送信 %-8s -> 受信 %-8s  BER=%.4f fidelity=%.4f lossless=%s",
              r[:message], r[:recovered], r[:ber], r[:certified_fidelity], r[:lossless])
end
puts

# 4) 5次方程式の解の公式（Durand–Kerner）: 例として x^5 - x - 1 = 0 を解く
roots = Bada::Quantum::Quintic.solve([0.0, 0.0, 0.0, -1.0, -1.0])
puts "x^5 - x - 1 = 0 の5解 (numeric solution formula):"
roots.each_with_index { |r, k| puts format("  x%d = %+.5f %+.5fi", k, r.real, r.imaginary) }
