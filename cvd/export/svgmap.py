"""Circular plasmid map as standalone SVG."""

import math
from xml.sax.saxutils import escape as xml_escape

from ..model import Design
from ..parts.elements import KINDS


def to_svg(d: Design) -> str:
    T, cx, cy, r = d.total, 180.0, 180.0, 130.0
    height = max(360, 48 + 18 * len(d.features))

    def pt(a):
        return cx + r * math.sin(a), cy - r * math.cos(a)

    svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 %d" width="700" height="%d" '
           'font-family="Helvetica, Arial, sans-serif">' % (height, height),
           '<rect width="700" height="%d" fill="#ffffff"/>' % height,
           '<circle cx="180" cy="180" r="130" fill="none" stroke="#d3dde5" stroke-width="30" opacity=".6"/>']
    for f in d.features:
        a0 = 2 * math.pi * (f.start - 1) / T
        a1 = max(2 * math.pi * f.end / T, a0 + 0.025)
        (x0, y0), (x1, y1) = pt(a0), pt(a1)
        svg.append('<path d="M%.2f %.2fA%d %d 0 %d 1 %.2f %.2f" fill="none" stroke="%s" stroke-width="26">'
                   '<title>%s: %d..%d (%d bp)</title></path>'
                   % (x0, y0, r, r, 1 if a1 - a0 > math.pi else 0, x1, y1, KINDS[f.kind][0],
                      xml_escape(f.name), f.start, f.end, f.length))
    title = d.name if len(d.name) <= 26 else d.name[:25] + "..."
    svg.append('<line x1="180" y1="30" x2="180" y2="12" stroke="#14202b" stroke-width="1.5"/>'
               '<text x="186" y="18" font-size="10" fill="#587083">1</text>')
    svg.append('<text x="180" y="172" text-anchor="middle" font-size="14" font-weight="600" fill="#14202b">%s</text>'
               % xml_escape(title))
    svg.append('<text x="180" y="194" text-anchor="middle" font-size="13" fill="#587083">%s bp</text>' % format(d.total, ","))
    for i, f in enumerate(d.features):
        y = 30 + 18 * i
        svg.append('<rect x="372" y="%d" width="11" height="11" rx="2" fill="%s"/>' % (y - 10, KINDS[f.kind][0]))
        svg.append('<text x="390" y="%d" font-size="12" fill="#14202b">%s <tspan fill="#587083">%d..%d</tspan></text>'
                   % (y, xml_escape(f.name), f.start, f.end))
    svg.append("</svg>")
    return "\n".join(svg) + "\n"
