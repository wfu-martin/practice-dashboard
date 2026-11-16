"""Issue #9: genre-and-country combinations (AC-4)."""

from conftest import scalar
from dashboard.metrics import genre_country_revenue


def test_ac4_top3_combinations(engine):
    # Given all years, the three biggest genre-and-country pairs are as the spec lists.
    top3 = genre_country_revenue(engine, limit=3)
    got = [
        (row.country, row.genre, round(float(row.revenue), 2))
        for row in top3.itertuples()
    ]
    assert got == [
        ("USA", "Rock", 155.43),
        ("Canada", "Rock", 105.93),
        ("USA", "Latin", 90.09),
    ]


def test_ac4_combinations_reconcile_to_independent_sql(engine):
    # Reconciliation: each top pair equals an independent query that filters
    # invoices and tracks separately, and the pairs add to the grand total
    # with each pair appearing once.
    combos = genre_country_revenue(engine)
    assert combos["revenue"].is_monotonic_decreasing
    assert not combos.duplicated(["genre", "country"]).any()
    grand_total = float(scalar(engine, "SELECT SUM(unit_price * quantity) FROM invoice_line"))
    assert round(float(combos["revenue"].sum()), 2) == round(grand_total, 2)
    for row in combos.head(3).itertuples():
        independent = float(
            scalar(
                engine,
                """
                SELECT SUM(unit_price * quantity) FROM invoice_line
                WHERE invoice_id IN (SELECT invoice_id FROM invoice WHERE billing_country = :c)
                  AND track_id IN (SELECT t.track_id FROM track t
                                   JOIN genre g ON g.genre_id = t.genre_id
                                   WHERE g.name = :g)
                """,
                {"c": row.country, "g": row.genre},
            )
        )
        assert round(float(row.revenue), 2) == round(independent, 2)


def test_ac4_year_filter_reconciles(engine):
    # The year argument (Screen 1's year picker): 2023 pairs add to that
    # year's grand total of 469.58.
    combos = genre_country_revenue(engine, year=2023)
    assert round(float(combos["revenue"].sum()), 2) == 469.58
