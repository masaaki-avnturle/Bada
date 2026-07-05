# frozen_string_literal: true

# omega_iq — Bada 赤外線IQ・テロメア分裂測定エンジン
#
#   絵 → 方程式 → Jones多項式 → テロメア分裂 → 赤外線/温度計 → IQ (順 + 真逆)
require_relative "omega_iq/jones"
require_relative "omega_iq/drawing"
require_relative "omega_iq/telomere"
require_relative "omega_iq/thermal"
require_relative "omega_iq/iq"
require_relative "omega_iq/pipeline"
require_relative "omega_iq/bada_runtime"

module OmegaIQ
  VERSION = "0.1.0"
end
