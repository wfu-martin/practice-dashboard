"""Issue #19: Screen 1 share bars, top 5 genres and top 5 countries (AC-1, AC-3)."""

import base64
import json

import numpy as np
from streamlit.testing.v1 import AppTest

from conftest import scalar
from dashboard.metrics import read_sql


def _open_screen_1() -> AppTest:
    """Run streamlit_app.py showing Screen 1 (the first page in the navigation)."""

    def script():
        import runpy

        import streamlit as st

        pages = []
        real_page = st.Page

        def page(fn, **kwargs):
            pages.append(fn)
            return real_page(fn, **kwargs)

        class Chosen:
            def run(self):
                pages[0]()

        st.Page = page
        st.navigation = lambda *args, **kwargs: Chosen()
        runpy.run_path("streamlit_app.py")

    return AppTest.from_function(script, default_timeout=60).run()


def _values(array) -> list:
    """A trace's values; plotly may store numbers as base64 bytes plus a dtype."""
    if isinstance(array, dict):
        return np.frombuffer(base64.b64decode(array["bdata"]), dtype=array["dtype"]).tolist()
    return list(array)


def _bars(app: AppTest) -> list[dict]:
    """The bar trace of every chart on the screen: labels, values, order, format."""
    out = []
    for chart in app.get("plotly_chart"):
        trace = json.loads(chart.proto.spec)["data"][0]
        out.append({
            "x": _values(trace["x"]), "y": _values(trace["y"]),
            "orientation": trace["orientation"], "texttemplate": trace["texttemplate"],
        })
    return out


def _find(bars: list[dict], first_label: str) -> dict:
    """The chart whose top bar is `first_label` (the screen's other charts differ)."""
    matches = [b for b in bars if b["y"] and b["y"][0] == first_label]
    assert matches, f"no bar chart on Screen 1 starts with {first_label}"
    return matches[0]


def _shares(trace: dict) -> list[tuple[str, float]]:
    return [(label, round(100 * float(x), 1)) for label, x in zip(trace["y"], trace["x"])]


def test_ac1_screen1_genre_bars(engine):
    # Given all years are selected, when Screen 1 loads, then bars show the top
    # five genres as shares of revenue, largest first, labeled with percentages.
    app = _open_screen_1()
    assert not app.exception
    trace = _find(_bars(app), "Rock")
    assert _shares(trace) == [
        ("Rock", 35.5),
        ("Latin", 16.4),
        ("Metal", 11.2),
        ("Alternative & Punk", 10.4),
        ("TV Shows", 4.0),
    ]
    assert trace["orientation"] == "h"
    assert trace["texttemplate"] == "%{x:.1%}"  # percentages to one decimal
    assert any(h.value.startswith("Rock earns 35.5% of revenue") for h in app.subheader)


def test_ac3_screen1_country_bars(engine):
    # Given all years are selected, when Screen 1 loads, then bars show the top
    # five billing countries as shares of revenue, largest first, labeled with percentages.
    app = _open_screen_1()
    assert not app.exception
    trace = _find(_bars(app), "USA")
    assert _shares(trace) == [
        ("USA", 22.5),
        ("Canada", 13.1),
        ("France", 8.4),
        ("Brazil", 8.2),
        ("Germany", 6.7),
    ]
    assert trace["orientation"] == "h"
    assert trace["texttemplate"] == "%{x:.1%}"
    assert any("22.5% of revenue" in h.value for h in app.subheader)


def test_ac1_genre_bars_reconcile_to_invoice_totals(engine):
    # Reconciliation: each bar equals that genre's line revenue over the invoice
    # totals (a different table), and the five bars are the five largest genres.
    finance = float(scalar(engine, "SELECT SUM(total) FROM invoice"))
    top = read_sql(
        engine,
        "SELECT g.name AS genre, SUM(il.unit_price * il.quantity) AS revenue "
        "FROM genre AS g JOIN track AS t ON t.genre_id = g.genre_id "
        "JOIN invoice_line AS il ON il.track_id = t.track_id "
        "GROUP BY g.name ORDER BY revenue DESC LIMIT 5",
    )
    expected = [(r.genre, round(100 * float(r.revenue) / finance, 1)) for r in top.itertuples()]
    trace = _find(_bars(_open_screen_1()), "Rock")
    assert _shares(trace) == expected


def test_ac3_country_bars_reconcile_to_invoice_totals(engine):
    # Reconciliation: each bar equals that country's invoice totals over all
    # invoice totals, and the five bars are the five largest countries.
    finance = float(scalar(engine, "SELECT SUM(total) FROM invoice"))
    top = read_sql(
        engine,
        "SELECT billing_country AS country, SUM(total) AS revenue FROM invoice "
        "GROUP BY billing_country ORDER BY revenue DESC LIMIT 5",
    )
    expected = [(r.country, round(100 * float(r.revenue) / finance, 1)) for r in top.itertuples()]
    trace = _find(_bars(_open_screen_1()), "USA")
    assert _shares(trace) == expected


def _combos(trace: dict) -> list[tuple[str, float]]:
    return [(label, round(float(x), 2)) for label, x in zip(trace["y"], trace["x"])]


def test_ac4_screen1_combination_bars(engine):
    # Given all years are selected, when Screen 1 loads, then ranked bars show the
    # top ten country-and-genre combinations in dollars, largest first.
    app = _open_screen_1()
    assert not app.exception
    trace = _find(_bars(app), "USA - Rock")
    combos = _combos(trace)
    assert len(combos) == 10
    assert combos[:3] == [("USA - Rock", 155.43), ("Canada - Rock", 105.93), ("USA - Latin", 90.09)]
    assert [v for _, v in combos] == sorted((v for _, v in combos), reverse=True)
    assert trace["orientation"] == "h"
    assert trace["texttemplate"] == "%{x:$,.0f}"  # whole dollars
    assert any(h.value.startswith("USA Rock is the biggest single combination") for h in app.subheader)


def test_ac4_combination_bars_reconcile_to_invoice_lines(engine):
    # Reconciliation: each bar equals that country's and genre's invoice-line
    # revenue summed straight from the line, track, and invoice tables.
    top = read_sql(
        engine,
        "SELECT i.billing_country || ' - ' || g.name AS label, "
        "ROUND(SUM(il.unit_price * il.quantity), 2) AS revenue "
        "FROM invoice_line AS il, invoice AS i, track AS t, genre AS g "
        "WHERE il.invoice_id = i.invoice_id AND il.track_id = t.track_id "
        "AND t.genre_id = g.genre_id "
        "GROUP BY i.billing_country, g.name ORDER BY revenue DESC, g.name, i.billing_country LIMIT 10",
    )
    expected = [(r.label, float(r.revenue)) for r in top.itertuples()]
    trace = _find(_bars(_open_screen_1()), "USA - Rock")
    assert _combos(trace) == expected
