"""Issue #22: Screen 3 Customers, top-10 bars and years bought (AC-7, AC-8)."""

from streamlit.testing.v1 import AppTest

from conftest import scalar
from dashboard.metrics import read_sql
from test_screen1 import _bars

CUSTOMERS = 2  # the third page in the navigation
TOP_TEN = "Helena Holý"  # the largest customer, so the top bar of the right chart


def _open_customers() -> AppTest:
    """Run streamlit_app.py showing Screen 3 (the Customers page)."""

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

    return AppTest.from_function(script, args=(CUSTOMERS,), default_timeout=60).run()


def _customer_bars(app: AppTest) -> dict:
    matches = [b for b in _bars(app) if b["y"] and TOP_TEN in b["y"]]
    assert matches, "no ranked bars of the top 10 customers on Screen 3"
    return matches[0]


def _years_table(app: AppTest):
    matches = [d.value for d in app.dataframe if "Years bought (of 5)" in d.value.columns]
    assert matches, "no years-bought table on Screen 3"
    return matches[0]


def _ranked(trace: dict) -> list[tuple[str, float]]:
    """(customer, revenue) from the top bar down; plotly lists the chart bottom-up."""
    return [(label, round(float(x), 2)) for label, x in zip(trace["y"], trace["x"])]


def test_ac7_screen3_top10_share(engine):
    # Given the Customers screen, when it loads, then ranked bars show the top 10
    # customers in dollars, largest first, totaling 451.20 (19.4% of revenue), and
    # the headline over them says so.
    app = _open_customers()
    assert not app.exception
    trace = _customer_bars(app)
    bars = _ranked(trace)
    assert len(bars) == 10
    assert bars[0] == ("Helena Holý", 49.62)
    assert [v for _, v in bars] == sorted((v for _, v in bars), reverse=True)
    assert round(sum(v for _, v in bars), 2) == 451.20
    assert trace["orientation"] == "h"
    assert trace["texttemplate"] == "%{x:$,.0f}"  # whole dollars
    assert any(
        h.value.startswith(r"Top 10 customers bring in \$451, 19.4% of total") for h in app.subheader
    )
    assert any("by customer" in c.value and "ties" in c.value for c in app.caption)


def test_ac7_customer_bars_reconcile_to_invoice_totals(engine):
    # Reconciliation: each bar equals that customer's invoice totals (a different
    # table); the bars are every customer at or above the 10th-highest total.
    top = read_sql(
        engine,
        "SELECT c.first_name || ' ' || c.last_name AS customer, SUM(i.total) AS revenue "
        "FROM invoice AS i JOIN customer AS c ON c.customer_id = i.customer_id "
        "GROUP BY c.customer_id, c.first_name, c.last_name "
        "HAVING SUM(i.total) >= (SELECT SUM(total) FROM invoice GROUP BY customer_id "
        "ORDER BY SUM(total) DESC OFFSET 9 LIMIT 1)",
    )
    expected = {r.customer: round(float(r.revenue), 2) for r in top.itertuples()}
    bars = _ranked(_customer_bars(_open_customers()))
    assert dict(bars) == expected
    assert round(sum(expected.values()) / float(scalar(engine, "SELECT SUM(total) FROM invoice")), 3) == 0.194


def test_ac8_screen3_years_table(engine):
    # Given the Customers screen, when it loads, then a table lists each top-10
    # customer with years bought of 5: 3 bought in 3 years, 5 in 4, and 2 in all 5.
    app = _open_customers()
    assert not app.exception
    table = _years_table(app)
    assert list(table.columns) == ["Customer", "Years bought (of 5)"]
    assert len(table) == 10
    counts = table["Years bought (of 5)"].astype(int).value_counts().to_dict()
    assert counts == {3: 3, 4: 5, 5: 2}
    assert any(h.value.startswith("2 of the top 10 bought in all 5 years") for h in app.subheader)
    assert any("at least one invoice" in c.value for c in app.caption)


def test_ac8_years_table_reconciles_to_invoice_dates(engine):
    # Reconciliation: for each customer in the table, count the distinct years
    # of their invoice dates in a separate query.
    table = _years_table(_open_customers())
    names = list(table["Customer"])
    expected = read_sql(
        engine,
        "SELECT c.first_name || ' ' || c.last_name AS customer, "
        "COUNT(DISTINCT EXTRACT(YEAR FROM i.invoice_date)) AS years "
        "FROM invoice AS i JOIN customer AS c ON c.customer_id = i.customer_id "
        "GROUP BY c.customer_id, c.first_name, c.last_name",
    )
    years = {r.customer: int(r.years) for r in expected.itertuples()}
    assert set(names) == set(dict(_ranked(_customer_bars(_open_customers()))))
    assert {n: int(y) for n, y in zip(names, table["Years bought (of 5)"])} == {n: years[n] for n in names}
