# frozen_string_literal: true

module Bada
  module Penrose
    # GlyphSVG — faithful SVG renderings of Roger Penrose's diagrammatic tensor
    # notation, matching his hand-drawn convention:
    #
    #   * a tensor is a SHAPE (box/oval/triangle); lines leaving the TOP are its
    #     UPPER indices, lines leaving the BOTTOM are its LOWER indices;
    #   * contraction joins an upper leg to a lower leg;
    #   * the covariant derivative ∇ is a big HOOP (ring) drawn AROUND the
    #     operand, with the derivative index as an extra leg out of the ring;
    #   * symmetrisation is a straight BAR across a bundle of legs;
    #     antisymmetrisation is a WAVY bar;
    #   * swapping two lines (a crossing) equals minus the uncrossed pair for an
    #     antisymmetric object.
    #
    # These are the picture-symbols shown on the palette in the web app. Colours
    # follow the Bada theme (gold shapes, cyan upper legs, blue lower legs).
    module GlyphSVG
      GOLD = "#c8a44a"
      UP   = "#40b8c0" # upper-index legs
      DOWN = "#4a80d0" # lower-index legs
      INK  = "#e6ecf3"

      module_function

      # --- fragment helpers (viewBox 0 0 120 120) ----------------------
      def upper_leg(x, top: 45, to: 12)
        %(<line x1="#{x}" y1="#{top}" x2="#{x}" y2="#{to}" stroke="#{UP}" stroke-width="3"/>)
      end

      def lower_leg(x, bottom: 75, to: 108)
        %(<line x1="#{x}" y1="#{bottom}" x2="#{x}" y2="#{to}" stroke="#{DOWN}" stroke-width="3"/>)
      end

      def box(label, x: 35, y: 45, w: 50, h: 30, stroke: GOLD)
        %(<rect x="#{x}" y="#{y}" width="#{w}" height="#{h}" rx="6" fill="none" ) +
          %(stroke="#{stroke}" stroke-width="3"/>) +
          %(<text x="#{x + w / 2}" y="#{y + h / 2 + 6}" text-anchor="middle" ) +
          %(font-size="19" font-style="italic" fill="#{stroke}">#{label}</text>)
      end

      def wrap(inner)
        %(<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg" ) +
          %(fill="none" stroke-linecap="round" stroke-linejoin="round">#{inner}</svg>)
      end

      # --- the symbols -------------------------------------------------
      # key => svg string
      def all
        {
          tensor: wrap(
            upper_leg(50) + upper_leg(70) + box("T") + lower_leg(50) + lower_leg(70)
          ),
          # a (1,1)-tensor: one upper (row) + one lower (column) leg = a matrix.
          matrix: wrap(
            upper_leg(60) + box("M") + lower_leg(60)
          ),
          # matrix product: contract the lower leg of one box with the upper leg
          # of the next (a vertical chain), free legs top and bottom.
          matmul: wrap(
            upper_leg(60, top: 34, to: 12) +
            box("A", x: 40, y: 34, w: 40, h: 24) +
            %(<line x1="60" y1="58" x2="60" y2="62" stroke="#{GOLD}" stroke-width="3"/>) +
            box("B", x: 40, y: 62, w: 40, h: 24) +
            lower_leg(60, bottom: 86, to: 108)
          ),
          # a vector: single upper index.
          vector: wrap(
            upper_leg(60) + box("v")
          ),
          wire: wrap(
            %(<line x1="60" y1="12" x2="60" y2="108" stroke="#{UP}" stroke-width="3"/>)
          ),
          # contraction: two boxes, an upper leg of A joined to a lower leg of B.
          contraction: wrap(
            box("A", x: 14, y: 34, w: 36, h: 26) +
            box("B", x: 70, y: 60, w: 36, h: 26) +
            upper_leg(24, top: 34, to: 12) +
            lower_leg(96, bottom: 86, to: 108) +
            # the joining wire: A's lower leg curves to B's upper leg
            %(<path d="M40 60 C40 84 80 36 88 60" stroke="#{GOLD}" stroke-width="3" fill="none"/>)
          ),
          metric: wrap(
            box("g") + lower_leg(50) + lower_leg(70)
          ),
          # cup ∪: bends two lines upward (raises indices) — g^{μν}.
          cup: wrap(
            %(<path d="M35 100 C35 45 85 45 85 100" stroke="#{GOLD}" stroke-width="3" fill="none"/>) +
            upper_leg(35, top: 100, to: 100) + upper_leg(85, top: 100, to: 100)
          ),
          # cap ∩: bends two lines downward (lowers indices) — g_{μν}.
          cap: wrap(
            %(<path d="M35 20 C35 75 85 75 85 20" stroke="#{GOLD}" stroke-width="3" fill="none"/>) +
            %(<line x1="35" y1="20" x2="35" y2="12" stroke="#{DOWN}" stroke-width="3"/>) +
            %(<line x1="85" y1="20" x2="85" y2="12" stroke="#{DOWN}" stroke-width="3"/>)
          ),
          # identity / Kronecker δ: a single straight through-line.
          delta: wrap(
            upper_leg(60, top: 60, to: 12) + lower_leg(60, bottom: 60, to: 108) +
            %(<circle cx="60" cy="60" r="3" fill="#{GOLD}"/>)
          ),
          # Levi-Civita ε: a triangle (totally antisymmetric) with a bar on legs.
          epsilon: wrap(
            %(<path d="M40 45 L80 45 L60 78 Z" stroke="#{GOLD}" stroke-width="3" fill="none"/>) +
            %(<text x="60" y="40" text-anchor="middle" font-size="15" fill="#{GOLD}">ε</text>) +
            lower_leg(48, bottom: 66, to: 108) + lower_leg(60, bottom: 78, to: 108) +
            lower_leg(72, bottom: 66, to: 108)
          ),
          # covariant derivative ∇: a HOOP around the operand + one derivative leg.
          nabla: wrap(
            upper_leg(60, top: 40, to: 12) +
            %(<ellipse cx="60" cy="62" rx="40" ry="30" stroke="#{GOLD}" stroke-width="3" fill="none"/>) +
            box("T", x: 46, y: 52, w: 28, h: 20) +
            %(<text x="24" y="52" text-anchor="middle" font-size="17" fill="#{GOLD}">∇</text>) +
            lower_leg(60, bottom: 72, to: 108) +
            # the extra derivative index leg, out of the hoop
            %(<line x1="92" y1="80" x2="112" y2="98" stroke="#{DOWN}" stroke-width="3"/>)
          ),
          # partial derivative ∂: a ring with ∂ and one leg.
          partial: wrap(
            upper_leg(60, top: 40, to: 12) +
            %(<circle cx="60" cy="62" r="30" stroke="#{GOLD}" stroke-width="3" fill="none"/>) +
            %(<text x="60" y="58" text-anchor="middle" font-size="20" fill="#{GOLD}">∂</text>) +
            lower_leg(60, bottom: 92, to: 108) +
            %(<line x1="86" y1="82" x2="106" y2="98" stroke="#{DOWN}" stroke-width="3"/>)
          ),
          # Lie derivative £: hoop with £, operand legs up and down.
          lie: wrap(
            upper_leg(60, top: 40, to: 12) +
            %(<ellipse cx="60" cy="62" rx="38" ry="28" stroke="#{GOLD}" stroke-width="3" fill="none"/>) +
            box("T", x: 48, y: 52, w: 24, h: 20) +
            %(<text x="26" y="54" text-anchor="middle" font-size="17" font-style="italic" fill="#{GOLD}">£</text>) +
            lower_leg(60, bottom: 72, to: 108)
          ),
          # symmetrisation: a straight bar across a bundle of legs.
          symmetrize: wrap(
            box("T") +
            upper_leg(48, top: 45, to: 12) + upper_leg(60, top: 45, to: 12) + upper_leg(72, top: 45, to: 12) +
            %(<line x1="40" y1="28" x2="80" y2="28" stroke="#{INK}" stroke-width="5"/>)
          ),
          # antisymmetrisation: a wavy bar across the bundle.
          antisymmetrize: wrap(
            box("T") +
            upper_leg(48, top: 45, to: 12) + upper_leg(60, top: 45, to: 12) + upper_leg(72, top: 45, to: 12) +
            %(<path d="M40 28 q5 -7 10 0 q5 7 10 0 q5 -7 10 0 q5 7 10 0" stroke="#{INK}" stroke-width="4" fill="none"/>)
          ),
          # swap / crossing = minus for an antisymmetric pair.
          swap: wrap(
            %(<line x1="30" y1="20" x2="60" y2="80" stroke="#{UP}" stroke-width="3"/>) +
            %(<line x1="60" y1="20" x2="30" y2="80" stroke="#{UP}" stroke-width="3"/>) +
            %(<text x="74" y="56" font-size="16" fill="#{GOLD}">= −</text>) +
            %(<line x1="98" y1="20" x2="98" y2="80" stroke="#{UP}" stroke-width="3"/>) +
            %(<line x1="110" y1="20" x2="110" y2="80" stroke="#{UP}" stroke-width="3"/>)
          ),
          # Riemann curvature: a box with two antisymmetric leg-pairs.
          riemann: wrap(
            upper_leg(52, top: 45, to: 12) + upper_leg(68, top: 45, to: 12) +
            %(<line x1="48" y1="30" x2="72" y2="30" stroke="#{INK}" stroke-width="3"/>) +
            box("R") +
            lower_leg(52) + lower_leg(68) +
            %(<line x1="48" y1="90" x2="72" y2="90" stroke="#{INK}" stroke-width="3"/>)
          ),
          # Torsion: triangle with an antisymmetric lower pair + one upper leg.
          torsion: wrap(
            upper_leg(60, top: 46, to: 12) +
            %(<path d="M42 46 L78 46 L60 74 Z" stroke="#{GOLD}" stroke-width="3" fill="none"/>) +
            %(<text x="60" y="42" text-anchor="middle" font-size="13" fill="#{GOLD}">T</text>) +
            lower_leg(50, bottom: 66, to: 108) + lower_leg(70, bottom: 66, to: 108) +
            %(<line x1="46" y1="90" x2="74" y2="90" stroke="#{INK}" stroke-width="3"/>)
          ),
          # integral ∫ … dμ : an integral sign wrapping the operand, measure leg.
          integral: wrap(
            %(<text x="22" y="78" font-size="60" fill="#{GOLD}">∫</text>) +
            upper_leg(64, top: 45, to: 12) + box("T", x: 44, y: 45, w: 44, h: 30) + lower_leg(64) +
            %(<text x="98" y="70" font-size="13" fill="#{DOWN}">dμ</text>)
          )
        }
      end

      # SVG for one key (or a neutral placeholder).
      def for(key)
        all[key.to_sym] || wrap(box("?"))
      end
    end
  end
end
