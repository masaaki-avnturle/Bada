"""Native media backend for Bada: raster images, Netpbm savers and a
dependency-free animated-GIF encoder.

This is the low-level engine behind Bada's `image` and `video` standard
libraries.  It writes genuine, viewer-openable files:

  * grayscale  -> binary PGM (Netpbm "P5")
  * colour     -> binary PPM (Netpbm "P6")
  * animation  -> animated GIF89a, encoded here with a self-contained
                  LZW compressor (no Pillow / numpy required).

It also hosts `xray_project`, a fast native kernel for the Beer-Lambert line
integral used by the `xray` library — the "global partial integral manifold"
of the report's gamma operator algebra.
"""

import math


class Image:
    """A simple raster image: mode 'L' (grayscale) or 'RGB'."""

    def __init__(self, width, height, mode="L", fill=0):
        self.width = int(width)
        self.height = int(height)
        self.mode = mode
        chans = 3 if mode == "RGB" else 1
        self.channels = chans
        self.data = bytearray([fill & 0xFF]) * (self.width * self.height * chans)

    # --- pixel access -----------------------------------------------------

    def _idx(self, x, y):
        return (y * self.width + x) * self.channels

    def set(self, x, y, v):
        x = int(x); y = int(y)
        if 0 <= x < self.width and 0 <= y < self.height:
            i = self._idx(x, y)
            self.data[i] = _clamp8(v)

    def set_rgb(self, x, y, r, g, b):
        x = int(x); y = int(y)
        if 0 <= x < self.width and 0 <= y < self.height:
            i = self._idx(x, y)
            self.data[i] = _clamp8(r)
            self.data[i + 1] = _clamp8(g)
            self.data[i + 2] = _clamp8(b)

    def get(self, x, y):
        x = int(x); y = int(y)
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.data[self._idx(x, y)]
        return 0

    def fill(self, v):
        b = _clamp8(v)
        for i in range(len(self.data)):
            self.data[i] = b

    # --- saving -----------------------------------------------------------

    def save(self, path):
        if self.mode == "RGB" or path.lower().endswith(".ppm"):
            self._save_ppm(path)
        else:
            self._save_pgm(path)
        return path

    def _save_pgm(self, path):
        if self.mode == "RGB":
            gray = self.to_gray()
            gray._save_pgm(path)
            return
        header = f"P5\n{self.width} {self.height}\n255\n".encode("ascii")
        with open(path, "wb") as f:
            f.write(header)
            f.write(bytes(self.data))

    def _save_ppm(self, path):
        if self.mode != "RGB":
            rgb = self.to_rgb()
            rgb._save_ppm(path)
            return
        header = f"P6\n{self.width} {self.height}\n255\n".encode("ascii")
        with open(path, "wb") as f:
            f.write(header)
            f.write(bytes(self.data))

    # --- conversions ------------------------------------------------------

    def to_gray(self):
        if self.mode == "L":
            out = Image(self.width, self.height, "L")
            out.data = bytearray(self.data)
            return out
        out = Image(self.width, self.height, "L")
        for p in range(self.width * self.height):
            r = self.data[p * 3]; g = self.data[p * 3 + 1]; b = self.data[p * 3 + 2]
            out.data[p] = (r * 299 + g * 587 + b * 114) // 1000
        return out

    def to_rgb(self):
        if self.mode == "RGB":
            out = Image(self.width, self.height, "RGB")
            out.data = bytearray(self.data)
            return out
        out = Image(self.width, self.height, "RGB")
        for p in range(self.width * self.height):
            v = self.data[p]
            out.data[p * 3] = v; out.data[p * 3 + 1] = v; out.data[p * 3 + 2] = v
        return out

    def gray_bytes(self):
        """Return a w*h bytes buffer of grayscale indices (for GIF frames)."""
        return bytes(self.to_gray().data)

    def to_png_bytes(self):
        """Encode the image as PNG (grayscale or RGB) using stdlib zlib."""
        import zlib, struct
        w, h = self.width, self.height
        if self.mode == "RGB":
            ctype = 2
            stride = w * 3
            pix = bytes(self.data)
        else:
            ctype = 0
            stride = w
            pix = bytes(self.to_gray().data)
        rows = bytearray()
        for y in range(h):
            rows.append(0)
            rows += pix[y * stride:(y + 1) * stride]

        def chunk(typ, data):
            return (struct.pack(">I", len(data)) + typ + data
                    + struct.pack(">I", zlib.crc32(typ + data) & 0xffffffff))

        ihdr = struct.pack(">IIBBBBB", w, h, 8, ctype, 0, 0, 0)
        return (b"\x89PNG\r\n\x1a\n"
                + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", zlib.compress(bytes(rows), 9))
                + chunk(b"IEND", b""))

    def save_png(self, path):
        with open(path, "wb") as f:
            f.write(self.to_png_bytes())
        return path

    def data_uri(self):
        """Return a base64 PNG data: URI for embedding in HTML."""
        import base64
        b64 = base64.b64encode(self.to_png_bytes()).decode("ascii")
        return "data:image/png;base64," + b64

    def __repr__(self):
        return f"<image {self.mode} {self.width}x{self.height}>"


class GifWriter:
    """Collects grayscale frames and writes an animated GIF89a."""

    def __init__(self, path, width, height, delay_cs=10, loop=0):
        self.path = path
        self.width = int(width)
        self.height = int(height)
        self.delay = int(delay_cs)      # frame delay in centiseconds
        self.loop = int(loop)           # 0 = loop forever
        self.frames = []                # list of w*h grayscale-index bytes

    def add(self, image):
        if image.width != self.width or image.height != self.height:
            from .errors import BadaRuntimeError
            raise BadaRuntimeError(
                f"gif frame size {image.width}x{image.height} "
                f"!= {self.width}x{self.height}")
        self.frames.append(image.gray_bytes())
        return self

    def save(self):
        if not self.frames:
            from .errors import BadaRuntimeError
            raise BadaRuntimeError("gif has no frames")
        data = _encode_gif(self.frames, self.width, self.height,
                            self.delay, self.loop)
        with open(self.path, "wb") as f:
            f.write(data)
        return self.path

    def __repr__(self):
        return f"<gif {self.path!r} {len(self.frames)} frames>"


# --- X-ray projection kernel ----------------------------------------------
#
# Renders a radiograph by integrating the linear attenuation coefficient mu
# of a tissue manifold along vertical detector rays and applying the
# Beer-Lambert law.  Each tissue is an ellipse whose mu follows a normalised
# gamma-function radial profile  x^k e^{-x} / Gamma(k+1)  — the report's
# gamma-operator density across the differential manifold.

def _gamma_density(rr, shell, k, gamma_kp1):
    """Radial attenuation weight in [0,1] across a tissue's manifold.

    Built from the gamma operator's density.  The lower incomplete-gamma
    shape  P(k, x) = gammainc(k, x)/Gamma(k)  rises from 0 to 1 as the ray
    moves inward, so the interior is fully attenuating and the rim softens
    smoothly — a gamma-function edge profile rather than a rim spike.
    """
    if rr < 0:
        return 0.0
    if rr >= 1.0:
        return 0.0
    # inward coordinate: 0 at rim, large at centre
    x = (1.0 - rr) * (k + 1.0) / max(shell, 1e-6)
    if x <= 0:
        return 0.0
    # regularised lower incomplete gamma P(k+1, x) via series (k small here)
    return _lower_gamma_P(k + 1.0, x)


def _lower_gamma_P(s, x):
    """Regularised lower incomplete gamma P(s,x) = gamma(s,x)/Gamma(s)."""
    if x <= 0:
        return 0.0
    if x > s + 40:
        return 1.0
    # series expansion: x^s e^-x sum_{n} x^n / (s(s+1)...(s+n))
    term = 1.0 / s
    total = term
    n = 1
    while n < 200:
        term *= x / (s + n)
        total += term
        if term < total * 1e-12:
            break
        n += 1
    val = total * math.exp(-x + s * math.log(x) - math.lgamma(s))
    if val > 1.0:
        return 1.0
    return val


def xray_project(image, tissues, i0, samples, soft, edge):
    """Fill `image` (mode 'L') with a radiograph of `tissues`.

    tissues: list of (cx, cy, rx, ry, mu, k) tuples — ellipses on the film
    plane, each with a peak attenuation `mu` and a gamma-profile shape `k`.

    Each pixel (x,y) is an INDEPENDENT detector: its ray travels along the
    depth axis z (into the film) through the tissue manifold.  At (x,y) the
    ray crosses each tissue over a chord whose half-length is the ellipse's
    local depth; the line integral of mu over that chord is

        ∫_ray mu dz  =  sum_t  mu_t * gammaProfile_t(r) * 2*depth_t(x,y)

    which is exactly the report's global partial-integral manifold of the
    gamma operator.  Beer-Lambert then gives the surviving beam
    I = I0 exp(-∫mu); the film-negative density 255-I (plus an edge term that
    sharpens bone rims) is written to the pixel.  Independent rays make lungs
    read dark and bone bright, as in a real chest radiograph.
    """
    w, h = image.width, image.height
    prepared = []
    for (cx, cy, rx, ry, mu, k) in tissues:
        prepared.append((float(cx), float(cy), float(rx), float(ry),
                         float(mu), float(k), math.gamma(k + 1.0)))
    data = image.data
    for y in range(h):
        row = y * w
        for x in range(w):
            integral = 0.0
            mrim = 0.0
            for (cx, cy, rx, ry, mu, k, gkp1) in prepared:
                nx = (x - cx) / rx
                ny = (y - cy) / ry
                rr2 = nx * nx + ny * ny
                if rr2 <= 1.0:
                    rr = math.sqrt(rr2)
                    # depth of the ellipsoid chord at this (x,y): goes to 0 at
                    # the rim, max at the centre — the z-extent of the manifold
                    depth = math.sqrt(1.0 - rr2)
                    dens = mu * _gamma_density(rr, 0.8, k, gkp1)
                    integral += dens * depth * 2.0
                    if dens > mrim:
                        mrim = dens
            surviving = i0 * math.exp(-soft * integral)
            v = (i0 - surviving) + edge * mrim
            data[row + x] = _clamp8(v)
    return image


# --- binaural soundscape kernel --------------------------------------------

def binaural_soundscape(carrier, beat, relief, duration, rate):
    """Native synth of a psychotropic biofeedback soundscape (stereo).

    Returns (left, right) lists of float samples.  Left ear plays `carrier`,
    right ear `carrier + beat`; the perceived beat entrains the target EEG
    band.  As `relief` rises the timbre warms (low overtone in, high shimmer
    out) and a slow beat-locked swell gives a breathing feel.
    """
    rate = int(rate)
    n = int(duration * rate)
    if n <= 0:
        return [], []
    tension = 1.0 - relief
    two_pi = 2.0 * math.pi
    left = [0.0] * n
    right = [0.0] * n
    # simple LCG noise bed state
    s = 12345
    prev = 0.0
    inv_rate = 1.0 / rate
    inv_n = 1.0 / n
    warm_amp = 0.30 * relief
    shim_amp = 0.12 * tension
    bed_amp = 0.08 * (0.5 + 0.5 * tension)
    for i in range(n):
        t = i * inv_rate
        env = math.sin(math.pi * i * inv_n)          # fade in/out
        # binaural carriers
        l = 0.5 * env * math.sin(two_pi * carrier * t)
        r = 0.5 * env * math.sin(two_pi * (carrier + beat) * t)
        # warm low overtone (richer as relief rises)
        warm = warm_amp * env * math.sin(two_pi * (carrier * 0.5) * t)
        # tense high shimmer (fades with relief)
        shim = shim_amp * env * math.sin(two_pi * (carrier * 4.0) * t)
        # soft noise bed
        s = (s * 1103515245 + 12345) % 2147483648
        white = (s / 1073741824.0) - 1.0
        prev = prev * 0.96 + white * 0.04
        bed = bed_amp * prev
        # slow beat-locked swell
        lfo = (1.0 + math.sin(two_pi * (beat / 10.0) * t)) / 2.0
        g = 0.55 + 0.45 * lfo
        left[i] = (l + warm + shim + bed) * g
        right[i] = (r + warm + shim + bed) * g
    _normalize_inplace(left, 0.9)
    _normalize_inplace(right, 0.9)
    return left, right


def _normalize_inplace(buf, peak):
    mx = 0.0
    for v in buf:
        a = v if v >= 0 else -v
        if a > mx:
            mx = a
    if mx == 0:
        return
    g = peak / mx
    for i in range(len(buf)):
        buf[i] *= g


# --- CT: Radon transform & filtered back-projection ------------------------
#
# A CT scan recovers a cross-section from its projections.  For each angle the
# scanner measures the LINE INTEGRAL of attenuation along every ray — the
# Radon transform.  Taken over all angles this is the "global partial integral
# manifold" of the gamma operator across the body cross-section.  Inverting it
# (filtered back-projection) reconstructs the slice.

def ct_sinogram(image, n_angles):
    """Forward Radon transform of a grayscale image -> sinogram image.

    Output: an Image of width=n_detectors, height=n_angles; each row is the
    parallel-beam projection (line integrals) of the slice at one angle.
    """
    w, h = image.width, image.height
    cx = (w - 1) / 2.0
    cy = (h - 1) / 2.0
    n_det = int(math.ceil(math.hypot(w, h)))
    det_c = (n_det - 1) / 2.0
    src = image.data
    sino = Image(n_det, n_angles, "L")
    raw = [0.0] * (n_det * n_angles)
    peak = 1e-9
    for ai in range(n_angles):
        theta = math.pi * ai / n_angles
        ct = math.cos(theta)
        st = math.sin(theta)
        base = ai * n_det
        for y in range(h):
            dy = y - cy
            for x in range(w):
                v = src[y * w + x]
                if v == 0:
                    continue
                t = (x - cx) * ct + dy * st + det_c
                ti = int(t)
                if 0 <= ti < n_det:
                    raw[base + ti] += v
        for d in range(n_det):
            if raw[base + d] > peak:
                peak = raw[base + d]
    scale = 255.0 / peak
    sd = sino.data
    for i in range(n_det * n_angles):
        sd[i] = _clamp8(raw[i] * scale)
    return sino


def _ramp_filter(row, n):
    """Apply a discrete Ram-Lak ramp high-pass to one projection row."""
    # Ram-Lak spatial kernel: h[0]=1/4, h[odd]=-1/(pi^2 k^2), h[even]=0
    out = [0.0] * n
    half = 32
    for i in range(n):
        acc = row[i] * 0.25
        for k in range(1, half):
            if k % 2 == 1:
                hk = -1.0 / (math.pi * math.pi * k * k)
                li = i - k
                ri = i + k
                if li >= 0:
                    acc += hk * row[li]
                if ri < n:
                    acc += hk * row[ri]
        out[i] = acc
    return out


def ct_reconstruct(image, n_angles, filtered):
    """Full CT: forward-project `image` then filtered back-projection.

    Returns the reconstructed Image (same size as input).  When `filtered` is
    true a ramp filter sharpens the projections (true FBP); otherwise plain
    back-projection (blurred) is returned.
    """
    w, h = image.width, image.height
    cx = (w - 1) / 2.0
    cy = (h - 1) / 2.0
    n_det = int(math.ceil(math.hypot(w, h)))
    det_c = (n_det - 1) / 2.0
    src = image.data

    # forward project into float rows
    rows = []
    for ai in range(n_angles):
        theta = math.pi * ai / n_angles
        ct = math.cos(theta); st = math.sin(theta)
        proj = [0.0] * n_det
        for y in range(h):
            dy = y - cy
            for x in range(w):
                v = src[y * w + x]
                if v:
                    t = (x - cx) * ct + dy * st + det_c
                    ti = int(t)
                    if 0 <= ti < n_det:
                        proj[ti] += v
        if filtered:
            proj = _ramp_filter(proj, n_det)
        rows.append((proj, ct, st))

    # back-project
    recon = [0.0] * (w * h)
    for (proj, ct, st) in rows:
        for y in range(h):
            dy = y - cy
            base = y * w
            for x in range(w):
                t = (x - cx) * ct + dy * st + det_c
                ti = int(t)
                if 0 <= ti < n_det:
                    recon[base + x] += proj[ti]

    # normalise to 8-bit
    mn = min(recon); mx = max(recon)
    rng = (mx - mn) or 1.0
    out = Image(w, h, "L")
    od = out.data
    for i in range(w * h):
        od[i] = _clamp8((recon[i] - mn) / rng * 255.0)
    return out


# --- ultrasound B-mode sector scan -----------------------------------------
#
# Pulse-echo imaging: from a transducer apex, scan lines fan out across a
# sector.  Each pixel's brightness is the local acoustic-impedance interface
# strength (the gradient of the tissue map) attenuated with depth (time-gain
# compensation) and modulated by multiplicative speckle — the characteristic
# grainy ultrasound texture.

def ultrasound_bmode(src, out, apex_x, apex_y, max_r, half_angle,
                     center_angle, atten, seed):
    w, h = src.width, src.height
    sd = src.data
    od = out.data
    s = int(seed) & 0x7fffffff
    two_pi = 2.0 * math.pi
    for y in range(h):
        for x in range(w):
            dx = x - apex_x
            dy = y - apex_y
            r = math.hypot(dx, dy)
            od_i = y * w + x
            if r < 1 or r > max_r:
                od[od_i] = 0
                continue
            ang = math.atan2(dy, dx)
            da = ang - center_angle
            while da > math.pi:
                da -= two_pi
            while da < -math.pi:
                da += two_pi
            if da < -half_angle or da > half_angle:
                od[od_i] = 0
                continue
            # interface strength = gradient magnitude of the tissue map
            xi = int(x); yi = int(y)
            if 0 < xi < w - 1 and 0 < yi < h - 1:
                gx = sd[yi * w + xi + 1] - sd[yi * w + xi - 1]
                gy = sd[(yi + 1) * w + xi] - sd[(yi - 1) * w + xi]
                grad = math.sqrt(gx * gx + gy * gy)
            else:
                grad = 0.0
            base = sd[od_i] * 0.12          # faint tissue echo
            echo = base + grad * 1.1
            # time-gain compensation: brighten with depth to offset attenuation
            tgc = math.exp(-atten * r) * (1.0 + r / max_r)
            # multiplicative speckle (Rayleigh-ish via LCG noise)
            s = (s * 1103515245 + 12345) & 0x7fffffff
            sp = 0.55 + 0.9 * (s / 2147483648.0)
            od[od_i] = _clamp8(echo * tgc * sp)
    return out


# --- endoscope tunnel view -------------------------------------------------
#
# A fibre-optic endoscope sees down a mucosal lumen: a circular field of view,
# a dark vanishing hole at the centre, pink mucosa receding in perspective,
# circular haustral folds, fine vessels and a bright specular reflection from
# the scope light.  Rendered in polar coordinates into an RGB image.

def endoscope_view(out, seed):
    w, h = out.width, out.height
    cx = (w - 1) / 2.0
    cy = (h - 1) / 2.0
    radius = min(w, h) / 2.0 - 1
    s = int(seed) & 0x7fffffff
    # specular highlight position (scope light), offset up-left
    hlx = cx - radius * 0.30
    hly = cy - radius * 0.30
    for y in range(h):
        for x in range(w):
            dx = x - cx
            dy = y - cy
            rr = math.hypot(dx, dy)
            idx = y * w + x
            if rr > radius:
                out.set_rgb(x, y, 0, 0, 0)
                continue
            ang = math.atan2(dy, dx)
            # perspective depth: centre = deep (dark), rim = near (bright)
            t = rr / radius                      # 0 centre .. 1 rim
            depth = 1.0 / (t + 0.12)             # large near centre
            # mucosa base brightness brightens toward the rim (vignette)
            vig = t * t
            # haustral folds: bright rings receding in depth
            folds = 0.5 + 0.5 * math.sin(depth * 3.0 + ang * 0.0)
            # vessel network: thin dark sinusoidal striae
            vessel = math.sin(ang * 7.0 + depth * 2.0)
            vfac = 1.0 - 0.35 * max(0.0, vessel - 0.6) / 0.4
            # speckle
            s = (s * 1103515245 + 12345) & 0x7fffffff
            sp = 0.85 + 0.3 * (s / 2147483648.0)
            base = (0.25 + 0.75 * vig) * (0.6 + 0.4 * folds) * vfac * sp
            # specular highlight
            hd = math.hypot(x - hlx, y - hly)
            spec = math.exp(-(hd * hd) / (2 * (radius * 0.10) ** 2))
            lum = base * 0.85 + spec * 0.9
            if lum > 1.0:
                lum = 1.0
            # mucosa colour: warm pink-red
            r = lum * 235
            g = lum * 120 + spec * 90
            b = lum * 120 + spec * 90
            out.set_rgb(x, y, int(r), int(g), int(b))
    return out


# --- neural / entropy field kernel -----------------------------------------
#
# Renders a scalar field sampled from Gaussian/gamma "activity sources" over a
# manifold, optionally converted to a local thermal-entropy reading.  This is
# the fast backend for the brain-imaging library: MRI anatomy, fMRI BOLD
# activation and EEG/topography scalp fields are all such fields.

def _digamma(x):
    """Digamma psi(x) for x > 0 (used for gamma-manifold entropy)."""
    result = 0.0
    while x < 6.0:
        result -= 1.0 / x
        x += 1.0
    f = 1.0 / (x * x)
    result += math.log(x) + 0.5 / x - f * (
        1.0 / 12 - f * (1.0 / 120 - f * (1.0 / 252)))
    return result


def gamma_manifold_entropy(k, theta):
    """Differential (thermal) entropy of a Gamma(k, theta) manifold:

        S = k + ln(theta) + ln Gamma(k) + (1 - k) psi(k)

    This is the heat-entropy value of the report's global partial-integral
    manifold of the gamma operator, used to weight neural activity.
    """
    if k <= 0 or theta <= 0:
        return 0.0
    return k + math.log(theta) + math.lgamma(k) + (1.0 - k) * _digamma(k)


def field_project(image, sources, base, gain, entropy_flag):
    """Render a scalar field of `sources` into a grayscale `image`.

    sources: list of (cx, cy, sigma, amp, k) — a localised activity blob whose
    spatial falloff is Gaussian (sigma) and whose strength `amp` is modulated
    by the gamma-manifold entropy of shape `k` when entropy_flag is set.

    The pixel value is  base + gain * field(x,y)  clamped to 8 bits.
    """
    w, h = image.width, image.height
    prepared = []
    for src in sources:
        cx, cy, sigma, amp, k = src
        s = float(sigma)
        if s < 1e-6:
            s = 1e-6
        weight = float(amp)
        if entropy_flag:
            # scale activity by the gamma manifold's thermal entropy
            ent = gamma_manifold_entropy(float(k), 1.0)
            weight *= (1.0 + 0.5 * ent)
        prepared.append((float(cx), float(cy), 1.0 / (2.0 * s * s), weight))
    data = image.data
    for y in range(h):
        row = y * w
        for x in range(w):
            acc = 0.0
            for (cx, cy, inv2s2, weight) in prepared:
                dx = x - cx
                dy = y - cy
                acc += weight * math.exp(-(dx * dx + dy * dy) * inv2s2)
            data[row + x] = _clamp8(base + gain * acc)
    return image


# --- audio: PCM WAV writer -------------------------------------------------
#
# Turns a list of float samples in [-1, 1] into a real, playable 16-bit mono
# WAV file — the backend for Bada's auditory biofeedback.

def write_wav(path, samples, rate):
    import struct as _struct
    rate = int(rate)
    frames = bytearray()
    for s in samples:
        if s > 1.0:
            s = 1.0
        elif s < -1.0:
            s = -1.0
        frames += _struct.pack("<h", int(s * 32767.0))
    data_size = len(frames)
    byte_rate = rate * 2
    with open(path, "wb") as f:
        f.write(b"RIFF")
        f.write(_struct.pack("<I", 36 + data_size))
        f.write(b"WAVE")
        f.write(b"fmt ")
        f.write(_struct.pack("<IHHIIHH", 16, 1, 1, rate, byte_rate, 2, 16))
        f.write(b"data")
        f.write(_struct.pack("<I", data_size))
        f.write(bytes(frames))
    return path


def write_wav_stereo(path, left, right, rate):
    """Write a 16-bit stereo WAV from two float channels in [-1, 1].

    Used for binaural-beat biofeedback: a slightly different tone in each ear
    produces a perceived beat at the difference frequency, entraining the
    listener toward a target brain-wave band.
    """
    import struct as _struct
    rate = int(rate)
    n = min(len(left), len(right))
    frames = bytearray()
    for i in range(n):
        l = left[i]
        r = right[i]
        if l > 1.0:
            l = 1.0
        elif l < -1.0:
            l = -1.0
        if r > 1.0:
            r = 1.0
        elif r < -1.0:
            r = -1.0
        frames += _struct.pack("<hh", int(l * 32767.0), int(r * 32767.0))
    data_size = len(frames)
    byte_rate = rate * 2 * 2          # 2 channels, 2 bytes each
    block_align = 2 * 2
    with open(path, "wb") as f:
        f.write(b"RIFF")
        f.write(_struct.pack("<I", 36 + data_size))
        f.write(b"WAVE")
        f.write(b"fmt ")
        f.write(_struct.pack("<IHHIIHH", 16, 1, 2, rate, byte_rate,
                             block_align, 16))
        f.write(b"data")
        f.write(_struct.pack("<I", data_size))
        f.write(bytes(frames))
    return path


# --- 5x7 bitmap font & text drawing ----------------------------------------

_FONT = {
    " ": ["     "] * 7,
    "A": [" ### ", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"],
    "B": ["#### ", "#   #", "#### ", "#   #", "#   #", "#   #", "#### "],
    "C": [" ### ", "#   #", "#    ", "#    ", "#    ", "#   #", " ### "],
    "D": ["#### ", "#   #", "#   #", "#   #", "#   #", "#   #", "#### "],
    "E": ["#####", "#    ", "#### ", "#    ", "#    ", "#    ", "#####"],
    "F": ["#####", "#    ", "#### ", "#    ", "#    ", "#    ", "#    "],
    "G": [" ### ", "#   #", "#    ", "# ###", "#   #", "#   #", " ### "],
    "H": ["#   #", "#   #", "#####", "#   #", "#   #", "#   #", "#   #"],
    "I": [" ### ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "],
    "J": ["  ###", "   # ", "   # ", "   # ", "#  # ", "#  # ", " ##  "],
    "K": ["#   #", "#  # ", "# #  ", "##   ", "# #  ", "#  # ", "#   #"],
    "L": ["#    ", "#    ", "#    ", "#    ", "#    ", "#    ", "#####"],
    "M": ["#   #", "## ##", "# # #", "#   #", "#   #", "#   #", "#   #"],
    "N": ["#   #", "##  #", "# # #", "#  ##", "#   #", "#   #", "#   #"],
    "O": [" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "],
    "P": ["#### ", "#   #", "#   #", "#### ", "#    ", "#    ", "#    "],
    "Q": [" ### ", "#   #", "#   #", "#   #", "# # #", "#  # ", " ## #"],
    "R": ["#### ", "#   #", "#   #", "#### ", "# #  ", "#  # ", "#   #"],
    "S": [" ####", "#    ", "#    ", " ### ", "    #", "    #", "#### "],
    "T": ["#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "],
    "U": ["#   #", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "],
    "V": ["#   #", "#   #", "#   #", "#   #", "#   #", " # # ", "  #  "],
    "W": ["#   #", "#   #", "#   #", "# # #", "# # #", "## ##", "#   #"],
    "X": ["#   #", "#   #", " # # ", "  #  ", " # # ", "#   #", "#   #"],
    "Y": ["#   #", "#   #", " # # ", "  #  ", "  #  ", "  #  ", "  #  "],
    "Z": ["#####", "    #", "   # ", "  #  ", " #   ", "#    ", "#####"],
    "0": [" ### ", "#   #", "#  ##", "# # #", "##  #", "#   #", " ### "],
    "1": ["  #  ", " ##  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "],
    "2": [" ### ", "#   #", "    #", "   # ", "  #  ", " #   ", "#####"],
    "3": ["#####", "   # ", "  #  ", "   # ", "    #", "#   #", " ### "],
    "4": ["   # ", "  ## ", " # # ", "#  # ", "#####", "   # ", "   # "],
    "5": ["#####", "#    ", "#### ", "    #", "    #", "#   #", " ### "],
    "6": [" ### ", "#    ", "#    ", "#### ", "#   #", "#   #", " ### "],
    "7": ["#####", "    #", "   # ", "  #  ", " #   ", " #   ", " #   "],
    "8": [" ### ", "#   #", "#   #", " ### ", "#   #", "#   #", " ### "],
    "9": [" ### ", "#   #", "#   #", " ####", "    #", "    #", " ### "],
    ".": ["     ", "     ", "     ", "     ", "     ", "  ## ", "  ## "],
    ",": ["     ", "     ", "     ", "     ", "  ## ", "  ## ", " #   "],
    ":": ["     ", "  ## ", "  ## ", "     ", "  ## ", "  ## ", "     "],
    "-": ["     ", "     ", "     ", "#####", "     ", "     ", "     "],
    "+": ["     ", "  #  ", "  #  ", "#####", "  #  ", "  #  ", "     "],
    "/": ["    #", "    #", "   # ", "  #  ", " #   ", "#    ", "#    "],
    "%": ["##  #", "##  #", "   # ", "  #  ", " #   ", "#  ##", "#  ##"],
    "(": ["  ## ", " #   ", "#    ", "#    ", "#    ", " #   ", "  ## "],
    ")": [" ##  ", "   # ", "    #", "    #", "    #", "   # ", " ##  "],
    "!": ["  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "     ", "  #  "],
    "=": ["     ", "     ", "#####", "     ", "#####", "     ", "     "],
    "#": [" # # ", " # # ", "#####", " # # ", "#####", " # # ", " # # "],
    "*": ["     ", "# # #", " ### ", "#####", " ### ", "# # #", "     "],
    ">": ["#    ", " #   ", "  #  ", "   # ", "  #  ", " #   ", "#    "],
}


def draw_text(image, x, y, text, value, scale=1):
    """Draw `text` with the built-in 5x7 font at (x, y), each dot `scale` px."""
    x = int(x); y = int(y); scale = max(1, int(scale))
    cx = x
    for ch in str(text).upper():
        glyph = _FONT.get(ch)
        if glyph is None:
            cx += 6 * scale
            continue
        for ry in range(7):
            rowbits = glyph[ry]
            for rx in range(5):
                if rowbits[rx] != " ":
                    for sy in range(scale):
                        for sx in range(scale):
                            image.set(cx + rx * scale + sx, y + ry * scale + sy, value)
        cx += 6 * scale
    return cx


def draw_text_rgb(image, x, y, text, r, g, b, scale=1):
    """Draw coloured text with the 5x7 font onto an RGB image."""
    x = int(x); y = int(y); scale = max(1, int(scale))
    cx = x
    for ch in str(text).upper():
        glyph = _FONT.get(ch)
        if glyph is None:
            cx += 6 * scale
            continue
        for ry in range(7):
            rowbits = glyph[ry]
            for rx in range(5):
                if rowbits[rx] != " ":
                    for sy in range(scale):
                        for sx in range(scale):
                            image.set_rgb(cx + rx * scale + sx,
                                          y + ry * scale + sy, r, g, b)
        cx += 6 * scale
    return cx


def text_width(text, scale=1):
    return len(str(text)) * 6 * int(scale)


# --- helpers ---------------------------------------------------------------

def _clamp8(v):
    v = int(v)
    if v < 0:
        return 0
    if v > 255:
        return 255
    return v


# --- animated GIF89a encoder (self-contained LZW) --------------------------

class _BitWriter:
    """Packs variable-width codes LSB-first, as GIF requires."""

    def __init__(self):
        self.out = bytearray()
        self.cur = 0
        self.nbits = 0

    def write(self, code, size):
        self.cur |= (code << self.nbits)
        self.nbits += size
        while self.nbits >= 8:
            self.out.append(self.cur & 0xFF)
            self.cur >>= 8
            self.nbits -= 8

    def flush(self):
        if self.nbits > 0:
            self.out.append(self.cur & 0xFF)
            self.cur = 0
            self.nbits = 0


def _lzw_compress(indices, min_code_size):
    clear_code = 1 << min_code_size
    end_code = clear_code + 1

    def fresh_table():
        table = {(i,): i for i in range(clear_code)}
        return table, clear_code + 2, min_code_size + 1

    bits = _BitWriter()
    table, next_code, code_size = fresh_table()
    bits.write(clear_code, code_size)

    buf = ()
    for px in indices:
        nb = buf + (px,)
        if nb in table:
            buf = nb
        else:
            bits.write(table[buf], code_size)
            table[nb] = next_code
            next_code += 1
            if next_code == (1 << code_size) and code_size < 12:
                code_size += 1
            elif next_code == 4096:
                bits.write(clear_code, code_size)
                table, next_code, code_size = fresh_table()
            buf = (px,)
    bits.write(table[buf], code_size)
    bits.write(end_code, code_size)
    bits.flush()
    return bits.out


def _sub_blocks(data):
    out = bytearray()
    i = 0
    n = len(data)
    while i < n:
        chunk = data[i:i + 255]
        out.append(len(chunk))
        out.extend(chunk)
        i += 255
    out.append(0)  # block terminator
    return out


def _encode_gif(frames, width, height, delay, loop):
    out = bytearray()
    out.extend(b"GIF89a")

    # logical screen descriptor: global grayscale colour table, 256 entries
    out.extend(width.to_bytes(2, "little"))
    out.extend(height.to_bytes(2, "little"))
    out.append(0xF7)   # GCT present, colour res 8, 2^(7+1)=256 entries
    out.append(0)      # background colour index
    out.append(0)      # pixel aspect ratio

    # global colour table: identity grayscale ramp
    for i in range(256):
        out.extend(bytes((i, i, i)))

    # NETSCAPE2.0 looping extension
    out.extend(b"\x21\xFF\x0B")
    out.extend(b"NETSCAPE2.0")
    out.extend(b"\x03\x01")
    out.extend((loop & 0xFFFF).to_bytes(2, "little"))
    out.append(0)

    min_code_size = 8
    for frame in frames:
        # graphic control extension (per-frame delay)
        out.extend(b"\x21\xF9\x04")
        out.append(0x00)                       # no transparency, disposal 0
        out.extend((delay & 0xFFFF).to_bytes(2, "little"))
        out.append(0)                          # transparent colour index
        out.append(0)                          # block terminator

        # image descriptor
        out.append(0x2C)
        out.extend((0).to_bytes(2, "little"))  # left
        out.extend((0).to_bytes(2, "little"))  # top
        out.extend(width.to_bytes(2, "little"))
        out.extend(height.to_bytes(2, "little"))
        out.append(0x00)                       # no local colour table

        out.append(min_code_size)
        compressed = _lzw_compress(frame, min_code_size)
        out.extend(_sub_blocks(compressed))

    out.append(0x3B)  # trailer
    return bytes(out)
