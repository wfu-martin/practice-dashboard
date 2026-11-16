"""The data layer: one function for each figure the dashboard shows.

Each function takes the database engine and returns a small DataFrame. The
heavy work (joining, filtering, adding up) happens in SQL on the server, so
only the finished numbers travel to the app. Queries on the course server
stop after 30 seconds; aggregating in SQL keeps them well under that.

The screens in streamlit_app.py call these functions; the tests in tests/
call the same functions and check their answers against the database.

revenue_by_genre is the template's worked example on vinyl_vault. Replace it
with the figures your spec defines.
"""

import pandas as pd
import sqlalchemy
from sqlalchemy import text


def read_sql(engine: sqlalchemy.Engine, sql: str, params: dict | None = None) -> pd.DataFrame:
    """Run one read-only query and hand back the rows.

    Values from filters go in `params` (written `:name` in the SQL), never
    pasted into the SQL text.
    """
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)


def about(engine: sqlalchemy.Engine) -> pd.DataFrame:
    """What this database is, in one row. Every course database has it."""
    return read_sql(engine, "SELECT display_name, description, granularity FROM meta.about")


def revenue_by_genre(engine: sqlalchemy.Engine) -> pd.DataFrame:
    """Revenue for each music genre, largest first.

    Revenue = unit price x quantity, added up over every invoice line.
    Granularity: one row per genre.
    """
    return genre_revenue_share(engine)[["genre", "revenue"]]


# Revenue as the spec defines it: unit price x quantity over every invoice line.
_LINE_REVENUE_SQL = "SELECT SUM(unit_price * quantity) AS revenue FROM invoice_line"


def grand_total(engine: sqlalchemy.Engine) -> pd.DataFrame:
    """Total revenue across all years, the one number that ties to Finance.

    Revenue = unit price x quantity, added up over every invoice line.
    Granularity: one row, column `revenue`.
    """
    return read_sql(engine, _LINE_REVENUE_SQL)


def finance_gap(engine: sqlalchemy.Engine) -> pd.DataFrame:
    """How far Finance's sum of invoice totals is from line-item revenue.

    gap = finance_total (sum of invoice totals) - revenue (invoice lines).
    Granularity: one row, columns `revenue`, `finance_total`, `gap`.
    """
    return read_sql(
        engine,
        f"""
        SELECT lines.revenue,
               invoices.finance_total,
               ROUND(invoices.finance_total - lines.revenue, 2) AS gap
        FROM ({_LINE_REVENUE_SQL}) AS lines,
             (SELECT SUM(total) AS finance_total FROM invoice) AS invoices
        """,
    )


def genre_revenue_share(engine: sqlalchemy.Engine, year: int | None = None) -> pd.DataFrame:
    """Revenue and share of total for each music genre, largest first.

    Revenue = unit price x quantity over every invoice line. Share is the
    genre's revenue as a percentage of all genre revenue in view (0 to 100).
    `year` limits the figures to invoices dated in that calendar year; None
    means all years.
    Granularity: one row per genre, columns `genre`, `revenue`, `share_pct`.
    """
    return read_sql(
        engine,
        """
        SELECT g.name AS genre,
               SUM(il.unit_price * il.quantity) AS revenue,
               100 * SUM(il.unit_price * il.quantity)
                   / SUM(SUM(il.unit_price * il.quantity)) OVER () AS share_pct
        FROM invoice_line AS il
        JOIN invoice AS i ON i.invoice_id = il.invoice_id
        JOIN track AS t ON t.track_id = il.track_id
        JOIN genre AS g ON g.genre_id = t.genre_id
        WHERE CAST(:year AS integer) IS NULL
           OR EXTRACT(YEAR FROM i.invoice_date) = CAST(:year AS integer)
        GROUP BY g.name
        ORDER BY revenue DESC
        """,
        {"year": year},
    )


def country_revenue_share(engine: sqlalchemy.Engine, year: int | None = None) -> pd.DataFrame:
    """Revenue and share of total for each billing country, largest first.

    Revenue = unit price x quantity over every invoice line. Country is the
    invoice's billing country. Share is the country's revenue as a percentage
    of all country revenue in view (0 to 100). `year` limits the figures to
    invoices dated in that calendar year; None means all years.
    Granularity: one row per country, columns `country`, `revenue`, `share_pct`.
    """
    return read_sql(
        engine,
        """
        SELECT i.billing_country AS country,
               SUM(il.unit_price * il.quantity) AS revenue,
               100 * SUM(il.unit_price * il.quantity)
                   / SUM(SUM(il.unit_price * il.quantity)) OVER () AS share_pct
        FROM invoice_line AS il
        JOIN invoice AS i ON i.invoice_id = il.invoice_id
        WHERE CAST(:year AS integer) IS NULL
           OR EXTRACT(YEAR FROM i.invoice_date) = CAST(:year AS integer)
        GROUP BY i.billing_country
        ORDER BY revenue DESC
        """,
        {"year": year},
    )


def genre_country_revenue(
    engine: sqlalchemy.Engine, year: int | None = None, limit: int | None = None
) -> pd.DataFrame:
    """Revenue for each genre-and-country pair, largest first.

    Revenue = unit price x quantity over every invoice line. Country is the
    invoice's billing country. `year` limits the figures to invoices dated in
    that calendar year; None means all years. `limit` keeps only the top rows;
    None means every pair.
    Granularity: one row per genre and country, columns `genre`, `country`,
    `revenue`.
    """
    return read_sql(
        engine,
        """
        SELECT g.name AS genre,
               i.billing_country AS country,
               SUM(il.unit_price * il.quantity) AS revenue
        FROM invoice_line AS il
        JOIN invoice AS i ON i.invoice_id = il.invoice_id
        JOIN track AS t ON t.track_id = il.track_id
        JOIN genre AS g ON g.genre_id = t.genre_id
        WHERE CAST(:year AS integer) IS NULL
           OR EXTRACT(YEAR FROM i.invoice_date) = CAST(:year AS integer)
        GROUP BY g.name, i.billing_country
        ORDER BY revenue DESC, genre, country
        LIMIT :limit
        """,
        {"year": year, "limit": limit},
    )


def yearly_revenue(engine: sqlalchemy.Engine) -> pd.DataFrame:
    """Revenue for each calendar year with its change from the prior year.

    Revenue = unit price x quantity over every invoice line, grouped by the
    invoice's calendar year. change_pct = (this year - prior year) / prior
    year, as a percentage; the first year has no prior year, so its change is
    empty (null). 2025 ends 22 Dec, so it is a nearly full year.
    Granularity: one row per year, oldest first, columns `year`, `revenue`,
    `change_pct`.
    """
    return read_sql(
        engine,
        """
        WITH yearly AS (
            SELECT CAST(EXTRACT(YEAR FROM i.invoice_date) AS integer) AS year,
                   SUM(il.unit_price * il.quantity) AS revenue
            FROM invoice_line AS il
            JOIN invoice AS i ON i.invoice_id = il.invoice_id
            GROUP BY 1
        )
        SELECT year,
               revenue,
               100 * (revenue - LAG(revenue) OVER (ORDER BY year))
                   / LAG(revenue) OVER (ORDER BY year) AS change_pct
        FROM yearly
        ORDER BY year
        """,
    )


def monthly_revenue(engine: sqlalchemy.Engine) -> pd.DataFrame:
    """Revenue for each calendar month, oldest first.

    Revenue = unit price x quantity over every invoice line, grouped by the
    invoice's calendar month. Always the full period (January 2021 to
    December 2025), whatever year is picked on Screen 1.
    Granularity: one row per month, columns `month` (first day of the month)
    and `revenue`.
    """
    raise NotImplementedError("Issue #11")
