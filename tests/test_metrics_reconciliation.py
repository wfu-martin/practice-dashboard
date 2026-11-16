"""Issue #16: every breakdown of revenue adds up to the grand total (AC-12)."""

from conftest import scalar
from dashboard.metrics import breakdown_totals, finance_gap, grand_total, read_sql

BREAKDOWNS = ["genre", "country", "year", "rep"]


def test_ac12_each_breakdown_sums_to_total(engine):
    # Given all years are selected, when revenue is broken out by genre, by
    # country, by year, and by rep, then each breakdown adds up to 2,328.60.
    totals = breakdown_totals(engine)
    assert list(totals["breakdown"]) == BREAKDOWNS
    assert [round(float(v), 2) for v in totals["revenue"]] == [2328.60] * 4
    # ...and 2,328.60 is the grand total and the sum of invoice totals.
    assert round(float(grand_total(engine)["revenue"].iloc[0]), 2) == 2328.60
    assert finance_gap(engine)["gap"].iloc[0] == 0


def test_ac12_breakdown_totals_reconcile_to_invoice_totals(engine):
    # Reconciliation: each breakdown's sum and row count against a different
    # path: invoice totals (not invoice lines) for country, year, and rep,
    # and invoice lines by track genre id for genre.
    totals = breakdown_totals(engine).set_index("breakdown")
    finance = round(float(scalar(engine, "SELECT SUM(total) FROM invoice")), 2)
    by_genre = read_sql(
        engine,
        """
        SELECT COUNT(*) AS groups, SUM(revenue) AS revenue
        FROM (
            SELECT t.genre_id, SUM(il.unit_price * il.quantity) AS revenue
            FROM invoice_line AS il
            JOIN track AS t ON t.track_id = il.track_id
            GROUP BY t.genre_id
        ) AS g
        """,
    )
    by_country = read_sql(
        engine,
        """
        SELECT COUNT(*) AS groups, SUM(revenue) AS revenue
        FROM (SELECT SUM(total) AS revenue FROM invoice GROUP BY billing_country) AS c
        """,
    )
    by_year = read_sql(
        engine,
        """
        SELECT COUNT(*) AS groups, SUM(revenue) AS revenue
        FROM (
            SELECT SUM(total) AS revenue FROM invoice
            GROUP BY EXTRACT(YEAR FROM invoice_date)
        ) AS y
        """,
    )
    by_rep = read_sql(
        engine,
        """
        SELECT COUNT(*) AS groups, SUM(revenue) AS revenue
        FROM (
            SELECT SUM(i.total) AS revenue
            FROM invoice AS i
            JOIN customer AS c ON c.customer_id = i.customer_id
            JOIN employee AS e ON e.employee_id = c.support_rep_id
            WHERE e.title = 'Sales Support Agent'
            GROUP BY e.employee_id
        ) AS r
        """,
    )
    for name, expected in [
        ("genre", by_genre),
        ("country", by_country),
        ("year", by_year),
        ("rep", by_rep),
    ]:
        assert int(totals.loc[name, "groups"]) == int(expected["groups"].iloc[0]), name
        assert round(float(totals.loc[name, "revenue"]), 2) == round(
            float(expected["revenue"].iloc[0]), 2
        ) == finance, name
    assert [int(totals.loc[n, "groups"]) for n in BREAKDOWNS] == [24, 24, 5, 3]
