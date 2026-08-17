# frozen_string_literal: true

# Bada::QC — a von-Neumann *pseudo quantum computer* built in Bada.
#
# 「量子コンピューターの制御回路をモニターに投射」「PCのハードディスクの内部に電子回路を
#   シミュレーション」「ディスクメモリの内蔵シミュレーション」「ノイマン型の擬似量子
#   コンピューター」「量子コンピューターの半導体のソースコード」——を一つに束ねる。
#
#   Bada::QC::DiskMemory  disk-backed (HDD) von-Neumann memory: program + state
#   Bada::QC::Logic       CMOS/MOSFET NAND electronic-circuit simulation + decoder
#   Bada::QC::ISA         BadaQASM instruction set + stored-program encoding
#   Bada::QC::CPU         fetch-decode-execute control unit (uses the decoder sim)
#   Bada::QC::Monitor     projects the control circuit onto the monitor
#   Bada::QC::Verilog     emits the semiconductor (RTL) source code
#   Bada::QC::Machine     the whole machine as one facade
#
#   require "bada"
#   m = Bada::QC::Machine.bell
#   puts m.report

require_relative "qc/disk_memory"
require_relative "qc/logic"
require_relative "qc/isa"
require_relative "qc/cpu"
require_relative "qc/monitor"
require_relative "qc/verilog"
require_relative "qc/machine"

module Bada
  module QC
  end
end
