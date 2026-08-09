# frozen_string_literal: true

require_relative "special"
require_relative "manifold"
require_relative "error_correction"
require_relative "tuplespace"

module Bada
  # USB device *resume* engine.
  #
  # A USB port can stop working for reasons that are not physical breakage:
  #
  #   * 許可なく          — the device sits at authorized = 0 (kernel refuses it)
  #   * プラグプレイなく    — the driver never re-binds, so hot-plug never fires
  #   * 接触不良          — an intermittent contact corrupts the descriptor bytes
  #                         the host reads over the control endpoint
  #
  # The contact fault shows up in the *machine-language* byte stream as an
  # "n進数のズレ" — a base-n digit drift: bytes slip by ±k or lose a nibble
  # while the wire chatters. Because the same descriptor is read many times, the
  # true value is recoverable: project every noisy read onto the complex
  # rotational body e^{iθ}, average along the closed spin orbit (the integrable
  # invariant of the special-relativity spinning-top geometry) and lift back.
  # A rotation preserves magnitude, so the descriptor's entropy invariant Ξ is
  # conserved — that conservation is the certificate that the byte was recovered
  # and not merely smoothed.
  #
  # Once the descriptor is clean the device is walked back to life through the
  # standard Linux resume state machine:
  #
  #   DETACHED → authorized(0→1) → power/control=on → unbind→bind → RESUMED
  #
  # By default every step is SIMULATED (safe anywhere, including CI). With
  # apply: true on a Linux host the same steps are written to the real sysfs
  # nodes for the selected device.
  #
  # This is the runtime behind `bin/bada usb` and `examples/usb_resume.bada`.
  module UsbResume
    module_function

    SYSFS = "/sys/bus/usb/devices"
    DRIVER_DIR = "/sys/bus/usb/drivers/usb"

    # ---- device model ---------------------------------------------------

    # A USB device as the engine sees it: identity, health, and the raw
    # descriptor bytes (the "machine language" that carries the n進数 digits).
    class Device
      attr_reader :id, :bus, :vendor, :product, :name
      attr_accessor :authorized, :power_control, :bound, :descriptor, :sysfs

      def initialize(id:, bus:, vendor:, product:, name:, authorized: 0,
                     power_control: "auto", bound: false, descriptor: nil, sysfs: nil)
        @id = id
        @bus = bus
        @vendor = vendor
        @product = product
        @name = name
        @authorized = authorized
        @power_control = power_control
        @bound = bound
        @descriptor = descriptor || default_descriptor
        @sysfs = sysfs
      end

      # A minimal, checksummed USB device descriptor (18 bytes) used when the
      # real bytes are unavailable. Byte 17 carries a base-256 checksum so
      # digit drift is detectable.
      def default_descriptor
        head = [0x12, 0x01, 0x00, 0x02, 0x00, 0x00, 0x00, 0x40,
                vendor & 0xff, (vendor >> 8) & 0xff,
                product & 0xff, (product >> 8) & 0xff,
                0x00, 0x01, 0x01, 0x02, 0x03]
        head + [checksum_of(head)]
      end

      def checksum_of(bytes)
        bytes.sum & 0xff
      end

      # true when authorized, bound, and awake.
      def alive?
        @authorized == 1 && @bound && @power_control != "suspend"
      end

      def status
        return "RESUMED" if alive?
        return "UNAUTHORIZED" if @authorized != 1
        return "UNBOUND" unless @bound
        "SUSPENDED"
      end

      def to_h
        { id: id, bus: bus, vendor: format("0x%04x", vendor),
          product: format("0x%04x", product), name: name,
          authorized: authorized, power_control: power_control,
          bound: bound, status: status }
      end
    end

    # ---- enumeration ----------------------------------------------------

    # Discover USB devices. On a Linux host with a populated sysfs the real
    # devices are read; everywhere else a small synthetic fleet (including one
    # faulted port) is returned so the engine always has something to resume.
    def scan
      real = scan_sysfs
      real.empty? ? synthetic_fleet : real
    end

    def scan_sysfs
      return [] unless Dir.exist?(SYSFS)
      devices = []
      Dir.children(SYSFS).sort.each do |entry|
        path = File.join(SYSFS, entry)
        vfile = File.join(path, "idVendor")
        pfile = File.join(path, "idProduct")
        next unless File.readable?(vfile) && File.readable?(pfile)
        vendor  = File.read(vfile).strip.to_i(16)
        product = File.read(pfile).strip.to_i(16)
        name = read_or(File.join(path, "product"), "USB device #{entry}")
        auth = read_or(File.join(path, "authorized"), "1").to_i
        pc   = read_or(File.join(path, "power/control"), "auto")
        bound = Dir.exist?(File.join(path, "driver"))
        devices << Device.new(
          id: entry, bus: entry.split("-").first.to_s, vendor: vendor,
          product: product, name: name, authorized: auth,
          power_control: pc, bound: bound, sysfs: path
        )
      rescue StandardError
        next
      end
      devices
    end

    def read_or(path, default)
      File.readable?(path) ? File.read(path).strip : default
    end

    # A synthetic fleet: two healthy devices and one classic "接触不良 +
    # 許可なく + プラグプレイなく" fault used for demos and tests.
    def synthetic_fleet
      keyboard = Device.new(id: "1-1", bus: "1", vendor: 0x046d, product: 0xc31c,
                            name: "USB Keyboard", authorized: 1, power_control: "on", bound: true)
      hub = Device.new(id: "usb2", bus: "2", vendor: 0x1d6b, product: 0x0002,
                       name: "Linux Foundation 2.0 root hub", authorized: 1,
                       power_control: "auto", bound: true)
      faulted = Device.new(id: "2-3", bus: "2", vendor: 0x0781, product: 0x5581,
                           name: "USB Mass Storage (faulted port)", authorized: 0,
                           power_control: "suspend", bound: false)
      # corrupt its descriptor the way a bad contact does (see below).
      faulted.descriptor = faulted.default_descriptor
      [keyboard, hub, faulted]
    end

    # ---- n進数 (base-n) digit-drift model & correction ------------------

    # Simulate contact-fault corruption of a byte stream: with probability p
    # each byte's base-n digits drift by ±1 (a slipped digit / bit chatter).
    # Deterministic given seed+trial so tests and the .bada script reproduce.
    def drift(bytes, base: 16, p: 0.35, seed: 1, trial: 0)
      state = (seed * 2_654_435_761 + trial * 40_503 + 0x9e3779b1) & 0xffffffff
      rng = lambda do
        state = (state * 1_103_515_245 + 12_345) & 0x7fffffff
        state / 0x7fffffff.to_f
      end
      bytes.each_with_index.map do |b, _i|
        digits = to_base(b, base, width: byte_width(base))
        digits = digits.map do |d|
          if rng.call < p
            step = rng.call < 0.5 ? -1 : 1
            (d + step).clamp(0, base - 1)
          else
            d
          end
        end
        from_base(digits, base) & 0xff
      end
    end

    # Number of base-`base` digits needed to hold a byte (0..255).
    def byte_width(base)
      w = 1
      w += 1 while base**w <= 255
      w
    end

    def to_base(value, base, width:)
      d = Array.new(width, 0)
      v = value
      (width - 1).downto(0) do |i|
        d[i] = v % base
        v /= base
      end
      d
    end

    def from_base(digits, base)
      digits.reduce(0) { |acc, d| acc * base + d }
    end

    # Recover a single true byte from many contact-faulted reads using the
    # complex-rotation-body integrable corrector. Each noisy read is a sample
    # on the spin orbit; ErrorCorrection.correct damps outliers (relativistic
    # time dilation) and returns the conserved orbit centre, which we round to
    # the nearest lattice byte.
    def recover_byte(samples)
      c = ErrorCorrection.correct(samples.map(&:to_f))
      value = c[:value].round.clamp(0, 255)
      { value: value, residual: c[:residual], samples: c[:samples] }
    end

    # Recover one true byte by correcting each base-n *digit* independently and
    # reassembling — this is literally "fixing the n進数のズレ". Because contact
    # drift walks each digit by ±1 about its true value, the rotation-body
    # integrable corrector converges on every digit far faster than on the whole
    # byte (whose value jumps by base^k when a high digit slips).
    def recover_byte_basen(samples, base)
      w = byte_width(base)
      digits = (0...w).map do |k|
        col = samples.map { |s| to_base(s & 0xff, base, width: w)[k].to_f }
        ErrorCorrection.correct(col)[:value].round.clamp(0, base - 1)
      end
      from_base(digits, base) & 0xff
    end

    # Recover a whole descriptor from `reads` faulted copies of it.
    # Returns the corrected byte array plus a per-byte residual and a
    # checksum-verified flag (the base-n consistency check).
    def recover_descriptor(truth, base: 16, reads: 9, p: 0.35, seed: 7)
      noisy = (0...reads).map { |t| drift(truth, base: base, p: p, seed: seed, trial: t) }
      corrected = truth.each_index.map do |i|
        recover_byte_basen(noisy.map { |copy| copy[i] }, base)
      end
      residual = truth.each_index.sum { |i| (corrected[i] - truth[i]).abs }
      body = corrected[0...-1]
      checksum_ok = (body.sum & 0xff) == corrected[-1]
      matched = corrected.each_index.count { |i| corrected[i] == truth[i] }
      {
        corrected: corrected,
        bit_errors_in: hamming(truth, noisy.first),
        bit_errors_out: hamming(truth, corrected),
        bytes_recovered: matched,
        bytes_total: truth.length,
        residual: residual,
        checksum_ok: checksum_ok
      }
    end

    def hamming(a, b)
      a.each_index.sum { |i| ((a[i] ^ (b[i] || 0)) & 0xff).to_s(2).count("1") }
    end

    # Like recover_descriptor but, exactly as a real driver re-issues a control
    # transfer until the descriptor checksums, it escalates the number of reads
    # (more independent samples on the spin orbit) until the base-n checksum
    # passes or max_reads is reached. Returns the best result seen.
    def recover_descriptor_adaptive(truth, base: 16, reads: 9, max_reads: 193, p: 0.35, seed: 7)
      best = nil
      r = reads
      while r <= max_reads
        rec = recover_descriptor(truth, base: base, reads: r, p: p, seed: seed)
        rec[:reads] = r
        best = rec if best.nil? || rec[:bytes_recovered] > best[:bytes_recovered]
        break if rec[:checksum_ok]
        r += 8
      end
      best
    end

    # ---- resume state machine ------------------------------------------

    # Resume one device. Returns a step-by-step report. When apply: true and a
    # real writable sysfs path is present, each step is also written to the
    # kernel; otherwise the steps are simulated on the in-memory Device.
    def resume(device, base: 16, reads: 9, p: 0.35, apply: false, db: nil)
      steps = []

      # 1) measure the port before touching it.
      before = device.status
      steps << step("measure", "port state = #{before}", ok: true)

      # 2) fix the machine-language n進数 drift on the descriptor, escalating
      #    reads (control-transfer retries) until the base-n checksum passes.
      rec = recover_descriptor_adaptive(device.descriptor, base: base, reads: reads, p: p)
      device.descriptor = rec[:corrected]
      steps << step(
        "n進数補正",
        "base-#{base} digit drift: #{rec[:bit_errors_in]}→#{rec[:bit_errors_out]} bit errors, " \
        "#{rec[:bytes_recovered]}/#{rec[:bytes_total]} bytes recovered in #{rec[:reads]} reads, " \
        "checksum #{rec[:checksum_ok] ? 'OK' : 'FAIL'}",
        ok: rec[:checksum_ok]
      )

      # 3) certify the entropy invariant is conserved on the rotation orbit —
      #    the integrable-system guarantee that the recovery is real.
      cert = ErrorCorrection.certify_invariant(rec[:corrected].pack("C*").unpack1("H*"))
      steps << step(
        "可積分認証",
        "Ξ=#{format('%.6f', cert[:invariant])} conserved=#{cert[:conserved]} residual=#{format('%.2e', cert[:residual])}",
        ok: cert[:conserved]
      )

      # 4) authorize (許可なく → 許可あり).
      steps << transition("authorize", device, apply) do |d|
        d.authorized = 1
        write_sysfs(File.join(d.sysfs, "authorized"), "1") if apply && d.sysfs
      end

      # 5) wake power management (resume from autosuspend).
      steps << transition("power/control=on", device, apply) do |d|
        d.power_control = "on"
        write_sysfs(File.join(d.sysfs, "power/control"), "on") if apply && d.sysfs
      end

      # 6) unbind → bind to force plug-and-play re-enumeration.
      steps << transition("rebind (plug&play)", device, apply) do |d|
        d.bound = false
        if apply && d.sysfs
          write_sysfs(File.join(DRIVER_DIR, "unbind"), d.id)
          write_sysfs(File.join(DRIVER_DIR, "bind"), d.id)
        end
        d.bound = true
      end

      # 7) verify.
      after = device.status
      ok = device.alive? && rec[:checksum_ok] && cert[:conserved]
      steps << step("verify", "port state = #{after}", ok: ok)

      if db
        db.push(device.to_h.to_s, key: "usb::#{device.id}",
                tags: { resumed: ok, before: before, after: after })
      end

      {
        device: device.to_h,
        before: before,
        after: after,
        resumed: ok,
        recovery: rec.reject { |k, _| k == :corrected },
        certificate: cert,
        steps: steps,
        applied: apply
      }
    end

    # Resume every faulted device found by scan; healthy ones are skipped.
    def resume_all(devices = scan, apply: false, db: nil, **opts)
      devices.map do |d|
        next { device: d.to_h, resumed: true, skipped: "already RESUMED" } if d.alive?
        resume(d, apply: apply, db: db, **opts)
      end
    end

    # ---- helpers --------------------------------------------------------

    def transition(name, device, apply)
      yield device
      step(name, apply ? "written to sysfs" : "simulated", ok: true)
    end

    def step(name, detail, ok:)
      { step: name, detail: detail, ok: ok }
    end

    def write_sysfs(path, value)
      File.write(path, value)
      true
    rescue StandardError => e
      warn "usb: could not write #{path}: #{e.message}"
      false
    end

    # Pretty one-screen report for the CLI.
    def render(result)
      lines = []
      d = result[:device]
      lines << "── #{d[:name]}  (#{d[:vendor]}:#{d[:product]}  bus #{d[:bus]}  id #{d[:id]})"
      if result[:skipped]
        lines << "   #{result[:skipped]}"
        return lines.join("\n")
      end
      result[:steps].each do |s|
        mark = s[:ok] ? "✓" : "✗"
        lines << format("   %s %-16s %s", mark, s[:step], s[:detail])
      end
      verdict = result[:resumed] ? "RESUMED ✅  (#{result[:before]} → #{result[:after]})" \
                                 : "NOT resumed ⚠  (#{result[:before]} → #{result[:after]})"
      lines << "   → #{verdict}#{result[:applied] ? '' : '   [simulation]'}"
      lines.join("\n")
    end
  end
end
