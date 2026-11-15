"""Clickable mockup of the four screens, with made-up numbers.

Run it with:  streamlit run mockup.py
It never connects to the database. Figures from spec.md's acceptance criteria
are used where the spec gives them; everything else is invented but plausible.
Every headline, tile, and chart goes through dashboard/charts.py.
"""

import numpy as np
import pandas as pd
import streamlit as st

from dashboard import charts

st.set_page_config(page_title="Vinyl Vault (mockup)", layout="wide")

TOTAL = 2328.60
YEAR_TOTALS = {2021: 449.46, 2022: 481.45, 2023: 469.58, 2024: 477.53, 2025: 450.58}
AVG_YEAR = TOTAL / 5

GENRES = pd.DataFrame({
    "genre": ["Rock", "Latin", "Metal", "Alternative & Punk", "TV Shows"],
    "revenue": [826.65, 382.14, 261.36, 241.56, 93.53],
})
COUNTRIES = pd.DataFrame({
    "country": ["USA", "Canada", "France", "Brazil", "Germany"],
    "revenue": [523.06, 303.96, 195.10, 190.10, 156.48],
})
COMBOS = pd.DataFrame({
    "combo": ["USA - Rock", "Canada - Rock", "USA - Latin", "USA - Metal", "France - Rock",
              "Brazil - Rock", "Germany - Rock", "Canada - Latin", "USA - Alternative & Punk",
              "Canada - Metal"],
    "revenue": [155.43, 105.93, 90.09, 61.20, 52.80, 50.47, 44.10, 41.33, 38.90, 36.25],
})
CUSTOMERS = pd.DataFrame({
    "customer": ["Helena Novak", "Luis Prado", "Mark Dupont", "Aiko Tanaka", "Sara Lindqvist",
                 "Omar Haddad", "Priya Raman", "John Whitfield", "Eva Kowalski", "Tom Becker"],
    "revenue": [55.40, 52.30, 50.80, 49.60, 47.90, 45.30, 42.70, 41.40, 33.00, 32.80],
    "years": [5, 5, 4, 4, 4, 4, 4, 3, 3, 3],
})
REPS = pd.DataFrame({
    "rep": ["Jane", "Margaret", "Steve"],
    "revenue": [833.04, 775.40, 720.16],
    "customers": [21, 20, 18],
})
REPS["per_customer"] = [39.67, 38.77, 40.01]


def monthly() -> pd.DataFrame:
    rng = np.random.default_rng(7)
    rows = []
    for year, total in YEAR_TOTALS.items():
        weights = rng.uniform(0.85, 1.15, 12)
        values = total * weights / weights.sum()
        rows += [(pd.Timestamp(year, m + 1, 1), v) for m, v in enumerate(values)]
    df = pd.DataFrame(rows, columns=["month", "revenue"])
    df.loc[0, "revenue"] = 35.64
    return df


def money(value: float) -> str:
    return f"${value:,.2f}"


def check_against_finance(total: float, breakdowns: list[str]) -> None:
    with st.expander("Check against Finance"):
        st.caption("Each breakdown's total against the sum of invoice totals.")
        rows = [{"Breakdown": b, "Total": money(total), "Sum of invoice totals": money(total),
                 "Gap": "0.00"} for b in breakdowns]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


def screen_money() -> None:
    year = st.sidebar.selectbox("Year", ["All years", 2021, 2022, 2023, 2024, 2025])
    total = TOTAL if year == "All years" else YEAR_TOTALS[year]
    scale = total / TOTAL
    period = "2021-2025" if year == "All years" else str(year)
    genres = GENRES.assign(revenue=GENRES["revenue"] * scale)
    countries = COUNTRIES.assign(revenue=COUNTRIES["revenue"] * scale)
    combos = COMBOS.assign(revenue=COMBOS["revenue"] * scale)

    top_genre, top_country = genres.iloc[0], countries.iloc[0]
    genre_share = top_genre["revenue"] / total
    country_share = top_country["revenue"] / total
    st.title("Where the money comes from")
    st.markdown(f"**{top_genre['genre']} earns {charts.fmt(genre_share, 'percent')} of revenue "
                f"and {top_country['country']} {charts.fmt(country_share, 'percent')}.**")
    charts.kpi_row([
        {"label": "Total revenue", "value": total, "kind": "money",
         **({} if year == "All years" else {"delta": total - AVG_YEAR, "versus": "vs yearly average"})},
        {"label": f"{top_genre['genre']} share of revenue", "value": genre_share, "kind": "percent"},
        {"label": f"{top_country['country']} share of revenue", "value": country_share,
         "kind": "percent"},
        {"label": "Gap vs. Finance", "value": 0.0, "kind": "money"},
    ])

    charts.headline(f"{top_genre['genre']} earns {charts.fmt(genre_share, 'percent')} of revenue",
                    f"Share of total revenue by genre, top 5, {period}.")
    charts.show(charts.ranked_bar(genres.assign(share=genres["revenue"] / total),
                                  "genre", "share", kind="percent", top=5))

    charts.headline(f"{top_country['country']} earns {charts.fmt(country_share, 'percent')} of revenue",
                    f"Share of total revenue by billing country, top 5, {period}.")
    charts.show(charts.ranked_bar(countries.assign(share=countries["revenue"] / total),
                                  "country", "share", kind="percent", top=5))

    best = combos.iloc[0]
    charts.headline(f"{best['combo']} is the biggest single combination at "
                    f"{charts.fmt(best['revenue'], 'money')}",
                    f"Revenue by billing country and genre, top 10, {period}.")
    charts.show(charts.ranked_bar(combos, "combo", "revenue", top=10))

    check_against_finance(total, ["By genre", "By country", "By year", "By rep",
                                  "Sum of invoice lines"])


def screen_growth() -> None:
    st.title("Growth")
    years = pd.DataFrame({"year": [str(y) for y in YEAR_TOTALS], "revenue": list(YEAR_TOTALS.values())})
    years["change"] = years["revenue"].pct_change()
    low, high = years["change"].min(), years["change"].max()
    st.markdown(f"**Revenue is flat: about {charts.fmt(years['revenue'].min(), 'money')} to "
                f"{charts.fmt(years['revenue'].max(), 'money')} a year since 2021.**")
    charts.kpi_row([
        {"label": "2024 revenue", "value": YEAR_TOTALS[2024], "kind": "money",
         "delta": YEAR_TOTALS[2024] - YEAR_TOTALS[2023], "versus": "vs 2023"},
        {"label": "2025 so far (to 22 Dec)", "value": YEAR_TOTALS[2025], "kind": "money",
         "delta": YEAR_TOTALS[2025] - YEAR_TOTALS[2024], "versus": "vs 2024"},
        {"label": "Average year", "value": AVG_YEAR, "kind": "money"},
        {"label": "Gap vs. Finance", "value": 0.0, "kind": "money"},
    ])

    charts.headline(f"Yearly revenue moved between {charts.fmt(low, 'percent')} and "
                    f"+{charts.fmt(high, 'percent')}",
                    "Revenue by calendar year, 2021-2025. 2025 ends 22 December.")
    charts.show(charts.trend_line(years, "year", "revenue"))
    table = pd.DataFrame({
        "Year": years["year"],
        "Revenue": [charts.fmt(v, "money") for v in years["revenue"]],
        "Change from prior year": ["none" if pd.isna(c) else f"{c:+.1%}" for c in years["change"]],
    })
    st.dataframe(table, hide_index=True, width="stretch")

    months = monthly()
    charts.headline(f"Monthly revenue ranges from {charts.fmt(months['revenue'].min(), 'money')} to "
                    f"{charts.fmt(months['revenue'].max(), 'money')}",
                    "Revenue by calendar month, January 2021 to December 2025.")
    charts.show(charts.trend_line(months, "month", "revenue"))

    check_against_finance(TOTAL, ["By genre", "By country", "By year", "By rep",
                                  "Sum of invoice lines"])


def screen_customers() -> None:
    st.title("Customers")
    top_total = CUSTOMERS["revenue"].sum()
    share = top_total / TOTAL
    all_five = int((CUSTOMERS["years"] == 5).sum())
    st.markdown(f"**The top 10 customers bring in {charts.fmt(share, 'percent')} of revenue.**")
    charts.kpi_row([
        {"label": "Top-10 share of revenue", "value": share, "kind": "percent",
         "delta": share - 0.10, "versus": "vs an even split (10.0%)"},
        {"label": "Top-10 revenue", "value": top_total, "kind": "money"},
        {"label": "Bought in all 5 years", "value": all_five, "kind": "count"},
        {"label": "Gap vs. Finance", "value": 0.0, "kind": "money"},
    ])

    charts.headline(f"The top 10 customers bring in {charts.fmt(top_total, 'money')}, "
                    f"{charts.fmt(share, 'percent')} of revenue",
                    "Revenue by customer, 2021-2025, top 10 (customers tied for 10th included).")
    charts.show(charts.ranked_bar(CUSTOMERS, "customer", "revenue", top=10))

    charts.headline(f"Only {all_five} of the top 10 bought in all 5 years",
                    "Calendar years with at least one invoice, top 10 customers, 2021-2025.")
    table = CUSTOMERS[["customer", "years"]].rename(
        columns={"customer": "Customer", "years": "Years bought (of 5)"})
    st.dataframe(table, hide_index=True, width="stretch")

    check_against_finance(TOTAL, ["By genre", "By country", "By year", "By rep",
                                  "Sum of invoice lines"])


def screen_reps() -> None:
    st.title("Sales reps")
    top = REPS.iloc[0]
    low = REPS.iloc[-1]
    best = REPS.loc[REPS["per_customer"].idxmax()]
    spread = REPS["per_customer"].max() - REPS["per_customer"].min()
    st.markdown(f"**{top['rep']}'s customers bring in the most: {charts.fmt(top['revenue'], 'money')}.**")
    charts.kpi_row([
        {"label": "Revenue from rep customers", "value": REPS["revenue"].sum(), "kind": "money"},
        {"label": f"Best revenue per customer ({best['rep']})", "value": best["per_customer"],
         "kind": "money"},
        {"label": "Average customers per rep", "value": REPS["customers"].mean(), "kind": "count"},
        {"label": "Gap vs. Finance", "value": 0.0, "kind": "money"},
    ])

    charts.headline(f"{top['rep']}'s customers bring in {charts.fmt(top['revenue'], 'money')}, "
                    f"{low['rep']}'s {charts.fmt(low['revenue'], 'money')}",
                    "Revenue from each sales support rep's customers, 2021-2025.")
    charts.show(charts.ranked_bar(REPS, "rep", "revenue", top=3))

    charts.headline(f"Revenue per customer differs by only {charts.fmt(spread, 'money')} across reps",
                    "Customers and revenue per customer for each sales support rep, 2021-2025.")
    table = pd.DataFrame({
        "Rep": REPS["rep"],
        "Customers": REPS["customers"],
        "Revenue per customer": [charts.fmt(v, "money") for v in REPS["per_customer"]],
    })
    st.dataframe(table, hide_index=True, width="stretch")

    check_against_finance(TOTAL, ["By genre", "By country", "By year", "By rep",
                                  "Sum of invoice lines"])


SCREENS = {
    "1. Where the money comes from": screen_money,
    "2. Growth": screen_growth,
    "3. Customers": screen_customers,
    "4. Sales reps": screen_reps,
}

# The first element on every screen.
st.warning("Mockup: made-up numbers")
choice = st.sidebar.radio("Screen", list(SCREENS))
SCREENS[choice]()
