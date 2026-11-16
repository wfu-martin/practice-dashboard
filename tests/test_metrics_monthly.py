"""Issue #11: monthly revenue (AC-6)."""

from conftest import scalar
from dashboard.metrics import monthly_revenue
from sqlalchemy import text


def test_ac6_monthly_60_months_jan_2021(engine):
    # Given the Growth screen, monthly revenue shows 60 months from January
    # 2021 to December 2025, and January 2021 is 35.64.
    monthly = monthly_revenue(engine)
    assert len(monthly) == 60
    assert monthly["month"].is_unique
    first, last = monthly["month"].iloc[0], monthly["month"].iloc[-1]
    assert (first.year, first.month) == (2021, 1)
    assert (last.year, last.month) == (2025, 12)
    assert round(float(monthly["revenue"].iloc[0]), 2) == 35.64


def test_ac6_monthly_revenue_reconciles_to_invoice_totals(engine):
    # Reconciliation: each month's revenue equals that month's invoice totals
    # (a different table), and the 60 months add up to the grand total.
    monthly = monthly_revenue(engine)
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT CAST(EXTRACT(YEAR FROM invoice_date) AS integer) AS y, "
                "CAST(EXTRACT(MONTH FROM invoice_date) AS integer) AS m, "
                "SUM(total) FROM invoice GROUP BY 1, 2"
            )
        ).all()
    expected = {(y, m): round(float(t), 2) for y, m, t in rows}
    actual = {
        (r.month.year, r.month.month): round(float(r.revenue), 2)
        for r in monthly.itertuples()
    }
    assert actual == expected
    finance_total = float(scalar(engine, "SELECT SUM(total) FROM invoice"))
    assert round(float(monthly["revenue"].sum()), 2) == round(finance_total, 2)
