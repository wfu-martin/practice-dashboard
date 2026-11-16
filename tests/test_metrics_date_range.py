"""Issue #26: the date range the data covers, shown under the Screen 2 to 4 headlines."""

import pandas as pd

from conftest import scalar
from dashboard.metrics import invoice_date_range


def test_ac11_date_range_reconciles_to_invoices(engine):
    # Reconciliation: the first and last dates equal the earliest and latest
    # invoice found a different way (ordering the invoices, not MIN and MAX).
    shown = invoice_date_range(engine)
    assert list(shown.columns) == ["first_date", "last_date"]
    first = scalar(engine, "SELECT invoice_date FROM invoice ORDER BY invoice_date ASC LIMIT 1")
    last = scalar(engine, "SELECT invoice_date FROM invoice ORDER BY invoice_date DESC LIMIT 1")
    assert pd.Timestamp(shown.loc[0, "first_date"]) == pd.Timestamp(first)
    assert pd.Timestamp(shown.loc[0, "last_date"]) == pd.Timestamp(last)


def test_ac11_date_range_is_jan_2021_to_22_dec_2025(engine):
    # The data runs 2021-01-01 to 2025-12-22, the period the captions name.
    shown = invoice_date_range(engine)
    assert pd.Timestamp(shown.loc[0, "first_date"]).date().isoformat() == "2021-01-01"
    assert pd.Timestamp(shown.loc[0, "last_date"]).date().isoformat() == "2025-12-22"
