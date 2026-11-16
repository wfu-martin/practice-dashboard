"""Issue #13: years bought for the top 10 customers (AC-8)."""

from conftest import scalar
from dashboard.metrics import top10_customers, top10_years_active, read_sql


def test_ac8_years_active_distribution(engine):
    # Given the Customers screen, of the top 10 customers 3 bought in 3 of the
    # 5 years, 5 bought in 4 years, and 2 bought in all 5 years.
    years = top10_years_active(engine)
    assert len(years) == 10
    counts = years["years_active"].value_counts().to_dict()
    assert counts == {3: 3, 4: 5, 5: 2}


def test_ac8_years_active_reconciles_to_invoice_dates(engine):
    # Reconciliation: pick the customers from invoice totals (not invoice
    # lines), count distinct years from invoice dates in a separate query, and
    # compare customer by customer. Same customers as the top-10 revenue list.
    years = top10_years_active(engine)
    tenth = scalar(
        engine,
        "SELECT SUM(total) FROM invoice GROUP BY customer_id "
        "ORDER BY SUM(total) DESC OFFSET 9 LIMIT 1",
    )
    expected = read_sql(
        engine,
        """
        SELECT customer_id,
               COUNT(DISTINCT EXTRACT(YEAR FROM invoice_date)) AS years_active
        FROM invoice
        WHERE customer_id IN (
            SELECT customer_id FROM invoice
            GROUP BY customer_id HAVING SUM(total) >= :tenth
        )
        GROUP BY customer_id
        """,
        {"tenth": tenth},
    )
    assert years["customer_id"].is_unique
    assert dict(zip(years["customer_id"], years["years_active"].astype(int))) == dict(
        zip(expected["customer_id"], expected["years_active"].astype(int))
    )
    assert set(years["customer_id"]) == set(top10_customers(engine)["customer_id"])
    assert years["years_active"].between(1, 5).all()
