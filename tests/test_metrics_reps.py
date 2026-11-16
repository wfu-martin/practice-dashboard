"""Issue #14: revenue per sales support rep (AC-9)."""

from conftest import scalar
from dashboard.metrics import rep_revenue, read_sql


def test_ac9_rep_revenue(engine):
    # Given the Sales reps screen, revenue from each rep's customers is
    # Jane 833.04, Margaret 775.40, and Steve 720.16.
    reps = rep_revenue(engine)
    got = {r: round(float(v), 2) for r, v in zip(reps["rep"], reps["revenue"])}
    assert got == {"Jane": 833.04, "Margaret": 775.40, "Steve": 720.16}
    assert list(reps["rep"]) == ["Jane", "Margaret", "Steve"]


def test_ac9_rep_revenue_reconciles_to_invoice_totals(engine):
    # Reconciliation: the same figure from invoice totals (not invoice lines),
    # rep by rep, and the reps together equal the grand total.
    reps = rep_revenue(engine)
    expected = read_sql(
        engine,
        """
        SELECT e.employee_id, SUM(i.total) AS revenue
        FROM invoice AS i
        JOIN customer AS c ON c.customer_id = i.customer_id
        JOIN employee AS e ON e.employee_id = c.support_rep_id
        WHERE e.title = 'Sales Support Agent'
        GROUP BY e.employee_id
        """,
    )
    assert reps["employee_id"].is_unique
    assert {int(k): round(float(v), 2) for k, v in zip(reps["employee_id"], reps["revenue"])} == {
        int(k): round(float(v), 2) for k, v in zip(expected["employee_id"], expected["revenue"])
    }
    grand = scalar(engine, "SELECT SUM(total) FROM invoice")
    assert round(float(reps["revenue"].sum()), 2) == round(float(grand), 2)
