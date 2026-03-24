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
<div id="wrap_$uid" style="resize: both; overflow: hidden; border: 1px solid #888;
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

        // --- Legend click: dim others instead of hide ---
        var origOp = gd.data.map(function(t) {
            return (t.opacity != null) ? t.opacity : 1;
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
            sel = newSel;
            Plotly.restyle(gd, "opacity", ops);
            return false;
        });

        gd.on("plotly_legenddoubleclick", function() { return false; });
    });
})();
</script>
""")


def show_resizable(fig, width="100%", height="500px", dim_opacity=0.1):
    """Display a Plotly figure in a resizable container with legend-highlight behavior.

    Features:
      - The container is CSS-resizable (drag bottom-right corner).
      - Plotly auto-relayouts to fill the container on resize.
      - Clicking a legend entry dims all *other* traces (by legendgroup).
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
        Opacity for non-selected traces when a legend entry is clicked (default 0.1).
    """
    uid = "plotly_" + uuid.uuid4().hex[:8]

    plot_html = fig.to_html(
        include_plotlyjs="cdn",
        config={"responsive": True},
        div_id=uid,
        full_html=False,
    )

    html = _TEMPLATE.substitute(
        uid=uid,
        width=width,
        height=height,
        plot_html=plot_html,
        dim_opacity=dim_opacity,
    )
    display(HTML(html))
