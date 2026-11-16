"""Issue #23: Screen 4 Sales reps, revenue bars and customers table (AC-9, AC-10)."""

from streamlit.testing.v1 import AppTest

from dashboard.metrics import read_sql
from test_screen1 import _bars

SALES_REPS = 3  # the fourth page in the navigation
TOP_REP = "Jane"  # the largest rep, so the top bar of the right chart


def _open_sales_reps() -> AppTest:
    """Run streamlit_app.py showing Screen 4 (the Sales reps page)."""

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

    return AppTest.from_function(script, args=(SALES_REPS,), default_timeout=60).run()


def _rep_bars(app: AppTest) -> dict:
    matches = [b for b in _bars(app) if b["y"] and TOP_REP in b["y"]]
    assert matches, "no ranked bars of revenue by rep on Screen 4"
    return matches[0]


def _rep_table(app: AppTest):
    matches = [d.value for d in app.dataframe if "Revenue per customer" in d.value.columns]
    assert matches, "no customers table on Screen 4"
    return matches[0]


def _ranked(trace: dict) -> list[tuple[str, float]]:
    """(rep, revenue) from the top bar down; plotly lists the chart bottom-up."""
    return [(label, round(float(x), 2)) for label, x in zip(trace["y"], trace["x"])]


def test_ac9_screen4_rep_bars(engine):
    # Given the Sales reps screen, when it loads, then ranked bars show revenue from
    # each rep's customers in dollars, largest first: Jane 833.04, Margaret 775.40,
    # Steve 720.16, and the headline over them says so.
    app = _open_sales_reps()
    assert not app.exception
    trace = _rep_bars(app)
    assert _ranked(trace) == [("Jane", 833.04), ("Margaret", 775.40), ("Steve", 720.16)]
    assert trace["orientation"] == "h"
    assert trace["texttemplate"] == "%{x:$,.0f}"  # whole dollars
    assert any(
        h.value == r"Jane's customers bring in \$833, Steve's \$720" for h in app.subheader
    )
    assert any("each sales rep's customers" in c.value and "full period" in c.value for c in app.caption)


def test_ac9_rep_bars_reconcile_to_invoice_totals(engine):
    # Reconciliation: each bar equals the invoice totals of that rep's customers
    # (invoice table instead of invoice lines).
    expected = read_sql(
        engine,
        "SELECT e.first_name AS rep, SUM(i.total) AS revenue "
        "FROM invoice AS i JOIN customer AS c ON c.customer_id = i.customer_id "
        "JOIN employee AS e ON e.employee_id = c.support_rep_id "
        "WHERE e.title = 'Sales Support Agent' GROUP BY e.employee_id, e.first_name",
    )
    want = {r.rep: round(float(r.revenue), 2) for r in expected.itertuples()}
    assert dict(_ranked(_rep_bars(_open_sales_reps()))) == want


def test_ac10_screen4_rep_table(engine):
    # Given the Sales reps screen, when it loads, then a table lists each rep with
    # customers (Jane 21, Margaret 20, Steve 18) and revenue per customer to the cent
    # (Jane $39.67, Margaret $38.77, Steve $40.01).
    app = _open_sales_reps()
    assert not app.exception
    table = _rep_table(app)
    assert list(table.columns) == ["Rep", "Customers", "Revenue per customer"]
    rows = {r.Rep: (int(r.Customers), r._2) for r in table.itertuples(index=False)}
    assert rows == {"Jane": (21, "$39.67"), "Margaret": (20, "$38.77"), "Steve": (18, "$40.01")}
    assert any(h.value == r"Revenue per customer is within \$1.24 across reps" for h in app.subheader)
    assert any("Customers and revenue per customer" in c.value and "full period" in c.value for c in app.caption)


def test_ac10_rep_table_reconciles_to_customer_invoices(engine):
    # Reconciliation: customers counted from the customer table, revenue per
    # customer from invoice totals divided by that count.
    expected = read_sql(
        engine,
        "SELECT e.first_name AS rep, COUNT(*) AS customers, "
        "SUM((SELECT COALESCE(SUM(i.total), 0) FROM invoice AS i "
        "WHERE i.customer_id = c.customer_id)) / COUNT(*) AS per_customer "
        "FROM customer AS c JOIN employee AS e ON e.employee_id = c.support_rep_id "
        "WHERE e.title = 'Sales Support Agent' GROUP BY e.employee_id, e.first_name",
    )
    want = {r.rep: (int(r.customers), f"${float(r.per_customer):,.2f}") for r in expected.itertuples()}
    table = _rep_table(_open_sales_reps())
    got = {r.Rep: (int(r.Customers), r._2) for r in table.itertuples(index=False)}
    assert got == want
