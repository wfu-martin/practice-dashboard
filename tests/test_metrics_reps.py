"""Issue #14: revenue per sales support rep (AC-9)."""

from conftest import scalar
from dashboard.metrics import read_sql, rep_customers, rep_revenue


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


def test_ac10_rep_customers_and_per_customer(engine):
    # Given the Sales reps screen, customers per rep are Jane 21, Margaret 20,
    # Steve 18, and revenue per customer is Jane 39.67, Margaret 38.77,
    # Steve 40.01.
    reps = rep_customers(engine)
    assert list(reps["rep"]) == ["Jane", "Margaret", "Steve"]
    customers = {r: int(n) for r, n in zip(reps["rep"], reps["customers"])}
    assert customers == {"Jane": 21, "Margaret": 20, "Steve": 18}
    per_customer = {
        r: round(float(v), 2) for r, v in zip(reps["rep"], reps["revenue_per_customer"])
    }
    assert per_customer == {"Jane": 39.67, "Margaret": 38.77, "Steve": 40.01}


def test_ac10_rep_customers_reconcile_to_customer_list(engine):
    # Reconciliation: counts come straight from the customer table, revenue
    # from invoice totals; revenue per customer is revenue divided by count,
    # and the reps' customers together are every customer.
    reps = rep_customers(engine)
    counts = read_sql(
        engine,
        """
        SELECT e.employee_id, COUNT(*) AS customers
        FROM customer AS c
        JOIN employee AS e ON e.employee_id = c.support_rep_id
        WHERE e.title = 'Sales Support Agent'
        GROUP BY e.employee_id
        """,
    )
    revenue = read_sql(
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
    want_counts = {int(k): int(v) for k, v in zip(counts["employee_id"], counts["customers"])}
    assert {int(k): int(v) for k, v in zip(reps["employee_id"], reps["customers"])} == want_counts
    want_revenue = {int(k): float(v) for k, v in zip(revenue["employee_id"], revenue["revenue"])}
    assert {
        int(k): round(float(v), 2)
        for k, v in zip(reps["employee_id"], reps["revenue_per_customer"])
    } == {k: round(want_revenue[k] / want_counts[k], 2) for k in want_counts}
    assert sum(want_counts.values()) == scalar(engine, "SELECT COUNT(*) FROM customer")
