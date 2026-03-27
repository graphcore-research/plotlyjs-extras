"""Resizable, interactive Plotly figure widget for Jupyter notebooks.

Enhancements over vanilla Plotly HTML output:
  - CSS-resizable container with auto-relayout
  - Legend click dims other traces instead of hiding them
  - Legend double-click is a no-op (prevents accidental hide-all)
"""

import uuid
from string import Template

from IPython.display import HTML, display

# JS template using $-substitution (avoids f-string brace escaping pain)
_TEMPLATE = Template(r"""
<div id="wrap_$uid"
    style="resize: both; overflow: hidden; border: 1px solid #888;
    width: $width; height: $height; min-width: 400px; min-height: 250px;
    position: relative;">
    $plot_html
</div>
<script>
(function() {
    var wrap = document.getElementById("wrap_$uid");
    var gd = document.getElementById("$uid");
    if (!wrap || !gd) return;
    gd.style.width = "100%";
    gd.style.height = "100%";

    function whenPlotReady(cb) {
        if (gd._fullData) { cb(); }
        else { setTimeout(function() { whenPlotReady(cb); }, 50); }
    }

    whenPlotReady(function() {
        // --- Resize observer ---
        var ro = new ResizeObserver(function(entries) {
            for (var e of entries) {
                var w = e.contentRect.width;
                var h = e.contentRect.height;
                if (w > 0 && h > 0) {
                    Plotly.relayout(gd, { width: w, height: h });
                }
            }
        });
        ro.observe(wrap);
        var rect = wrap.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0) {
            Plotly.relayout(gd, { width: rect.width, height: rect.height });
        }

        function blendWithBlack(color, amount) {
            if (typeof color !== "string") return color;
            var c = color.trim();

            function clamp(x) {
                return Math.max(0, Math.min(255, Math.round(x)));
            }

            var m3 = c.match(/^#([0-9a-fA-F]{3})$$/);
            if (m3) {
                var h = m3[1];
                var r3 = parseInt(h[0] + h[0], 16);
                var g3 = parseInt(h[1] + h[1], 16);
                var b3 = parseInt(h[2] + h[2], 16);
                r3 = clamp(r3 * (1 - amount));
                g3 = clamp(g3 * (1 - amount));
                b3 = clamp(b3 * (1 - amount));
                return "#"
                    + r3.toString(16).padStart(2, "0")
                    + g3.toString(16).padStart(2, "0")
                    + b3.toString(16).padStart(2, "0");
            }

            var m6 = c.match(/^#([0-9a-fA-F]{6})$$/);
            if (m6) {
                var hex = m6[1];
                var r6 = parseInt(hex.slice(0, 2), 16);
                var g6 = parseInt(hex.slice(2, 4), 16);
                var b6 = parseInt(hex.slice(4, 6), 16);
                r6 = clamp(r6 * (1 - amount));
                g6 = clamp(g6 * (1 - amount));
                b6 = clamp(b6 * (1 - amount));
                return "#"
                    + r6.toString(16).padStart(2, "0")
                    + g6.toString(16).padStart(2, "0")
                    + b6.toString(16).padStart(2, "0");
            }

            var mrgb = c.match(/^rgba?\(([^)]+)\)$$/i);
            if (mrgb) {
                var parts = mrgb[1]
                    .split(",")
                    .map(function(v) { return v.trim(); });
                if (parts.length === 3 || parts.length === 4) {
                    var rr = clamp(parseFloat(parts[0]) * (1 - amount));
                    var gg = clamp(parseFloat(parts[1]) * (1 - amount));
                    var bb = clamp(parseFloat(parts[2]) * (1 - amount));
                    if (parts.length === 4) {
                        return (
                            "rgba(" + rr + ", " + gg + ", " + bb
                            + ", " + parts[3] + ")"
                        );
                    }
                    return "rgb(" + rr + ", " + gg + ", " + bb + ")";
                }
            }

            return color;
        }

        function maybeDarkenColor(color) {
            if (Array.isArray(color) || color == null) return color;
            return blendWithBlack(color, $active_darken);
        }

        // --- Legend click: dim others, darken selected group ---
        var origOp = gd.data.map(function(t) {
            return (t.opacity != null) ? t.opacity : 1;
        });
        var baseStyles = gd._fullData.map(function(t) {
            return {
                lineColor: t.line && t.line.color,
                markerColor: t.marker && t.marker.color,
                fillColor: t.fillcolor,
                textColor: t.textfont && t.textfont.color,
            };
        });
        var sel = null;

        gd.on("plotly_legendclick", function(e) {
            var lg = gd.data[e.curveNumber].legendgroup;
            if (!lg) return false;
            var newSel = (sel === lg) ? null : lg;
            var ops = gd.data.map(function(t, i) {
                if (newSel === null) return origOp[i];
                return (t.legendgroup === newSel) ? origOp[i] : $dim_opacity;
            });
            var lineColors = gd.data.map(function(t, i) {
                var c = baseStyles[i].lineColor;
                if (newSel !== null && t.legendgroup === newSel) {
                    return maybeDarkenColor(c);
                }
                return c;
            });
            var markerColors = gd.data.map(function(t, i) {
                var c = baseStyles[i].markerColor;
                if (newSel !== null && t.legendgroup === newSel) {
                    return maybeDarkenColor(c);
                }
                return c;
            });
            var fillColors = gd.data.map(function(t, i) {
                var c = baseStyles[i].fillColor;
                if (newSel !== null && t.legendgroup === newSel) {
                    return maybeDarkenColor(c);
                }
                return c;
            });
            var textColors = gd.data.map(function(t, i) {
                var c = baseStyles[i].textColor;
                if (newSel !== null && t.legendgroup === newSel) {
                    return maybeDarkenColor(c);
                }
                return c;
            });
            sel = newSel;
            Plotly.restyle(gd, {
                opacity: ops,
                "line.color": lineColors,
                "marker.color": markerColors,
                fillcolor: fillColors,
                "textfont.color": textColors,
            });
            return false;
        });

        gd.on("plotly_legenddoubleclick", function() { return false; });
    });
})();
</script>
""")


def show_resizable(
    fig,
    width="100%",
    height="500px",
    dim_opacity=0.1,
    active_darken=0.2,
):
    """Display a Plotly figure in a resizable container.

    Features:
      - The container is CSS-resizable (drag bottom-right corner).
      - Plotly auto-relayouts to fill the container on resize.
            - Clicking a legend entry dims all *other* traces (by legendgroup)
                and darkens the selected traces.
      - Clicking the same entry again restores all traces.
      - Double-click on legend is suppressed (no hide-all).

    Parameters
    ----------
    fig : plotly.graph_objects.Figure
        The Plotly figure to display.
    width : str
        CSS width of the container (default "100%").
    height : str
        CSS height of the container (default "500px").
    dim_opacity : float
        Opacity for non-selected traces when a legend entry is clicked
        (default 0.1).
    active_darken : float
        Blend factor toward black for selected traces (default 0.2).
    """

    html = build_resizable_html(
        fig,
        width=width,
        height=height,
        dim_opacity=dim_opacity,
        active_darken=active_darken,
    )
    display(HTML(html))


def build_resizable_html(
    fig,
    width="100%",
    height="500px",
    dim_opacity=0.1,
    active_darken=0.2,
):
    """Return HTML string for a resizable Plotly container.

    This is useful for automation workflows (e.g., screenshot generation)
    where returning HTML is preferable to displaying directly in a notebook.
    """
    uid = "plotly_" + uuid.uuid4().hex[:8]

    plot_html = fig.to_html(
        include_plotlyjs="cdn",
        config={"responsive": True},
        div_id=uid,
        full_html=False,
    )

    return _TEMPLATE.substitute(
        uid=uid,
        width=width,
        height=height,
        plot_html=plot_html,
        dim_opacity=dim_opacity,
        active_darken=active_darken,
    )
