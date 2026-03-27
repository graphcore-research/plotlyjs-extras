"""Generate README screenshots for legend highlight behavior.

Creates two images:
- before click
- after first legend click
"""

from pathlib import Path
import argparse
import tempfile

import plotly.graph_objects as go
from plotly.colors import sample_colorscale

from plotlyjs_extras import build_resizable_html


def build_demo_figure() -> go.Figure:
    x = [1, 2, 3, 4, 5, 6, 7]
    base_colors = sample_colorscale("Viridis", [i / 7 for i in range(8)])

    series = [
        {
            "name": "Line 1",
            "y": [1.1, 1.5, 1.9, 2.2, 2.6, 3.0, 3.2],
            "dash": "solid",
            "width": 3,
            "alpha": 0.95,
        },
        {
            "name": "Line 2",
            "y": [0.9, 1.2, 1.6, 2.0, 2.3, 2.6, 2.9],
            "dash": "dash",
            "width": 2.6,
            "alpha": 0.88,
        },
        {
            "name": "Line 3",
            "y": [0.8, 1.1, 1.4, 1.8, 2.0, 2.2, 2.5],
            "dash": "dot",
            "width": 2.4,
            "alpha": 0.80,
        },
        {
            "name": "Line 4",
            "y": [1.5, 1.8, 2.1, 2.4, 2.7, 2.9, 3.1],
            "dash": "dashdot",
            "width": 2.4,
            "alpha": 0.74,
        },
        {
            "name": "Line 5",
            "y": [2.2, 2.1, 2.0, 1.95, 1.9, 1.85, 1.8],
            "dash": "longdash",
            "width": 2.8,
            "alpha": 0.65,
        },
        {
            "name": "Line 6",
            "y": [2.5, 2.35, 2.2, 2.1, 2.0, 1.95, 1.9],
            "dash": "longdashdot",
            "width": 2.4,
            "alpha": 0.55,
        },
        {
            "name": "Line 7",
            "y": [1.8, 1.7, 1.6, 1.65, 1.75, 1.9, 2.05],
            "dash": "solid",
            "width": 1.8,
            "alpha": 0.42,
        },
        {
            "name": "Line 8",
            "y": [1.35, 1.5, 1.65, 1.8, 1.95, 2.1, 2.25],
            "dash": "dot",
            "width": 1.8,
            "alpha": 0.36,
        },
    ]

    fig = go.Figure()
    for index, row in enumerate(series):
        red, green, blue = (
            base_colors[index].replace("rgb(", "").replace(")", "").split(",")
        )
        color = f"rgba({red.strip()}, {green.strip()}, {blue.strip()}, {row['alpha']})"
        fig.add_trace(
            go.Scatter(
                x=x,
                y=row["y"],
                mode="lines+markers",
                name=row["name"],
                legendgroup=row["name"],
                line={
                    "dash": row["dash"],
                    "width": row["width"],
                    "color": color,
                },
                marker={"size": 6, "color": color},
            )
        )

    fig.update_layout(
        title="Legend click to focus a line",
        template="plotly_white",
        yaxis_title="Value",
        xaxis_title="Step",
    )
    return fig


def create_page_html() -> str:
    figure_html = build_resizable_html(
        build_demo_figure(),
        width="960px",
        height="520px",
        dim_opacity=0.12,
        active_darken=0.25,
    )
    return (
        """<!doctype html>
<html>
  <head>
    <meta charset=\"utf-8\" />
    <title>plotlyjs-extras README screenshots</title>
    <style>
      body {
        margin: 0;
        padding: 24px;
        background: #ffffff;
        font-family: system-ui, -apple-system, sans-serif;
      }
      #screenshot-root {
        width: 980px;
      }
    </style>
  </head>
  <body>
    <div id=\"screenshot-root\">\n"""
        + figure_html
        + """\n    </div>
  </body>
</html>
"""
    )


def generate_screenshots(output_dir: Path) -> None:
    try:
        from playwright.sync_api import sync_playwright  # pyright: ignore
    except ImportError as exc:
        raise SystemExit(
            "Playwright is required. Install with "
            "`pip install playwright` and then run "
            "`python -m playwright install chromium`."
        ) from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    before_path = output_dir / "legend-before-click.png"
    after_path = output_dir / "legend-after-click.png"

    with tempfile.TemporaryDirectory() as tmp:
        html_path = Path(tmp) / "screenshot_demo.html"
        html_path.write_text(create_page_html(), encoding="utf-8")

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1200, "height": 760})
            page.goto(html_path.as_uri())
            page.wait_for_selector("div.js-plotly-plot")
            page.wait_for_timeout(400)

            root = page.locator("#screenshot-root")
            root.screenshot(path=str(before_path))

            page.locator(".legend .traces .legendtoggle").first.click()
            page.wait_for_timeout(300)
            root.screenshot(path=str(after_path))
            browser.close()

    print(f"Wrote {before_path}")
    print(f"Wrote {after_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=("Generate before/after legend click screenshots for README."),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/assets"),
        help="Directory for generated PNG files.",
    )
    args = parser.parse_args()
    generate_screenshots(args.output_dir)


if __name__ == "__main__":
    main()
