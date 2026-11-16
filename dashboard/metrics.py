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
    return read_sql(
        engine,
        """
        SELECT g.name AS genre,
               SUM(il.unit_price * il.quantity) AS revenue
        FROM invoice_line AS il
        JOIN track AS t ON t.track_id = il.track_id
        JOIN genre AS g ON g.genre_id = t.genre_id
        GROUP BY g.name
        ORDER BY revenue DESC
        """,
    )


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
    raise NotImplementedError("Issue #7")
