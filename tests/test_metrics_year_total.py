"""Issue #24: the year choices and the total for one year (AC-2)."""

import pandas as pd

from conftest import scalar
from dashboard.metrics import available_years, read_sql, year_total


def test_ac2_year_2023_total_is_469_58(engine):
    # Given the year 2023, the grand total is 469.58; with no year it is the
    # all-years total, 2,328.60.
    assert round(float(year_total(engine, 2023).loc[0, "revenue"]), 2) == 469.58
    assert round(float(year_total(engine).loc[0, "revenue"]), 2) == 2328.60


def test_ac2_year_total_reconciles_to_invoice_totals(engine):
    # Reconciliation: each year's line-item total equals that year's invoice
    # totals (a different table), and a year with no invoices has no revenue.
    for year in available_years(engine)["year"]:
        finance = scalar(
            engine,
            "SELECT SUM(total) FROM invoice WHERE EXTRACT(YEAR FROM invoice_date) = :y",
            {"y": int(year)},
        )
        assert round(float(year_total(engine, int(year)).loc[0, "revenue"]), 2) == round(float(finance), 2)
    none = year_total(engine, 2019).loc[0, "revenue"]
    assert pd.isna(none) or float(none) == 0  # no invoices: empty or zero, never an error


def test_ac2_available_years_reconcile_to_invoices(engine):
    # Reconciliation: the picker's choices are exactly the years that have
    # invoices, oldest first (2021 to 2025).
    years = available_years(engine)
    assert list(years.columns) == ["year"]
    expected = sorted(
        int(y)
        for y in read_sql(engine, "SELECT DISTINCT EXTRACT(YEAR FROM invoice_date) AS y FROM invoice")["y"]
    )
    assert [int(y) for y in years["year"]] == expected == [2021, 2022, 2023, 2024, 2025]
