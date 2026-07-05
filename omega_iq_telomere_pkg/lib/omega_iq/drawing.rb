# frozen_string_literal: true

module OmegaIQ
  # 絵を方程式化する — turn the drawing into equations, then into a knot diagram.
  #
  # The drawing is a set of straight line segments ("bonds" of the molecular
  # picture, or strands of a knot). The RED ARROW gives a traversal ORDER over
  # those segments. We:
  #
  #   1. read the segments in red-arrow order as one closed polyline,
  #   2. emit the parametric line equation of every segment,
  #   3. find every proper self-intersection of the polyline (the crossings),
  #   4. build a planar-diagram (PD) code, orienting each crossing by the
  #      arrow direction (its sign) and alternating over/under along the walk.
  #
  # The PD code produced here is exactly what OmegaIQ::Jones consumes.
  #
  # Asset format (assets/diagram_arrows.txt):
  #   # segments:  id x1 y1 x2 y2
  #   S 0 0.0 0.0 2.0 2.0
  #   ...
  #   # arrow order (red arrow): the sequence the segments are traversed in
  #   ARROW 0 3 1 4 2 5
  Segment = Struct.new(:id, :x1, :y1, :x2, :y2) do
    # Parametric line equation P(s) = A + s*(B - A), s in [0,1].
    def equation
      dx = x2 - x1
      dy = y2 - y1
      format("L%d(s) = (%.3f + %.3f s, %.3f + %.3f s),  s in [0,1]", id, x1, dx, y1, dy)
    end

    def dir
      [x2 - x1, y2 - y1]
    end
  end

  class Drawing
    attr_reader :segments, :arrow_order, :equations, :crossings

    def initialize(segments, arrow_order)
      @segments = segments
      @arrow_order = arrow_order
      @equations = []
      @crossings = []
    end

    def self.load(path)
      segs = {}
      order = []
      File.foreach(path, encoding: "UTF-8") do |raw|
        line = raw.strip
        next if line.empty? || line.start_with?("#")
        tok = line.split
        case tok[0]
        when "S"
          id = tok[1].to_i
          segs[id] = Segment.new(id, *tok[2, 4].map(&:to_f))
        when "ARROW"
          order = tok[1..].map(&:to_i)
        end
      end
      order = segs.keys.sort if order.empty?
      new(order.map { |i| segs.fetch(i) }, order)
    end

    # Run the full 絵→方程式→交差→PD pipeline. Returns self.
    def analyse
      build_equations
      build_crossings
      self
    end

    def build_equations
      @equations = @segments.map(&:equation)
      # closure equation of the polyline (last point returns to the first)
      @equations << "closure: L#{@segments.last.id}(1) = L#{@segments.first.id}(0)"
      @equations
    end

    # Proper segment/segment intersections along the arrow-ordered walk.
    # Each entry: [i, j, x, y, sign, s_i, s_j] where s_i/s_j are the fractions
    # of the hit along segments i and j (their positions on the closed walk).
    def build_crossings
      pts = []
      segs = @segments
      n = segs.length
      (0...n).each do |i|
        ((i + 1)...n).each do |j|
          next if adjacent?(i, j, n) # consecutive segments share an endpoint
          hit = intersect(segs[i], segs[j])
          next unless hit
          x, y, si, sj = hit
          # sign slot kept for positional layout; the writhe sign is derived
          # geometrically (with over/under) later in assemble_crossing.
          pts << [i, j, x, y, 0, si, sj]
        end
      end
      @crossings = build_pd(pts)
    end

    private

    def adjacent?(i, j, n)
      (i - j).abs == 1 || (i.zero? && j == n - 1)
    end

    # Segment intersection; returns [x, y, s_i, s_j] for a proper interior hit.
    def intersect(a, b)
      x1, y1, x2, y2 = a.x1, a.y1, a.x2, a.y2
      x3, y3, x4, y4 = b.x1, b.y1, b.x2, b.y2
      den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
      return nil if den.abs < 1e-12
      t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
      u = ((x1 - x3) * (y1 - y2) - (y1 - y3) * (x1 - x2)) / den
      eps = 1e-9
      return nil unless t > eps && t < 1 - eps && u > eps && u < 1 - eps
      [x1 + t * (x2 - x1), y1 + t * (y2 - y1), t, u]
    end

    # Build the crossing list from the ordered intersection list.
    #
    # Arcs are the pieces of the closed walk between consecutive crossing passes.
    # For each crossing the four incident half-edges are ordered COUNTER-CLOCKWISE
    # by their geometric angle, giving arcs [e0,e1,e2,e3]. Over/under alternates
    # along the walk (the picture records no depth, so the canonical alternating
    # diagram is used); `over_even` is true when the over-strand occupies the even
    # ccw positions {e0,e2}. The writhe sign is the right-handed sign of the
    # (over, under) direction frame.
    #
    #   crossing = [id, e0, e1, e2, e3, over_even, sign]
    def build_pd(pts)
      return [] if pts.empty?

      passes = []
      pts.each_with_index do |(i, j, _x, _y, _sign, si, sj), cid|
        passes << { pos: [i, si], cid: cid, strand: :i } # pass on strand i
        passes << { pos: [j, sj], cid: cid, strand: :j } # pass on strand j
      end
      passes.sort_by! { |p| p[:pos] }

      m = passes.length # 2 * (#crossings): arc k spans pass k -> pass k+1
      info = Hash.new { |h, k| h[k] = {} } # cid => {i:{in:,out:,k:}, j:{...}}
      passes.each_with_index do |p, k|
        info[p[:cid]][p[:strand]] = { in: (k - 1) % m, out: k, k: k }
      end

      pts.each_index.map { |cid| assemble_crossing(cid, pts[cid], info[cid]) }
    end

    # Assemble one crossing in the KnotTheory X[e0,e1,e2,e3] convention:
    # the four arcs counter-clockwise, e0 the INCOMING UNDER arc (so e0,e2 are
    # the under-strand, e1,e3 the over-strand). With this anchoring the Kauffman
    # A-smoothing is always join(e0,e1),(e2,e3), independent of the crossing.
    def assemble_crossing(cid, pt, info)
      i, j = pt[0], pt[1]
      di = @segments[i].dir
      dj = @segments[j].dir
      # half-edges: [arc, angle-from-crossing, strand, role]; in-edges point back.
      halves = [
        { arc: info[:i][:in],  ang: Math.atan2(-di[1], -di[0]), strand: :i, role: :in },
        { arc: info[:i][:out], ang: Math.atan2(di[1], di[0]),   strand: :i, role: :out },
        { arc: info[:j][:in],  ang: Math.atan2(-dj[1], -dj[0]), strand: :j, role: :in },
        { arc: info[:j][:out], ang: Math.atan2(dj[1], dj[0]),   strand: :j, role: :out }
      ]
      halves.sort_by! { |h| h[:ang] } # counter-clockwise

      # Alternating diagram: the strand whose pass falls on an even walk index is
      # the over-strand here, so the other strand is under.
      over = info[:i][:k].even? ? :i : :j
      under = over == :i ? :j : :i

      start = halves.index { |h| h[:strand] == under && h[:role] == :in }
      e = (0..3).map { |k| halves[(start + k) % 4][:arc] }

      sign = writhe_sign(di, dj, over)
      [cid, e[0], e[1], e[2], e[3], sign]
    end

    # Right-handed writhe sign from the oriented over/under strands.
    def writhe_sign(di, dj, over)
      over_dir  = over == :i ? di : dj
      under_dir = over == :i ? dj : di
      cross = over_dir[0] * under_dir[1] - over_dir[1] * under_dir[0]
      cross >= 0 ? 1 : -1
    end
  end
end
