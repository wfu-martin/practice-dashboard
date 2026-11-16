"""Issue #10: yearly revenue and change from the prior year (AC-5)."""

import pandas as pd

from conftest import scalar
from dashboard.metrics import yearly_revenue


def test_ac5_yearly_revenue_and_change(engine):
    # Given the Growth screen, yearly revenue and change from the prior year
    # are as the spec lists; 2021 has no prior year, so its change is empty.
    yearly = yearly_revenue(engine)
    assert list(yearly["year"]) == [2021, 2022, 2023, 2024, 2025]
    assert [round(float(r), 2) for r in yearly["revenue"]] == [
        449.46, 481.45, 469.58, 477.53, 450.58,
    ]
    assert pd.isna(yearly["change_pct"].iloc[0])
    assert [round(float(c), 1) for c in yearly["change_pct"].iloc[1:]] == [
        7.1, -2.5, 1.7, -5.6,
    ]


def test_ac5_yearly_revenue_reconciles_to_invoice_totals(engine):
    # Reconciliation: each year's revenue equals the invoice totals for that
    # year (a different table), the years add to the grand total, and each
    # change is recomputed from those independent yearly totals.
    yearly = yearly_revenue(engine)
    for row in yearly.itertuples():
        invoice_total = float(
            scalar(
                engine,
                "SELECT SUM(total) FROM invoice "
                "WHERE EXTRACT(YEAR FROM invoice_date) = :year",
                {"year": int(row.year)},
            )
        )
        assert round(float(row.revenue), 2) == round(invoice_total, 2)
    finance_total = float(scalar(engine, "SELECT SUM(total) FROM invoice"))
    assert round(float(yearly["revenue"].sum()), 2) == round(finance_total, 2)
    assert yearly["year"].is_unique
    # 2025 ends 22 Dec, so its -5.6% is a nearly full year against a full one.
    last_2025 = scalar(
        engine,
        "SELECT MAX(invoice_date) FROM invoice "
        "WHERE EXTRACT(YEAR FROM invoice_date) = 2025",
    )
    assert (last_2025.month, last_2025.day) == (12, 22)
    totals = [float(r) for r in yearly["revenue"]]
    for prior, this, change in zip(totals, totals[1:], yearly["change_pct"].iloc[1:]):
        assert round(float(change), 2) == round(100 * (this - prior) / prior, 2)

