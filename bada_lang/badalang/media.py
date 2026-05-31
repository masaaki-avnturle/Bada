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
