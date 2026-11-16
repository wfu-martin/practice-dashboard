"""Issue #8: country revenue and share (AC-3)."""

from conftest import scalar
from dashboard.metrics import country_revenue_share


def test_ac3_top5_countries_and_shares(engine):
    # Given all years, the top five countries and their shares are as the spec lists.
    top5 = country_revenue_share(engine).head(5)
    got = [
        (row.country, round(float(row.revenue), 2), round(float(row.share_pct), 1))
        for row in top5.itertuples()
    ]
    assert got == [
        ("USA", 523.06, 22.5),
        ("Canada", 303.96, 13.1),
        ("France", 195.10, 8.4),
        ("Brazil", 190.10, 8.2),
        ("Germany", 156.48, 6.7),
    ]


def test_ac3_countries_reconcile_to_invoice_totals(engine):
    # Reconciliation: each country's revenue equals the sum of its invoice
    # totals (a different table), the rows add to the grand total, the
    # shares add to 100%, and each country appears once.
    countries = country_revenue_share(engine)
    finance_total = float(scalar(engine, "SELECT SUM(total) FROM invoice"))
    assert round(float(countries["revenue"].sum()), 2) == round(finance_total, 2)
    assert round(float(countries["share_pct"].sum()), 1) == 100.0
    assert countries["country"].is_unique
    for country in ("USA", "Canada", "Germany"):
        invoice_side = float(
            scalar(
                engine,
                "SELECT SUM(total) FROM invoice WHERE billing_country = :c",
                {"c": country},
            )
        )
        row = countries[countries["country"] == country]["revenue"].iloc[0]
        assert round(float(row), 2) == round(invoice_side, 2)
