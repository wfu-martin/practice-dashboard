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
    return read_sql(
        engine,
        """
        SELECT CAST(DATE_TRUNC('month', i.invoice_date) AS date) AS month,
               SUM(il.unit_price * il.quantity) AS revenue
        FROM invoice_line AS il
        JOIN invoice AS i ON i.invoice_id = il.invoice_id
        GROUP BY 1
        ORDER BY 1
        """,
    )


def top10_customers(engine: sqlalchemy.Engine) -> pd.DataFrame:
    """The top 10 customers by revenue, ties for 10th place included.

    Revenue = unit price x quantity over every invoice line, added up per
    customer over the full period. Customers tied for 10th place are all
    included, so the list can show 11. share_pct is the customer's revenue as
    a percentage of total revenue from all customers (0 to 100), so the column
    adds up to the top-10 share.
    Granularity: one row per customer, largest first, columns `customer_id`,
    `customer` (first and last name), `revenue`, `share_pct`.
    """
    return read_sql(
        engine,
        """
        WITH customer_revenue AS (
            SELECT c.customer_id,
                   c.first_name || ' ' || c.last_name AS customer,
                   SUM(il.unit_price * il.quantity) AS revenue
            FROM invoice_line AS il
            JOIN invoice AS i ON i.invoice_id = il.invoice_id
            JOIN customer AS c ON c.customer_id = i.customer_id
            GROUP BY c.customer_id, c.first_name, c.last_name
        ),
        ranked AS (
            SELECT customer_id,
                   customer,
                   revenue,
                   100 * revenue / SUM(revenue) OVER () AS share_pct,
                   RANK() OVER (ORDER BY revenue DESC) AS revenue_rank
            FROM customer_revenue
        )
        SELECT customer_id, customer, revenue, share_pct
        FROM ranked
        WHERE revenue_rank <= 10
        ORDER BY revenue DESC, customer
        """,
    )


def top10_years_active(engine: sqlalchemy.Engine) -> pd.DataFrame:
    """Years bought for each of the top 10 customers (same set as top10_customers).

    Years active = count of distinct calendar years with at least one invoice.
    The customers are the top 10 by revenue over the full period, ties for 10th
    place included, so the list can show 11.
    Granularity: one row per customer, largest revenue first, columns
    `customer_id`, `customer` (first and last name), `years_active` (1 to 5).
    """
    return read_sql(
        engine,
        """
        WITH customer_revenue AS (
            SELECT i.customer_id,
                   SUM(il.unit_price * il.quantity) AS revenue
            FROM invoice_line AS il
            JOIN invoice AS i ON i.invoice_id = il.invoice_id
            GROUP BY i.customer_id
        ),
        ranked AS (
            SELECT customer_id,
                   revenue,
                   RANK() OVER (ORDER BY revenue DESC) AS revenue_rank
            FROM customer_revenue
        ),
        years AS (
            SELECT customer_id,
                   COUNT(DISTINCT EXTRACT(YEAR FROM invoice_date)) AS years_active
            FROM invoice
            GROUP BY customer_id
        )
        SELECT c.customer_id,
               c.first_name || ' ' || c.last_name AS customer,
               y.years_active
        FROM ranked AS t
        JOIN years AS y ON y.customer_id = t.customer_id
        JOIN customer AS c ON c.customer_id = t.customer_id
        WHERE t.revenue_rank <= 10
        ORDER BY t.revenue DESC, customer
        """,
    )


def rep_revenue(engine: sqlalchemy.Engine) -> pd.DataFrame:
    """Revenue from each sales support rep's customers, full period.

    Rep revenue = revenue (unit_price x quantity, summed) from customers whose
    support_rep_id is the rep, for employees titled Sales Support Agent.
    Granularity: one row per rep, largest revenue first, columns `employee_id`,
    `rep` (first name), `revenue`.
    """
    return read_sql(
        engine,
        """
        SELECT e.employee_id,
               e.first_name AS rep,
               SUM(il.unit_price * il.quantity) AS revenue
        FROM invoice_line AS il
        JOIN invoice AS i ON i.invoice_id = il.invoice_id
        JOIN customer AS c ON c.customer_id = i.customer_id
        JOIN employee AS e ON e.employee_id = c.support_rep_id
        WHERE e.title = 'Sales Support Agent'
        GROUP BY e.employee_id, e.first_name
        ORDER BY revenue DESC, rep
        """,
    )


def rep_customers(engine: sqlalchemy.Engine) -> pd.DataFrame:
    """Customers and revenue per customer for each sales support rep, full period.

    Rep customers = count of customers whose support_rep_id is the rep.
    Revenue per customer = Rep revenue / Rep customers, for employees titled
    Sales Support Agent.
    Granularity: one row per rep, most customers first, columns `employee_id`,
    `rep` (first name), `customers`, `revenue_per_customer`.
    """
    return read_sql(
        engine,
        """
        WITH customer_revenue AS (
            SELECT i.customer_id,
                   SUM(il.unit_price * il.quantity) AS revenue
            FROM invoice_line AS il
            JOIN invoice AS i ON i.invoice_id = il.invoice_id
            GROUP BY i.customer_id
        )
        SELECT e.employee_id,
               e.first_name AS rep,
               COUNT(c.customer_id) AS customers,
               COALESCE(SUM(cr.revenue), 0) / COUNT(c.customer_id)
                   AS revenue_per_customer
        FROM employee AS e
        JOIN customer AS c ON c.support_rep_id = e.employee_id
        LEFT JOIN customer_revenue AS cr ON cr.customer_id = c.customer_id
        WHERE e.title = 'Sales Support Agent'
        GROUP BY e.employee_id, e.first_name
        ORDER BY customers DESC, rep
        """,
    )


def breakdown_totals(engine: sqlalchemy.Engine) -> pd.DataFrame:
    """What each breakdown of revenue adds up to, to tie back to Finance.

    Adds up the rows of the genre, country, year, and rep revenue figures
    (genre_revenue_share, country_revenue_share, yearly_revenue, rep_revenue),
    all years, so each total can be compared with the 2,328.60 grand total.
    Granularity: one row per breakdown, in the order genre, country, year,
    rep, columns `breakdown`, `groups` (rows in that breakdown), `revenue`
    (their sum).
    """
    breakdowns = {
        "genre": genre_revenue_share(engine),
        "country": country_revenue_share(engine),
        "year": yearly_revenue(engine),
        "rep": rep_revenue(engine),
    }
    return pd.DataFrame(
        {
            "breakdown": list(breakdowns),
            "groups": [len(rows) for rows in breakdowns.values()],
            "revenue": [rows["revenue"].sum() for rows in breakdowns.values()],
        }
    )


def finance_check(engine: sqlalchemy.Engine) -> pd.DataFrame:
    """The "Check against Finance" table: each breakdown against Finance's total.

    Starts from breakdown_totals (genre, country, year, rep) and adds a fifth
    row, `invoices`, for the sum of invoice totals itself (one group per
    invoice). Every row is set beside Finance's total, the sum of invoice
    totals (2,328.60), all years.
    Granularity: one row per breakdown, in the order genre, country, year,
    rep, invoices; columns `breakdown`, `groups`, `revenue` (the breakdown's
    sum), `finance_total` (sum of invoice totals), `gap` (finance_total minus
    revenue, rounded to cents).
    """
    raise NotImplementedError("Issue #18")
