# Design

How the dashboard looks: each screen as drawn, and the style rules every
chart follows. `/dashkit:design` draws the screens from `spec.md` and builds
`mockup.py`; `/dashkit:review-dashboard` checks the finished app against this
file. The rules live in code in `dashboard/charts.py` and
`.streamlit/config.toml`; change a rule here and there together.

---

## Screens

### Chart choices

Every screen also has a "Gap vs. Finance" tile and a collapsed "Check against
Finance" section (question 10): a table of group totals (genre, country, year,
rep, invoices), each against 2,328.60.

| Screen | # | Question | Chart | Why | Tiles |
|---|---|---|---|---|---|
| 1. Where the money comes from | 1 | Top 5 genres and share | Horizontal bars of percentages | Shares of a whole, 5 parts | Total revenue (vs. yearly average), top genre share, top country share, gap vs. Finance |
| 1 | 2 | Top 5 countries and share | Horizontal bars of percentages | Shares of a whole, 5 parts | (same row) |
| 1 | 3 | Top genre-and-country combinations | Ranked horizontal bars, top 10 | Items ranked by size | (same row) |
| 2. Growth | 4 | Yearly revenue and % change | Line of 5 years, plus a small table of values and % change | Change over time; exact values looked up | Last full year (2024) vs. 2023, 2025 so far vs. 2024, 5-year average |
| 2 | 5 | Monthly revenue | Line of 60 months | Change over time | (same row) |
| 3. Customers | 6 | Top-10 customer share | Ranked horizontal bars of the 10 customers, share in the headline | Items ranked by size | Top-10 share vs. an even split, top-10 revenue, customers who bought in all 5 years |
| 3 | 7 | Years bought, top 10 customers | Table (customer, years bought of 5) | Exact values looked up | (same row) |
| 4. Sales reps | 8 | Revenue per rep | Ranked horizontal bars | Items ranked by size | Total rep revenue, best revenue per customer, average customers per rep |
| 4 | 9 | Customers and revenue per customer | Table (rep, customers, revenue per customer) | Exact values looked up | (same row) |
| All | 10 | Does it tie to Finance | Collapsed table of group totals against 2,328.60 | Exact values looked up | Gap vs. Finance on every screen |

### Drawings

<One text wireframe per screen, with the framed question each section
answers and the chart chosen for it. Drawn with `/dashkit:design`.>

---

## Style rules

### Page

- Each screen opens with one sentence stating the main takeaway, then a row
  of three or four headline numbers (`charts.kpi_row`), each shown against a
  comparison: last year, a target, or the average.
- Then one section per framed question, in the order the stakeholder's
  decision needs them.
- Filters sit in the sidebar and apply to the whole screen. Their defaults
  show the most recent complete period.

### Choosing a chart

| The question compares | Chart | Helper |
|---|---|---|
| Items ranked by size | Horizontal bars, largest at the top | `charts.ranked_bar` |
| Change over time | A line | `charts.trend_line` |
| Shares of a whole (up to five parts) | Horizontal bars of percentages, not a pie | `charts.ranked_bar(kind="percent")` |
| Exact values someone will look up | A table | `st.dataframe` |

Anything else (a distribution, two measures against each other): agree on
the chart with the team before building it, and add a row here.

### Words

- Every section's headline states its takeaway with the number, computed
  from the data: "Rock earns 35% of revenue", not "Revenue by genre"
  (`charts.headline`).
- Under the headline, one caption: the metric, its period, and its filters,
  as `spec.md` defines them.
- Labels in plain words, never column names: "Revenue", not
  `total_revenue`. Sentence case.

### Numbers

- Money in whole dollars ($1,234), with cents under $10 ($5.65); counts
  with separators (1,234); percentages to one decimal (12.3%).
- Bars start at zero.

### Color

- One accent color for what the headline is about; neutral gray for
  everything else; red only for a loss or a miss.
- A category keeps the same color on every chart.
- Color never carries a meaning alone: the headline or a label says it too.
- Nothing decorative: no 3-D, no background images, gridlines only where
  reading a value needs them.

### When there is nothing to show

- A filter that leaves no rows shows a short note (`charts.nothing_to_show`)
  in place of an error or an empty chart.
