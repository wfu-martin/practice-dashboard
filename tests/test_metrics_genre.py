"""Issue #7: genre revenue and share, all years or one year (AC-1, AC-2)."""

from conftest import scalar
from dashboard.metrics import genre_revenue_share


def test_ac1_top5_genres_and_shares(engine):
    # Given all years, the top five genres and their shares are as the spec lists.
    top5 = genre_revenue_share(engine).head(5)
    got = [
        (row.genre, round(float(row.revenue), 2), round(float(row.share_pct), 1))
        for row in top5.itertuples()
    ]
    assert got == [
        ("Rock", 826.65, 35.5),
        ("Latin", 382.14, 16.4),
        ("Metal", 261.36, 11.2),
        ("Alternative & Punk", 241.56, 10.4),
        ("TV Shows", 93.53, 4.0),
    ]


def test_ac1_genres_reconcile_to_invoice_totals(engine):
    # Reconciliation: every genre row adds back to the invoice totals (a
    # different table), the shares add to 100%, and each genre appears once.
    genres = genre_revenue_share(engine)
    finance_total = float(scalar(engine, "SELECT SUM(total) FROM invoice"))
    assert round(float(genres["revenue"].sum()), 2) == round(finance_total, 2)
    assert round(float(genres["share_pct"].sum()), 1) == 100.0
    assert genres["genre"].is_unique
    rock_alone = float(
        scalar(
            engine,
            """
            SELECT SUM(il.unit_price * il.quantity)
            FROM invoice_line AS il
            WHERE il.track_id IN (
                SELECT t.track_id FROM track AS t
                WHERE t.genre_id = (SELECT genre_id FROM genre WHERE name = 'Rock')
            )
            """,
        )
    )
    rock_row = genres[genres["genre"] == "Rock"]["revenue"].iloc[0]
    assert round(float(rock_row), 2) == round(rock_alone, 2)


def test_ac2_2023_total_and_top_genre(engine):
    # Given 2023, the grand total is 469.58 and the top genre is Rock at 156.42.
    genres = genre_revenue_share(engine, year=2023)
    total_2023 = float(
        scalar(
            engine,
            "SELECT SUM(total) FROM invoice WHERE EXTRACT(YEAR FROM invoice_date) = 2023",
        )
    )
    assert round(float(genres["revenue"].sum()), 2) == 469.58
    assert round(total_2023, 2) == 469.58
    assert genres.iloc[0]["genre"] == "Rock"
    assert round(float(genres.iloc[0]["revenue"]), 2) == 156.42
