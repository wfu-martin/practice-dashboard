"""Issue #6: the grand total and the gap to Finance (AC-11)."""

from conftest import scalar
from dashboard.metrics import finance_gap, grand_total


def test_ac11_grand_total_is_2328_60(engine):
    # Given all years in view, the grand total is 2,328.60 and equals the
    # sum of invoice totals (the independent route: the invoice table).
    on_screen = float(grand_total(engine)["revenue"].iloc[0])
    independent = float(scalar(engine, "SELECT SUM(total) FROM invoice"))
    assert round(on_screen, 2) == 2328.60
    assert round(on_screen, 2) == round(independent, 2)


def test_ac11_gap_is_zero(engine):
    # The gap is line-item revenue minus Finance's invoice total. The
    # independent check counts invoices whose lines disagree with their total.
    gap = float(finance_gap(engine)["gap"].iloc[0])
    mismatched = scalar(
        engine,
        """
        SELECT COUNT(*) FROM (
            SELECT i.invoice_id
            FROM invoice AS i
            JOIN invoice_line AS il ON il.invoice_id = i.invoice_id
            GROUP BY i.invoice_id, i.total
            HAVING ROUND(SUM(il.unit_price * il.quantity), 2) <> ROUND(i.total, 2)
        ) AS bad
        """,
    )
    assert round(gap, 2) == 0.00
    assert mismatched == 0
