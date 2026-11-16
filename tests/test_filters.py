"""Issue #25: Screens 2-4 ignore the year picker (AC-13).

The year picker lives on Screen 1. With 2023 picked there, Growth, Customers
and Sales reps still show the full period (all five years).
"""

from streamlit.testing.v1 import AppTest

from dashboard.metrics import read_sql
from test_screen1 import _bars
from test_screen1_year import _picker, _tiles
from test_screen2 import _chart_with, _lines
from test_screen3 import _customer_bars, _ranked as _ranked_customers, _years_table
from test_screen4 import _rep_bars, _ranked as _ranked_reps


def _script():
    """streamlit_app.py showing the screen named by st.session_state['screen'] (0 to 3)."""
    import runpy

    import streamlit as st

    pages = []
    real_page = st.Page

    def page(fn, **kwargs):
        pages.append(fn)
        return real_page(fn, **kwargs)

    class Chosen:
        def run(self):
            pages[st.session_state.get("screen", 0)]()

    st.Page = page
    st.navigation = lambda *args, **kwargs: Chosen()
    runpy.run_path("streamlit_app.py")


def _with_2023_picked() -> AppTest:
    """One session: Screen 1 with 2023 picked, ready to move on to other screens."""
    app = AppTest.from_function(_script, default_timeout=60).run()
    _picker(app).set_value("2023").run()
    assert not app.exception
    assert _tiles(app)["Total revenue"][0] == "$470"  # 2023 really is in force
    return app


def _go_to(app: AppTest, screen: int) -> AppTest:
    app.session_state["screen"] = screen
    app.run()
    assert not app.exception
    return app


def test_ac13_other_screens_show_full_period(engine):
    # Given 2023 is picked on Screen 1, when the user opens Growth, Customers
    # and Sales reps in the same visit, then each shows the full period: Growth
    # still draws all five years, and the customer and rep bars equal the
    # full-period invoice totals.
    app = _with_2023_picked()

    growth = _go_to(app, 1)
    totals = read_sql(
        engine,
        "SELECT CAST(EXTRACT(YEAR FROM invoice_date) AS integer) AS year, SUM(total) AS revenue "
        "FROM invoice GROUP BY 1 ORDER BY 1",
    )
    assert list(totals["year"]) == [2021, 2022, 2023, 2024, 2025]
    line = _chart_with(_lines(growth), 5)
    assert [str(x) for x in line["x"]] == ["2021", "2022", "2023", "2024", "2025"]
    assert [round(y, 2) for y in line["y"]] == [round(float(v), 2) for v in totals["revenue"]]
    assert list(growth.dataframe[0].value["Year"].astype(str)) == ["2021", "2022", "2023", "2024", "2025"]

    customers = _go_to(app, 2)
    top = read_sql(
        engine,
        "SELECT c.first_name || ' ' || c.last_name AS customer, SUM(i.total) AS revenue "
        "FROM invoice AS i, customer AS c WHERE i.customer_id = c.customer_id "
        "GROUP BY c.customer_id, c.first_name, c.last_name ORDER BY revenue DESC LIMIT 10",
    )
    assert round(sum(r for _, r in _ranked_customers(_customer_bars(customers))), 2) == round(float(top["revenue"].sum()), 2)
    years = read_sql(
        engine,
        "SELECT c.first_name || ' ' || c.last_name AS customer, "
        "COUNT(DISTINCT EXTRACT(YEAR FROM i.invoice_date)) AS years_bought "
        "FROM invoice AS i, customer AS c WHERE i.customer_id = c.customer_id "
        "GROUP BY c.customer_id, c.first_name, c.last_name",
    ).set_index("customer")["years_bought"]
    table = _years_table(customers)
    assert len(table) >= 10
    assert dict(zip(table["Customer"], table["Years bought (of 5)"].astype(int))) == {c: int(years[c]) for c in table["Customer"]}

    reps = _go_to(app, 3)
    by_rep = read_sql(
        engine,
        "SELECT e.first_name || ' ' || e.last_name AS rep, SUM(i.total) AS revenue "
        "FROM invoice AS i, customer AS c, employee AS e "
        "WHERE i.customer_id = c.customer_id AND c.support_rep_id = e.employee_id "
        "GROUP BY e.employee_id, e.first_name, e.last_name ORDER BY revenue DESC",
    )
    assert round(sum(r for _, r in _ranked_reps(_rep_bars(reps))), 2) == round(float(by_rep["revenue"].sum()), 2) == 2328.60
