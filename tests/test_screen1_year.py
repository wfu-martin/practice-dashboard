"""Issue #24: the year picker on Screen 1 (AC-2).

Screen 1's genre bars, country bars, combination bars, tiles and headlines
follow the year chosen in the sidebar; the default is all years.
"""

from streamlit.testing.v1 import AppTest

from conftest import scalar
from dashboard.metrics import read_sql
from test_screen1 import _bars, _combos, _find, _shares

ALL = "All years"


def _script():
    """Run streamlit_app.py showing Screen 1 (the first page in the navigation)."""
    import os
    import runpy

    import pandas as pd
    import streamlit as st

    from dashboard import metrics

    if os.environ.get("ADD_YEAR_WITHOUT_INVOICES"):  # a choice that leaves no rows
        real = metrics.available_years
        metrics.available_years = lambda engine: pd.concat(
            [pd.DataFrame({"year": [int(os.environ["ADD_YEAR_WITHOUT_INVOICES"])]}), real(engine)],
            ignore_index=True,
        )

    pages = []
    real_page = st.Page

    def page(fn, **kwargs):
        pages.append(fn)
        return real_page(fn, **kwargs)

    class Chosen:
        def run(self):
            pages[0]()

    st.cache_data.clear()  # every run asks the database afresh
    st.Page = page
    st.navigation = lambda *args, **kwargs: Chosen()
    runpy.run_path("streamlit_app.py")


def _picker(app: AppTest):
    """The sidebar's year picker (a dropdown labeled Year)."""
    pickers = [s for s in app.sidebar.selectbox if s.label == "Year"]
    assert pickers, "Screen 1 has no Year dropdown in the sidebar"
    return pickers[0]


def _open(year=None) -> AppTest:
    """Screen 1, with `year` picked in the sidebar (None leaves the default)."""
    app = AppTest.from_function(_script, default_timeout=60).run()
    assert not app.exception
    if year is not None:
        _picker(app).set_value(year).run()
        assert not app.exception
    return app


def _tiles(app: AppTest) -> dict:
    return {m.label: (m.value, m.delta) for m in app.metric}


def _year_revenue(engine, year: int) -> float:
    return float(
        scalar(engine, "SELECT SUM(total) FROM invoice WHERE EXTRACT(YEAR FROM invoice_date) = :y", {"y": year})
    )


def test_ac2_screen1_year_picker_defaults_to_all_years(engine):
    # Given nothing is picked, when Screen 1 loads, then the Year dropdown reads
    # All years and offers each year that has invoices (2021 to 2025), and the
    # tiles show the all-years total against Finance.
    app = _open()
    picker = _picker(app)
    years = sorted(
        int(y) for y in read_sql(engine, "SELECT DISTINCT EXTRACT(YEAR FROM invoice_date) AS y FROM invoice")["y"]
    )
    assert picker.value == ALL
    assert list(picker.options) == [ALL] + [str(y) for y in years]
    assert _tiles(app)["Total revenue"] == ("$2,329", "+$0 vs Finance")
    assert any("all years" in c.value for c in app.caption)


def test_ac2_screen1_year_2023_total_and_top_genre(engine):
    # Given the year 2023 is selected, when Screen 1 loads, then the grand total
    # is 469.58 (shown as $470 in whole dollars) and the top genre is Rock, at
    # 156.42, a 33.3% share of that total.
    app = _open(2023)
    trace = _find(_bars(app), "Rock")
    assert _shares(trace)[0] == ("Rock", round(100 * 156.42 / 469.58, 1)) == ("Rock", 33.3)
    assert _tiles(app)["Total revenue"][0] == "$470"
    assert _tiles(app)["Top genre: Rock"][0] == "33.3%"
    assert any(h.value.startswith("Rock earns 33.3% of revenue") for h in app.subheader)
    assert any("2023" in c.value for c in app.caption)
    assert not any("all years" in c.value for c in app.caption)
    assert float(scalar(engine, "SELECT SUM(total) FROM invoice WHERE EXTRACT(YEAR FROM invoice_date) = 2023")) == 469.58


def test_ac2_year_2023_total_tile_against_yearly_average(engine):
    # For one year the total tile is set against the average year (the
    # yearly mean of all five), as design.md draws it.
    yearly = [_year_revenue(engine, y) for y in range(2021, 2026)]
    average = sum(yearly) / len(yearly)
    app = _open(2023)
    value, delta = _tiles(app)["Total revenue"]
    assert value == "$470"
    assert delta == f"+${round(469.58 - average):,} vs yearly average"  # about +$4


def test_ac2_year_2023_genre_bars_reconcile_to_invoice_lines(engine):
    # Reconciliation: with 2023 picked, each genre bar is that genre's 2023
    # invoice-line revenue over the 2023 invoice totals, the five largest.
    top = read_sql(
        engine,
        "SELECT g.name AS genre, SUM(il.unit_price * il.quantity) AS revenue "
        "FROM invoice_line AS il, invoice AS i, track AS t, genre AS g "
        "WHERE il.invoice_id = i.invoice_id AND il.track_id = t.track_id AND t.genre_id = g.genre_id "
        "AND i.invoice_date >= '2023-01-01' AND i.invoice_date < '2024-01-01' "
        "GROUP BY g.name ORDER BY revenue DESC LIMIT 5",
    )
    finance = _year_revenue(engine, 2023)
    expected = [(r.genre, round(100 * float(r.revenue) / finance, 1)) for r in top.itertuples()]
    assert _shares(_find(_bars(_open(2023)), "Rock")) == expected


def test_ac2_year_2023_country_bars_reconcile_to_invoice_totals(engine):
    # Reconciliation: with 2023 picked, each country bar is that country's 2023
    # invoice totals over all 2023 invoice totals, the five largest.
    top = read_sql(
        engine,
        "SELECT billing_country AS country, SUM(total) AS revenue FROM invoice "
        "WHERE invoice_date >= '2023-01-01' AND invoice_date < '2024-01-01' "
        "GROUP BY billing_country ORDER BY revenue DESC LIMIT 5",
    )
    finance = _year_revenue(engine, 2023)
    expected = [(r.country, round(100 * float(r.revenue) / finance, 1)) for r in top.itertuples()]
    assert _shares(_find(_bars(_open(2023)), expected[0][0])) == expected
    app = _open(2023)
    assert _tiles(app)[f"Top country: {expected[0][0]}"][0] == f"{expected[0][1]:.1f}%"


def test_ac2_year_2023_combination_bars_reconcile_to_invoice_lines(engine):
    # Reconciliation: with 2023 picked, the top-10 combination bars are 2023
    # only (the #20 review note), not the all-years bars.
    top = read_sql(
        engine,
        "SELECT i.billing_country || ' - ' || g.name AS label, "
        "ROUND(SUM(il.unit_price * il.quantity), 2) AS revenue "
        "FROM invoice_line AS il, invoice AS i, track AS t, genre AS g "
        "WHERE il.invoice_id = i.invoice_id AND il.track_id = t.track_id AND t.genre_id = g.genre_id "
        "AND i.invoice_date >= '2023-01-01' AND i.invoice_date < '2024-01-01' "
        "GROUP BY i.billing_country, g.name ORDER BY revenue DESC, g.name, i.billing_country LIMIT 10",
    )
    expected = [(r.label, float(r.revenue)) for r in top.itertuples()]
    app = _open(2023)
    assert _combos(_find(_bars(app), expected[0][0])) == expected
    assert expected[0][0] != "USA - Rock"  # a different top than all years
    assert any(h.value.startswith(f"{expected[0][0].replace(' - ', ' ')} is the biggest") for h in app.subheader)


def test_ac2_picking_all_years_again_restores_the_default_view(engine):
    # Given 2023 is picked and then All years, Screen 1 shows the all-years
    # figures again.
    app = _open(2023)
    _picker(app).set_value(ALL).run()
    assert not app.exception
    assert _shares(_find(_bars(app), "Rock"))[0] == ("Rock", 35.5)
    assert _tiles(app)["Total revenue"][0] == "$2,329"


def test_ac2_year_with_no_rows_shows_nothing_to_show(engine, monkeypatch):
    # Given a year with no invoices is picked, when Screen 1 loads, then a short
    # note replaces the charts and tiles, with no error.
    monkeypatch.setenv("ADD_YEAR_WITHOUT_INVOICES", "2019")
    app = _open(2019)
    assert [n.value for n in app.info] == ["No data for 2019. Widen the filters to see results."]
    assert not app.get("plotly_chart")
    assert not app.metric
