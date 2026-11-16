"""Issue #21: Screen 2 Growth, yearly and monthly lines (AC-5, AC-6)."""

import json

from streamlit.testing.v1 import AppTest

from conftest import scalar
from dashboard.metrics import read_sql
from test_screen1 import _values

GROWTH = 1  # the second page in the navigation


def _open_growth() -> AppTest:
    """Run streamlit_app.py showing Screen 2 (the Growth page)."""

    def script(index):
        import runpy

        import streamlit as st

        pages = []
        real_page = st.Page

        def page(fn, **kwargs):
            pages.append(fn)
            return real_page(fn, **kwargs)

        class Chosen:
            def run(self):
                pages[index]()

        st.Page = page
        st.navigation = lambda *args, **kwargs: Chosen()
        runpy.run_path("streamlit_app.py")

    return AppTest.from_function(script, args=(GROWTH,), default_timeout=60).run()


def _lines(app: AppTest) -> list[dict]:
    """Every line trace on the screen: points, drawing mode, label format."""
    out = []
    for chart in app.get("plotly_chart"):
        for trace in json.loads(chart.proto.spec)["data"]:
            if trace["type"] == "scatter":
                out.append({
                    "x": _values(trace["x"]), "y": [float(v) for v in _values(trace["y"])],
                    "mode": trace.get("mode", ""), "texttemplate": trace.get("texttemplate", ""),
                })
    return out


def _chart_with(lines: list[dict], points: int) -> dict:
    matches = [t for t in lines if len(t["x"]) == points]
    assert matches, f"no line chart with {points} points on Screen 2"
    return matches[0]


def test_ac5_screen2_yearly_table(engine):
    # Given the Growth screen, when it loads, then a line of the five yearly
    # revenues (labeled in dollars) sits above a table of revenue and change
    # from the prior year, with 2021 showing none and the note that 2025 ends 22 Dec.
    app = _open_growth()
    assert not app.exception
    line = _chart_with(_lines(app), 5)
    assert [str(x) for x in line["x"]] == ["2021", "2022", "2023", "2024", "2025"]
    assert [round(y, 2) for y in line["y"]] == [449.46, 481.45, 469.58, 477.53, 450.58]
    assert "text" in line["mode"]
    assert line["texttemplate"] == "%{y:$,.0f}"  # whole dollars on every point
    table = app.dataframe[0].value
    assert list(table.columns) == ["Year", "Revenue", "Change from prior year"]
    assert list(table["Year"].astype(str)) == ["2021", "2022", "2023", "2024", "2025"]
    assert list(table["Revenue"]) == ["$449", "$481", "$470", "$478", "$451"]
    assert list(table["Change from prior year"]) == ["none", "+7.1%", "-2.5%", "+1.7%", "-5.6%"]
    assert any(h.value.startswith("Yearly revenue moved between -5.6% and +7.1%") for h in app.subheader)
    assert any("22 Dec" in c.value and "calendar year" in c.value for c in app.caption)


def test_ac5_yearly_line_reconciles_to_invoice_totals(engine):
    # Reconciliation: each point on the yearly line equals the invoice totals
    # for that year, and each change in the table is recomputed from them.
    totals = read_sql(
        engine,
        "SELECT CAST(EXTRACT(YEAR FROM invoice_date) AS integer) AS year, SUM(total) AS revenue "
        "FROM invoice GROUP BY 1 ORDER BY 1",
    )
    app = _open_growth()
    line = _chart_with(_lines(app), 5)
    assert [round(y, 2) for y in line["y"]] == [round(float(v), 2) for v in totals["revenue"]]
    revenue = [float(v) for v in totals["revenue"]]
    changes = ["none"] + [f"{100 * (b - a) / a:+.1f}%" for a, b in zip(revenue, revenue[1:])]
    assert list(app.dataframe[0].value["Change from prior year"]) == changes


def test_ac6_screen2_monthly_line(engine):
    # Given the Growth screen, when it loads, then a line of 60 months, January
    # 2021 to December 2025, oldest first, with January 2021 at 35.64.
    app = _open_growth()
    assert not app.exception
    line = _chart_with(_lines(app), 60)
    assert str(line["x"][0])[:10] == "2021-01-01"
    assert str(line["x"][-1])[:10] == "2025-12-01"
    assert round(line["y"][0], 2) == 35.64
    assert [str(x) for x in line["x"]] == sorted(str(x) for x in line["x"])
    assert any(h.value.startswith("Monthly revenue is usually about $38") for h in app.subheader)
    assert any("calendar month" in c.value for c in app.caption)


def test_ac6_monthly_line_reconciles_to_invoice_totals(engine):
    # Reconciliation: each month's point equals that month's invoice totals,
    # and the 60 months add to Finance's 2,328.60.
    totals = read_sql(
        engine,
        "SELECT TO_CHAR(invoice_date, 'YYYY-MM') AS month, SUM(total) AS revenue "
        "FROM invoice GROUP BY 1 ORDER BY 1",
    )
    line = _chart_with(_lines(_open_growth()), 60)
    assert [str(x)[:7] for x in line["x"]] == list(totals["month"])
    assert [round(y, 2) for y in line["y"]] == [round(float(v), 2) for v in totals["revenue"]]
    assert round(sum(line["y"]), 2) == round(float(scalar(engine, "SELECT SUM(total) FROM invoice")), 2)
