# frozen_string_literal: true

module Bada
  module Quantum
    # The semiconductor realisability principle (半導体で使える原理).
    #
    # For the telegraph to be buildable, the entangled pair must come from
    # something you can fabricate: a semiconductor quantum dot emitting a
    # polarization-entangled photon pair via the biexciton–exciton cascade, with
    # spin qubits read through the band structure. Two textbook relations decide
    # whether that hardware works at a given temperature:
    #
    #   * Fermi–Dirac occupation  f(E) = 1 / (1 + exp((E-μ)/kT))  — thermal
    #     population of carrier states; thermal excitation across the gap is the
    #     dominant qubit error source.
    #   * WKB tunnelling  T ≈ exp(-2 κ d),  κ = sqrt(2 m ΔE)/ħ  — how well a
    #     read/coupling barrier passes the carrier.
    #
    # We work in electron-volts with kT in eV so no SI juggling is needed, and
    # turn the thermal excitation into the channel's bit-flip probability.
    module Semiconductor
      module_function

      KB_EV = 8.617333262e-5 # Boltzmann constant in eV/K

      # A few representative direct-gap materials (eV) used for entangled-photon
      # sources / spin qubits.
      BAND_GAPS = {
        "GaAs"   => 1.42,
        "InAs"   => 0.354,
        "InGaAs" => 0.75,
        "Si"     => 1.12,
        "diamond(NV)" => 5.47
      }.freeze

      def kT(temp_k)
        KB_EV * temp_k
      end

      # Fermi–Dirac occupation of a state at energy E (eV) with chemical
      # potential mu (eV) at temperature T (K).
      def fermi_dirac(energy_ev, mu_ev, temp_k)
        x = (energy_ev - mu_ev) / kT(temp_k)
        x = 700.0 if x > 700.0 # avoid overflow
        x = -700.0 if x < -700.0
        1.0 / (1.0 + Math.exp(x))
      end

      # Thermal excitation probability across the gap (μ at mid-gap): the qubit
      # bit-flip probability from the lattice bath.
      def thermal_flip(material, temp_k)
        eg = BAND_GAPS.fetch(material)
        # occupation of the conduction edge with mu at mid-gap
        fermi_dirac(eg, eg / 2.0, temp_k)
      end

      # WKB tunnelling transmission through a barrier of height ΔE (eV) and
      # width d (nm) for an electron (m = m_e).
      def tunnelling(barrier_ev, width_nm)
        # κ [1/nm] = sqrt(2 m ΔE)/ħ ; with ΔE in eV this is ≈ 5.123 * sqrt(ΔE)
        kappa = 5.123 * Math.sqrt([barrier_ev, 0.0].max)
        Math.exp(-2.0 * kappa * width_nm)
      end

      # Feasibility report for a chosen material at operating temperature.
      def report(material: "GaAs", temp_k: 4.0, barrier_ev: 0.3, width_nm: 5.0)
        flip = thermal_flip(material, temp_k)
        {
          material: material,
          band_gap_ev: BAND_GAPS.fetch(material),
          temperature_k: temp_k,
          kT_ev: kT(temp_k),
          bit_flip_prob: flip,
          tunnelling: tunnelling(barrier_ev, width_nm),
          # a channel is "buildable" if thermal errors are correctable (<10%)
          feasible: flip < 0.1
        }
      end
    end
  end
end
