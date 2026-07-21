# encoding: UTF-8
# frozen_string_literal: true
# Generate the app icon (icon.png, 1024x1024) with no image libraries — a pure
# Ruby PNG encoder (zlib only). Draws a Penrose "tensor box with index legs"
# glyph in the Bada palette (dark navy bg, gold box, cyan legs).
require "zlib"

W = H = 1024
BG   = [0x0b, 0x0e, 0x14]
GOLD = [0xc8, 0xa4, 0x4a]
CYAN = [0x40, 0xb8, 0xc0]
BLUE = [0x4a, 0x80, 0xd0]

# RGBA framebuffer
buf = Array.new(W * H) { BG + [255] }

def put(buf, x, y, c)
  return if x < 0 || y < 0 || x >= W || y >= H
  buf[y * W + x] = c + [255]
end

def rect(buf, x0, y0, x1, y1, c)
  (y0..y1).each { |y| (x0..x1).each { |x| put(buf, x, y, c) } }
end

# thick line (horizontal or vertical) of half-width t
def hline(buf, x0, x1, y, t, c) = rect(buf, x0, y - t, x1, y + t, c)
def vline(buf, x, y0, y1, t, c) = rect(buf, x - t, y0, x + t, y1, c)

# box outline (square ring) centered
cx = cy = 512
half = 250
tk = 26

# --- index legs (Penrose: lines leaving the tensor = indices) ---
# two legs top, three legs bottom, one each side — evokes a mixed tensor
vline(buf, cx - 120, 60, cy - half, 14, CYAN)
vline(buf, cx + 120, 60, cy - half, 14, CYAN)
vline(buf, cx - 150, cy + half, 964, 14, CYAN)
vline(buf, cx,       cy + half, 964, 14, CYAN)
vline(buf, cx + 150, cy + half, 964, 14, CYAN)
hline(buf, 60, cx - half, cy, 14, BLUE)
hline(buf, cx + half, 964, cy, 14, BLUE)

# --- tensor box (gold ring) ---
rect(buf, cx - half, cy - half, cx + half, cy - half + tk, GOLD) # top
rect(buf, cx - half, cy + half - tk, cx + half, cy + half, GOLD) # bottom
rect(buf, cx - half, cy - half, cx - half + tk, cy + half, GOLD) # left
rect(buf, cx + half - tk, cy - half, cx + half, cy + half, GOLD) # right

# --- inner mark: a small gold "R" bar cluster (result) ---
rect(buf, cx - 70, cy - 90, cx - 44, cy + 90, GOLD)          # R stem
rect(buf, cx - 70, cy - 90, cx + 40, cy - 64, GOLD)          # R top bar
rect(buf, cx - 70, cy - 10, cx + 40, cy + 16, GOLD)          # R mid bar
rect(buf, cx + 14, cy - 64, cx + 40, cy - 10, GOLD)          # R bowl right
# R leg (diagonal, stepped)
10.times { |i| rect(buf, cx - 40 + i * 8, cy + 16 + i * 8, cx - 14 + i * 8, cy + 42 + i * 8, GOLD) }

# ---- encode PNG ----
def chunk(type, data)
  out = [data.bytesize].pack("N") + type + data
  out + [Zlib.crc32(type + data)].pack("N")
end

raw = "".b
H.times do |y|
  raw << "\x00".b # filter type 0 (none)
  W.times do |x|
    px = buf[y * W + x]
    raw << px.pack("C4")
  end
end

png = "\x89PNG\r\n\x1a\n".b
ihdr = [W, H].pack("NN") + [8, 6, 0, 0, 0].pack("C5") # 8-bit, RGBA
png << chunk("IHDR", ihdr)
png << chunk("IDAT", Zlib::Deflate.deflate(raw, 9))
png << chunk("IEND", "")

path = File.expand_path("icon.png", __dir__)
File.binwrite(path, png)
puts "wrote #{path} (#{png.bytesize} bytes, #{W}x#{H} RGBA)"
