from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


def render_svg(curve: list[dict[str, float | int]]) -> str:
    width = 720
    height = 520
    left = 75
    top = 35
    plot = 400

    def x(value: float) -> float:
        return left + value * plot

    def y(value: float) -> float:
        return top + (1.0 - value) * plot

    grid = []
    labels = []
    for step in range(0, 11):
        value = step / 10
        grid.append(
            f'<line x1="{x(value):.1f}" y1="{top}" x2="{x(value):.1f}" '
            f'y2="{top + plot}" class="grid"/>'
        )
        grid.append(
            f'<line x1="{left}" y1="{y(value):.1f}" x2="{left + plot}" '
            f'y2="{y(value):.1f}" class="grid"/>'
        )
        labels.append(
            f'<text x="{x(value):.1f}" y="{top + plot + 24}" class="tick" '
            f'text-anchor="middle">{value:.1f}</text>'
        )
        labels.append(
            f'<text x="{left - 14}" y="{y(value) + 4:.1f}" class="tick" '
            f'text-anchor="end">{value:.1f}</text>'
        )

    points = []
    for row in curve:
        confidence = float(row["mean_confidence"])
        accuracy = float(row["empirical_accuracy"])
        count = int(row["count"])
        radius = min(14.0, 4.0 + count ** 0.5 / 2.0)
        title = html.escape(
            f"confidence={confidence:.3f}, empirical={accuracy:.3f}, n={count}"
        )
        points.append(
            f'<circle cx="{x(confidence):.1f}" cy="{y(accuracy):.1f}" '
            f'r="{radius:.1f}" class="point"><title>{title}</title></circle>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">Evidence reliability diagram</title>
<desc id="desc">Mean predicted trust score versus empirical validity by calibration bin.</desc>
<style>
text{{font-family:system-ui,sans-serif;fill:#172033}}.grid{{stroke:#d9dfeb;stroke-width:1}}
.axis{{stroke:#172033;stroke-width:2}}.ideal{{stroke:#6b7280;stroke-width:2;stroke-dasharray:7 7}}
.point{{fill:#5a46d6;fill-opacity:.78;stroke:#3427a8;stroke-width:1.5}}.tick{{font-size:12px}}
.label{{font-size:15px;font-weight:650}}.heading{{font-size:20px;font-weight:750}}
</style>
<text x="{left}" y="22" class="heading">Evidence calibration reliability</text>
{''.join(grid)}
<line x1="{left}" y1="{top + plot}" x2="{left + plot}" y2="{top + plot}" class="axis"/>
<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot}" class="axis"/>
<line x1="{x(0):.1f}" y1="{y(0):.1f}" x2="{x(1):.1f}" y2="{y(1):.1f}" class="ideal"/>
{''.join(points)}
{''.join(labels)}
<text x="{left + plot / 2}" y="{top + plot + 55}" class="label" text-anchor="middle">Mean trust score</text>
<text x="18" y="{top + plot / 2}" class="label" text-anchor="middle"
transform="rotate(-90 18 {top + plot / 2})">Empirical evidence validity</text>
<text x="{left + plot + 35}" y="{top + 40}" class="tick">Dashed: ideal calibration</text>
<text x="{left + plot + 35}" y="{top + 62}" class="tick">Point size: bin sample count</text>
</svg>"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Render calibration reliability SVG")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.report.read_text(encoding="utf-8"))
    curve = payload["calibration"]["curve"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_svg(curve), encoding="utf-8")
    print(f"Reliability diagram: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
