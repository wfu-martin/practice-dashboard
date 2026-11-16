"""The dashboard's four screens. Run it with:  streamlit run streamlit_app.py

Each screen opens with a one-sentence takeaway and a row of headline numbers,
as design.md draws it. Every query lives in dashboard/metrics.py and every
headline and tile is drawn by dashboard/charts.py.

Rule for a public app on a shared login: no box where a viewer can type SQL.
Filters (dropdowns, sliders, dates) pass values to the queries as parameters.
"""

import pandas as pd
import streamlit as st

from dashboard import charts, db, metrics

st.set_page_config(page_title="Music store revenue", layout="wide")


# Each loader is cached for ten minutes: every viewer shares one answer
# instead of each sending the same query to the server.
@st.cache_data(ttl=600)
def load_grand_total():
    return metrics.grand_total(db.get_engine())


@st.cache_data(ttl=600)
def load_finance_gap():
    return metrics.finance_gap(db.get_engine())


@st.cache_data(ttl=600)
def load_finance_check():
    return metrics.finance_check(db.get_engine())


@st.cache_data(ttl=600)
def load_genres():
    return metrics.genre_revenue_share(db.get_engine())


@st.cache_data(ttl=600)
def load_countries():
    return metrics.country_revenue_share(db.get_engine())


@st.cache_data(ttl=600)
def load_combinations():
    return metrics.genre_country_revenue(db.get_engine(), limit=10)


@st.cache_data(ttl=600)
def load_yearly():
    return metrics.yearly_revenue(db.get_engine())


@st.cache_data(ttl=600)
def load_monthly():
    return metrics.monthly_revenue(db.get_engine())


@st.cache_data(ttl=600)
def load_top10_customers():
    return metrics.top10_customers(db.get_engine())


@st.cache_data(ttl=600)
def load_top10_years():
    return metrics.top10_years_active(db.get_engine())


@st.cache_data(ttl=600)
def load_rep_revenue():
    return metrics.rep_revenue(db.get_engine())


@st.cache_data(ttl=600)
def load_rep_customers():
    return metrics.rep_customers(db.get_engine())


def gap_tile() -> dict:
    """The "Gap vs. Finance" tile every screen ends its row with."""
    return {"label": "Gap vs Finance", "value": float(load_finance_gap().loc[0, "gap"]), "kind": "money"}


def finance_section():
    """The collapsed "Check against Finance" section every screen ends with."""
    charts.finance_check(load_finance_check())


def share_bars(takeaway: str, note: str, data, label: str, label_name: str):
    """A headline and horizontal bars of each item's share of revenue, top 5."""
    shares = data.assign(share=data["share_pct"] / 100).rename(columns={label: label_name})
    charts.headline(takeaway, note)
    charts.show(charts.ranked_bar(shares, label_name, "share", kind="percent", top=5))


def where_the_money_comes_from():
    # The sidebar area where the year picker will go (Screen 1 only).
    st.sidebar.subheader("Year")
    st.sidebar.caption("All years")

    genres = load_genres()
    countries = load_countries()
    total = float(load_grand_total().loc[0, "revenue"])
    gap = float(load_finance_gap().loc[0, "gap"])
    top_genre, top_country = genres.iloc[0], countries.iloc[0]

    charts.headline(
        f"{top_genre['genre']} and {top_country['country']} carry the most revenue",
        "Revenue (unit price × quantity), all invoices, all years.",
    )
    charts.kpi_row([
        {"label": "Total revenue", "value": total, "kind": "money", "delta": gap, "versus": "vs Finance"},
        {"label": f"Top genre: {top_genre['genre']}", "value": top_genre["share_pct"] / 100, "kind": "percent"},
        {"label": f"Top country: {top_country['country']}", "value": top_country["share_pct"] / 100, "kind": "percent"},
        gap_tile(),
    ])
    share_bars(
        f"{top_genre['genre']} earns {charts.fmt(top_genre['share_pct'] / 100, 'percent')} of revenue",
        "Revenue by genre, all years, top 5, as a share of all revenue.",
        genres, "genre", "Genre",
    )
    share_bars(
        f"{top_country['country']} earns {charts.fmt(top_country['share_pct'] / 100, 'percent')} of revenue",
        "Revenue by billing country, all years, top 5, as a share of all revenue.",
        countries, "country", "Country",
    )
    combinations = load_combinations().assign(Combination=lambda d: d["country"] + " - " + d["genre"])
    top_combo = combinations.iloc[0]
    charts.headline(
        f"{top_combo['country']} {top_combo['genre']} is the biggest single combination: "
        f"{charts.fmt(top_combo['revenue'], 'money')}",
        "Revenue (unit price × quantity) by billing country and genre, all years, top 10.",
    )
    charts.show(charts.ranked_bar(combinations.astype({"revenue": float}), "Combination", "revenue"))
    finance_section()


def growth():
    yearly = load_yearly()
    last_full, so_far = yearly.iloc[-2], yearly.iloc[-1]

    charts.headline(
        f"Revenue has stayed between {charts.fmt(yearly['revenue'].min(), 'money')} and "
        f"{charts.fmt(yearly['revenue'].max(), 'money')} a year since {int(yearly.iloc[0]['year'])}",
        "Revenue (unit price × quantity) by calendar year, all invoices.",
    )
    charts.kpi_row([
        {"label": f"{int(last_full['year'])} vs {int(last_full['year']) - 1}", "value": last_full["revenue"],
         "kind": "money", "delta": last_full["change_pct"] / 100, "delta_kind": "percent"},
        {"label": f"{int(so_far['year'])} so far vs {int(so_far['year']) - 1}", "value": so_far["revenue"],
         "kind": "money", "delta": so_far["change_pct"] / 100, "delta_kind": "percent"},
        {"label": f"{len(yearly)}-year average", "value": yearly["revenue"].mean(), "kind": "money"},
        gap_tile(),
    ])
    st.caption(f"{int(so_far['year'])} is not a full year: it ends 22 Dec.")

    # Yearly line and table (question 4). Years are text so the axis shows
    # 2021, 2022, ... and never 2021.5.
    changes = yearly["change_pct"].dropna()
    charts.headline(
        f"Yearly revenue moved between {charts.fmt(changes.min() / 100, 'percent')} "
        f"and +{charts.fmt(changes.max() / 100, 'percent')}",
        f"Revenue by calendar year, {int(yearly.iloc[0]['year'])}-{int(so_far['year'])}; "
        f"{int(so_far['year'])} ends 22 Dec.",
    )
    by_year = yearly.assign(year=yearly["year"].astype(str), revenue=yearly["revenue"].astype(float))
    charts.show(charts.trend_line(by_year, "year", "revenue", label_points=True))
    st.dataframe(
        pd.DataFrame({
            "Year": by_year["year"],
            "Revenue": [charts.fmt(r, "money") for r in by_year["revenue"]],
            "Change from prior year": [
                "none" if pd.isna(c) else f"{c:+.1f}%" for c in yearly["change_pct"]
            ],
        }),
        hide_index=True,
        width="stretch",
    )

    # Monthly line (question 5).
    monthly = load_monthly().astype({"revenue": float})
    typical = monthly["revenue"].median()
    charts.headline(
        f"Monthly revenue is usually about {charts.fmt(typical, 'money')}, "
        f"from {charts.fmt(monthly['revenue'].min(), 'money')} to {charts.fmt(monthly['revenue'].max(), 'money')}",
        f"Revenue by calendar month, {pd.Timestamp(monthly['month'].iloc[0]):%b %Y}-"
        f"{pd.Timestamp(monthly['month'].iloc[-1]):%b %Y}.",
    )
    charts.show(charts.trend_line(monthly.assign(month=pd.to_datetime(monthly["month"])), "month", "revenue"))
    finance_section()


def customers():
    top = load_top10_customers()
    years = load_top10_years()
    all_customers = int(load_rep_customers()["customers"].sum())
    share = top["share_pct"].sum() / 100
    even = len(top) / all_customers
    all_five = int((years["years_active"] == 5).sum())

    charts.headline(
        f"The top {len(top)} customers bring in {charts.fmt(share, 'percent')} of revenue",
        "Revenue (unit price × quantity) by customer, all invoices, full period; ties for 10th place included.",
    )
    charts.kpi_row([
        {"label": f"Top-{len(top)} share", "value": share, "kind": "percent", "delta": share - even,
         "versus": f"vs {charts.fmt(even, 'percent')} if even"},
        {"label": f"Top-{len(top)} revenue", "value": top["revenue"].sum(), "kind": "money"},
        {"label": f"Bought all 5 years (of {len(years)})", "value": all_five, "kind": "count"},
        gap_tile(),
    ])

    # Ranked bars of the top customers (question 6).
    bars = top.assign(revenue=top["revenue"].astype(float)).rename(columns={"customer": "Customer"})
    top_revenue = bars["revenue"].sum()
    charts.headline(
        f"Top {len(top)} customers bring in {charts.fmt(top_revenue, 'money')}, "
        f"{charts.fmt(share, 'percent')} of total",
        "Revenue by customer, full period, top 10 (ties included).",
    )
    charts.show(charts.ranked_bar(bars, "Customer", "revenue", top=len(bars)))

    # Years bought, from the top (question 7).
    charts.headline(
        f"{all_five} of the top {len(years)} bought in all 5 years",
        "Years with at least one invoice, top 10 customers.",
    )
    st.dataframe(
        pd.DataFrame({
            "Customer": years["customer"],
            "Years bought (of 5)": years["years_active"].astype(int),
        }),
        hide_index=True,
        width="stretch",
    )
    finance_section()


def sales_reps():
    revenue = load_rep_revenue()
    reps = load_rep_customers()
    per_customer = revenue["revenue"].sum() / reps["customers"].sum()
    best = reps.loc[reps["revenue_per_customer"].idxmax()]
    top_rep = revenue.iloc[0]

    charts.headline(
        f"{top_rep['rep']}'s customers bring in the most: {charts.fmt(top_rep['revenue'], 'money')}",
        "Revenue (unit price × quantity) from each sales rep's customers, all invoices, full period.",
    )
    charts.kpi_row([
        {"label": "Avg per customer", "value": per_customer, "kind": "cents"},
        {"label": f"Top per customer: {best['rep']}", "value": best["revenue_per_customer"], "kind": "cents",
         "delta": best["revenue_per_customer"] - per_customer, "versus": "vs avg"},
        {"label": "Avg customers per rep", "value": reps["customers"].mean(), "kind": "count"},
        gap_tile(),
    ])

    # Ranked bars of revenue by rep (question 8).
    bars = revenue.astype({"revenue": float}).rename(columns={"rep": "Rep"})
    lowest = bars.iloc[-1]
    charts.headline(
        f"{top_rep['rep']}'s customers bring in {charts.fmt(top_rep['revenue'], 'money')}, "
        f"{lowest['Rep']}'s {charts.fmt(lowest['revenue'], 'money')}",
        "Revenue from each rep's customers, full period.",
    )
    charts.show(charts.ranked_bar(bars, "Rep", "revenue", top=len(bars)))

    # Customers and revenue per customer, one row per rep (question 9).
    spread = reps["revenue_per_customer"].max() - reps["revenue_per_customer"].min()
    charts.headline(
        f"Revenue per customer is within {charts.fmt(spread, 'cents')} across reps",
        "Customers and revenue per customer, full period.",
    )
    st.dataframe(
        pd.DataFrame({
            "Rep": reps["rep"],
            "Customers": reps["customers"].astype(int),
            "Revenue per customer": [charts.fmt(v, "cents") for v in reps["revenue_per_customer"]],
        }),
        hide_index=True,
        width="stretch",
    )
    finance_section()


# Navigation runs along the top, so the sidebar exists only where a screen
# puts a filter there (Screen 1's year picker).
pages = st.navigation(
    [
        st.Page(where_the_money_comes_from, title="Where the money comes from", url_path="money", default=True),
        st.Page(growth, title="Growth", url_path="growth"),
        st.Page(customers, title="Customers", url_path="customers"),
        st.Page(sales_reps, title="Sales reps", url_path="reps"),
    ],
    position="top",
)
pages.run()
