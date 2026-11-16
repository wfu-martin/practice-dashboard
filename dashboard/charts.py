"""Every headline, number tile, and chart on the dashboard, in one house style.

design.md states the style rules in words; this module is where they live in
code. Views call these helpers instead of drawing charts directly, so a view
built by any teammate, in any session, looks like the rest of the dashboard.
To change the look, change the rule in design.md and the matching line here
(and the theme in .streamlit/config.toml), never one view at a time.

Number kinds: "money" ($1,234, or $5.65 under $10), "count" (1,234),
"percent" (12.3%, from a fraction such as 0.123), "cents" ($39.67, always
two decimals: averages per customer).
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# The accent marks what the headline is about; everything else is neutral.
# Red is kept for a loss or a miss. The accent matches primaryColor in
# .streamlit/config.toml.
ACCENT = "#1F5FA8"
NEUTRAL = "#B4BAC1"
NEGATIVE = "#B23B3B"
TEXT = "#1F2933"

# d3 formats for chart labels, Python formats for headline numbers. Money
# under $10 keeps its cents: a $5.65 average order must not read as $6.
_D3 = {"money": "$,.0f", "count": ",.0f", "percent": ".1%", "cents": "$,.2f"}
_PY = {"money": "${:,.0f}", "count": "{:,.0f}", "percent": "{:.1%}", "cents": "${:,.2f}"}


def _kind(kind: str, largest: float) -> str:
    return "cents" if kind == "money" and abs(largest) < 10 else kind


def fmt(value, kind: str) -> str:
    """One number written the house way, for headlines and captions."""
    return _PY[_kind(kind, float(value))].format(float(value))


def headline(takeaway: str, note: str = "") -> None:
    """A section's headline: the takeaway as a sentence, then what it measures.

    takeaway: the answer, with its number ("Rock earns 35% of revenue").
    note: the metric, its period, and its filters, from the spec.
    """
    # Two dollar signs in one line would be read as a formula and garbled.
    st.subheader(takeaway.replace("$", r"\$"))
    if note:
        st.caption(note.replace("$", r"\$"))


def kpi_row(tiles: list[dict]) -> None:
    """A row of headline numbers, each against a comparison.

    Each tile is {"label", "value", "kind"} plus, optionally, "delta" (the
    change against the comparison, same kind and precision as the value unless
    "delta_kind" names another, such as "percent" for a change from last year)
    and "versus" (what it is compared with, such as "vs last year").
    """
    for column, tile in zip(st.columns(len(tiles)), tiles):
        delta = None
        if tile.get("delta") is not None:
            sign = "+" if float(tile["delta"]) >= 0 else "-"
            delta_kind = tile.get("delta_kind", tile["kind"])
            basis = tile["value"] if delta_kind == tile["kind"] else tile["delta"]
            precision = _kind(delta_kind, float(basis))
            delta = sign + _PY[precision].format(abs(float(tile["delta"])))
            if tile.get("versus"):
                delta += f" {tile['versus']}"
        column.metric(tile["label"], fmt(tile["value"], tile["kind"]), delta)


def ranked_bar(
    df: pd.DataFrame,
    label: str,
    value: str,
    kind: str = "money",
    highlight: str | None = None,
    top: int = 10,
) -> go.Figure:
    """Items ranked by size: horizontal bars, largest at the top.

    The highlighted item (the largest, unless named) gets the accent color;
    the rest stay neutral. Each bar carries its value, so the chart needs no
    axis numbers or gridlines.
    """
    data = df.nlargest(top, value)
    focus = highlight if highlight is not None else data.iloc[0][label]
    colors = [ACCENT if item == focus else NEUTRAL for item in data[label]]
    d3 = _D3[_kind(kind, data[value].abs().max())]
    fig = px.bar(data, x=value, y=label, orientation="h")
    fig.update_traces(
        marker_color=colors,
        texttemplate=f"%{{x:{d3}}}",
        textposition="outside",
        cliponaxis=False,
        hovertemplate=f"%{{y}}: %{{x:{d3}}}<extra></extra>",
    )
    fig.update_yaxes(categoryorder="total ascending", title=None)
    fig.update_xaxes(visible=False, rangemode="tozero")
    return _house(fig, height=max(240, 34 * len(data) + 60))


def trend_line(
    df: pd.DataFrame, date: str, value: str, kind: str = "money", label_points: bool = False
) -> go.Figure:
    """Change over time: one line in the accent color.

    The latest value is labeled; with label_points, every point is (for a line
    of only a few points, such as five years).
    """
    data = df.sort_values(date)
    d3 = _D3[_kind(kind, data[value].abs().max())]
    fig = px.line(data, x=date, y=value)
    fig.update_traces(
        line={"color": ACCENT, "width": 3},
        hovertemplate=f"%{{x}}: %{{y:{d3}}}<extra></extra>",
    )
    if label_points:
        fig.update_traces(
            mode="lines+markers+text",
            marker={"color": ACCENT, "size": 8},
            texttemplate=f"%{{y:{d3}}}",
            textposition="top center",
            textfont={"color": ACCENT, "size": 14},
            cliponaxis=False,
        )
    else:
        last = data.iloc[-1]
        fig.add_annotation(
            x=last[date], y=last[value], text=fmt(last[value], kind),
            showarrow=False, xanchor="left", xshift=8, font={"color": ACCENT, "size": 14},
        )
    fig.update_xaxes(title=None, showgrid=False)
    fig.update_yaxes(title=None, tickformat=d3, gridcolor="#ECEEF1", rangemode="tozero")
    return _house(fig, height=320)


_FINANCE_ROWS = {
    "genre": "By genre",
    "country": "By country",
    "year": "By year",
    "rep": "By rep",
    "invoices": "Sum of invoice totals",
}


def finance_check(table: pd.DataFrame) -> None:
    """The collapsed "Check against Finance" section: group totals against Finance.

    table: one row per breakdown with `breakdown`, `groups`, `revenue`,
    `finance_total` and `gap` (metrics.finance_check). Exact values someone
    will look up, so it is a table with cents, closed until opened.
    """
    shown = pd.DataFrame(
        {
            "Breakdown": table["breakdown"].map(_FINANCE_ROWS),
            "Groups": table["groups"].astype(int),
            "Revenue": table["revenue"].astype(float),
            "Finance total": table["finance_total"].astype(float),
            "Gap": table["gap"].astype(float),
        }
    )
    money = st.column_config.NumberColumn(format="dollar", step=0.01)
    with st.expander("Check against Finance", expanded=False):
        st.caption(
            "Each breakdown of revenue, all years, against Finance's total "
            "(the sum of invoice totals). A gap of 0.00 means they tie out."
        )
        st.dataframe(
            shown,
            hide_index=True,
            width="stretch",
            column_config={"Revenue": money, "Finance total": money, "Gap": money},
        )


def show(fig: go.Figure) -> None:
    """Put a chart on the page, full width, without the toolbar."""
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def nothing_to_show(what: str = "these filters") -> None:
    """The note shown when a filter leaves no rows."""
    st.info(f"No data for {what}. Widen the filters to see results.")


_BACK_TO_TOP_CSS = f"""
<style>
a.back-to-top {{
    position: fixed; right: 1rem; bottom: 1rem; z-index: 1000;
    padding: 0.35rem 0.8rem; border-radius: 1rem;
    background: {ACCENT}; color: #FFFFFF !important; font-size: 0.85rem;
    text-decoration: none !important; box-shadow: 0 1px 4px rgba(0,0,0,0.3);
}}
a.back-to-top:focus-visible {{ outline: 3px solid {TEXT}; outline-offset: 2px; }}
/* Room at the foot of every page so the button never rests on the last content. */
[data-testid="stMainBlockContainer"] {{ padding-bottom: 5rem; }}
</style>
"""

# Streamlit scrolls inside its own main container, not the browser window, and a
# plain link to "#" would not move it. This listener scrolls that container.
_BACK_TO_TOP_JS = """
<script>
if (!window.__backToTopReady) {
  window.__backToTopReady = true;
  document.addEventListener("click", function (event) {
    var link = event.target.closest && event.target.closest("a.back-to-top");
    if (!link) { return; }
    event.preventDefault();
    var main = document.querySelector('[data-testid="stMain"]');
    if (main) { main.scrollTo({ top: 0, behavior: "smooth" }); }
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
}
</script>
"""


def back_to_top() -> None:
    """Draw the floating 'Back to top' button, bottom-right, once per screen.

    Not a filter: it changes no numbers. A real link, so the keyboard reaches it.
    """
    st.markdown(
        _BACK_TO_TOP_CSS + '<a class="back-to-top" href="#">Back to top</a>',
        unsafe_allow_html=True,
    )
    st.html(_BACK_TO_TOP_JS, unsafe_allow_javascript=True)


def _house(fig: go.Figure, height: int) -> go.Figure:
    fig.update_layout(
        height=height,
        margin={"l": 0, "r": 60, "t": 10, "b": 0},
        plot_bgcolor="white",
        paper_bgcolor="white",
        font={"color": TEXT, "size": 14},
        showlegend=False,
    )
    return fig
