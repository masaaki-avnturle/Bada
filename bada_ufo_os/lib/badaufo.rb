# frozen_string_literal: true

# BadaUFO-OS — 反重力UFOオペレーティングシステム / 生成AI操縦士
#
#   require "badaufo"
#   os = BadaUFO::OS.new
#   puts os.boot
#   puts os.command("physics")
#   puts os.command("ascend 8")
#   puts os.command("ask 反重力の原理は？")
#
# モジュール地図:
#   BadaUFO::SpecialBridge   Bada::Special への橋（□_ag, □_dal, e^π/π^e）
#   BadaUFO::Antigravity     反重力物理コア（重力/相対論の補空間・真空エネルギー）
#   BadaUFO::VacuumReservoir 無尽蔵の真空エネルギー体
#   BadaUFO::AntigravityDrive 反重力推進ドライブ
#   BadaUFO::Copilot         生成AI操縦士（Bada::Generator + Ω::DATABASE）
#   BadaUFO::OS              オペレーティングシステム・カーネル
require_relative "badaufo/special_bridge"
require_relative "badaufo/antigravity"
require_relative "badaufo/copilot"
require_relative "badaufo/os"

module BadaUFO
  VERSION = "1.0.0"
end
