"""Issue #18: the "Check against Finance" section and the gap tile (AC-11, AC-12)."""

import pytest
from streamlit.testing.v1 import AppTest

from conftest import scalar
from dashboard.metrics import finance_check, read_sql

ROWS = ["genre", "country", "year", "rep", "invoices"]
SCREENS = ["money", "growth", "customers", "reps"]  # in navigation order


def test_ac12_finance_table_rows_sum_to_total(engine):
    # Given all years are selected, when revenue is broken out by genre, by
    # country, by year, and by rep, then each breakdown adds up to 2,328.60
    # (and so does the sum of invoice totals, the table's fifth row).
    table = finance_check(engine)
    assert list(table["breakdown"]) == ROWS
    assert [round(float(v), 2) for v in table["revenue"]] == [2328.60] * 5
    assert [round(float(v), 2) for v in table["finance_total"]] == [2328.60] * 5
    assert [round(float(v), 2) for v in table["gap"]] == [0.0] * 5


def test_ac12_finance_check_reconciles_to_invoices(engine):
    # Reconciliation: the table's counts and totals against plain invoice
    # queries, a different path from the line-item figures behind it.
    table = finance_check(engine).set_index("breakdown")
    finance = round(float(scalar(engine, "SELECT SUM(total) FROM invoice")), 2)
    invoices = int(scalar(engine, "SELECT COUNT(*) FROM invoice"))
    by_country = int(scalar(engine, "SELECT COUNT(DISTINCT billing_country) FROM invoice"))
    by_year = int(
        scalar(engine, "SELECT COUNT(DISTINCT EXTRACT(YEAR FROM invoice_date)) FROM invoice")
    )
    by_genre = int(
        scalar(
            engine,
            "SELECT COUNT(DISTINCT t.genre_id) FROM invoice_line AS il "
            "JOIN track AS t ON t.track_id = il.track_id",
        )
    )
    by_rep = int(
        scalar(
            engine,
            "SELECT COUNT(DISTINCT c.support_rep_id) FROM invoice AS i "
            "JOIN customer AS c ON c.customer_id = i.customer_id",
        )
    )
    assert (finance, invoices) == (2328.60, 412)
    assert [int(table.loc[n, "groups"]) for n in ROWS] == [
        by_genre, by_country, by_year, by_rep, invoices,
    ]
    assert table.loc["invoices", "groups"] == 412
    for name in ROWS:
        assert round(float(table.loc[name, "finance_total"]), 2) == finance, name
        assert round(float(table.loc[name, "revenue"]), 2) == finance, name
        assert round(float(table.loc[name, "gap"]), 2) == 0, name
    # Finance's total reached by a second route: the invoice lines.
    lines = read_sql(engine, "SELECT SUM(unit_price * quantity) AS v FROM invoice_line")
    assert round(float(lines["v"].iloc[0]), 2) == finance


def _open_screen(index: int) -> AppTest:
    """Run streamlit_app.py showing one screen (by its place in the navigation)."""

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

    return AppTest.from_function(script, args=(index,), default_timeout=60).run()


@pytest.mark.parametrize("screen", range(len(SCREENS)), ids=SCREENS)
def test_ac11_finance_gap_tile_shows_zero(engine, screen):
    # Given any screen with all years in view, when it loads, then the gap
    # tile reads $0.00 and a collapsed "Check against Finance" section holds
    # the table that shows 2,328.60 on every row with a gap of 0.00.
    app = _open_screen(screen)
    assert not app.exception
    tiles = {m.label: m.value for m in app.metric}
    assert tiles["Gap vs Finance"] == "$0.00"

    sections = [e for e in app.expander if e.label == "Check against Finance"]
    assert len(sections) == 1
    assert not sections[0].proto.expanded  # collapsed until opened
    table = sections[0].dataframe[0].value
    assert len(table) == 5
    assert [round(float(v), 2) for v in table["Finance total"]] == [2328.60] * 5
    assert [round(float(v), 2) for v in table["Gap"]] == [0.0] * 5
