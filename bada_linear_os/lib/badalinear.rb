# frozen_string_literal: true

# BadaLinear-OS — 反重力リニア新幹線 オペレーティングシステム
#
# 超電導リニアの「超伝導磁石による浮上」を論文集の反重力（重力方程式の補空間
# エネルギー）に、「空気抵抗」を補空間包絡（真空エネルギー体 x^x のコホモロジー
# 切断）によるゼロ抗力に置き換え、BadaUFO-OS を生成AI車掌つきの鉄道 OS として
# Bada 言語で作り換えたもの。
#
#   require "badalinear"
#   os = BadaLinear::OS.new
#   puts os.boot
#   puts os.command("compare")
#   puts os.command("depart 1000")
#
# モジュール地図:
#   BadaLinear::Guideway   超伝導→反重力浮上・空気抵抗→補空間包絡・推進・時刻表
#   BadaLinear::Conductor  生成AI車掌（BadaUFO::Copilot の作り換え）
#   BadaLinear::OS         カーネル（status/physics/depart/route/compare/ask）
require_relative "badalinear/guideway"
require_relative "badalinear/os"

module BadaLinear
  VERSION = "1.0.0"
end
