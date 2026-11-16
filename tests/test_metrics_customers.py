"""Issue #12: top-10 customers, revenue and share (AC-7)."""

from conftest import scalar
from dashboard.metrics import top10_customers


def test_ac7_top10_revenue_and_share(engine):
    # Given the Customers screen, the top 10 customers account for 451.20 of
    # revenue, which is 19.4% of the total.
    top = top10_customers(engine)
    assert round(float(top["revenue"].sum()), 2) == 451.20
    assert round(float(top["share_pct"].sum()), 1) == 19.4
    assert len(top) == 10


def test_ac7_top10_reconciles_to_invoice_totals(engine):
    # Reconciliation: rank customers by their invoice totals (a different
    # table), find the 10th-highest total, and keep everyone at or above it so
    # ties for 10th are included. The revenue, the customers chosen, and the
    # share of the invoice grand total all match.
    top = top10_customers(engine)
    tenth = scalar(
        engine,
        "SELECT SUM(total) FROM invoice GROUP BY customer_id "
        "ORDER BY SUM(total) DESC OFFSET 9 LIMIT 1",
    )
    expected_revenue = float(
        scalar(
            engine,
            "SELECT SUM(t) FROM (SELECT SUM(total) AS t FROM invoice "
            "GROUP BY customer_id) AS c WHERE t >= :tenth",
            {"tenth": tenth},
        )
    )
    expected_count = scalar(
        engine,
        "SELECT COUNT(*) FROM (SELECT SUM(total) AS t FROM invoice "
        "GROUP BY customer_id) AS c WHERE t >= :tenth",
        {"tenth": tenth},
    )
    finance_total = float(scalar(engine, "SELECT SUM(total) FROM invoice"))
    assert round(float(top["revenue"].sum()), 2) == round(expected_revenue, 2)
    assert len(top) == expected_count
    assert top["customer_id"].is_unique
    assert round(float(top["share_pct"].sum()), 2) == round(
        100 * expected_revenue / finance_total, 2
    )
    # Every customer shown earns at least the 10th-place amount.
    assert (top["revenue"].astype(float).round(2) >= round(float(tenth), 2)).all()
