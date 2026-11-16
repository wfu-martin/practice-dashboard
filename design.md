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
| 1. Where the money comes from | 1 | Top 5 genres and share | Horizontal bars of percentages | Shares of a whole, 5 parts | Total revenue (vs. yearly average for one year; vs. Finance for all years), top genre share, top country share, gap vs. Finance |
| 1 | 2 | Top 5 countries and share | Horizontal bars of percentages | Shares of a whole, 5 parts | (same row) |
| 1 | 3 | Top genre-and-country combinations | Ranked horizontal bars, top 10 | Items ranked by size | (same row) |
| 2. Growth | 4 | Yearly revenue and % change | Line of 5 years, plus a small table of values and % change | Change over time; exact values looked up | Last full year (2024) vs. 2023, 2025 so far vs. 2024, 5-year average |
| 2 | 5 | Monthly revenue | Line of 60 months | Change over time | (same row) |
| 3. Customers | 6 | Top-10 customer share | Ranked horizontal bars of the 10 customers, share in the headline | Items ranked by size | Top-10 share vs. an even split, top-10 revenue, customers who bought in all 5 years |
| 3 | 7 | Years bought, top 10 customers | Table (customer, years bought of 5) | Exact values looked up | (same row) |
| 4. Sales reps | 8 | Revenue per rep | Ranked horizontal bars | Items ranked by size | Average revenue per customer, top revenue per customer (vs. the average), average customers per rep |
| 4 | 9 | Customers and revenue per customer | Table (rep, customers, revenue per customer) | Exact values looked up | (same row) |
| All | 10 | Does it tie to Finance | Collapsed table of group totals against 2,328.60 | Exact values looked up | Gap vs. Finance on every screen |

### Drawings

Numbers in the drawings come from the acceptance criteria in `spec.md`; the
real headlines are computed from the data. Every screen's caption names the
metric, the period and the filters.

**Screen 1. Where the money comes from** (questions 1, 2, 3, 10)

```
 SIDEBAR            Rock and the USA carry the most revenue
 Year: [All years]  ----------------------------------------------------
                    [Total revenue] [Top genre share] [Top country] [Gap vs Finance]
                    [$2,329       ] [35.5%          ] [USA 22.5%  ] [$0.00          ]
                    [+$0 vs Finance ] [Rock           ] [           ] [ties out       ]

                    Rock earns 35.5% of revenue                  <- Q1, bars of %
                    Revenue by genre, all years, top 5
                    Rock             ████████████████  35.5%
                    Latin            ███████▌          16.4%
                    Metal            █████▏            11.2%
                    Alternative&Punk ████▊             10.4%
                    TV Shows         █▉                 4.0%

                    The USA earns 22.5% of revenue               <- Q2, bars of %
                    Revenue by billing country, all years, top 5
                    USA ██████████  22.5%   Canada ██████ 13.1%
                    France ████ 8.4%  Brazil ████ 8.2%  Germany ███ 6.7%

                    USA Rock is the biggest single combination  <- Q3, ranked bars
                    Revenue by country and genre, top 10
                    USA - Rock       ████████████  $155
                    Canada - Rock    ████████      $106
                    USA - Latin      ███████        $90
                    ... (10 rows)

                    > Check against Finance (collapsed)          <- Q10
```

**Screen 2. Growth** (questions 4, 5, 10)

```
 SIDEBAR            Revenue is flat: about $450-$480 a year since 2021
 (no filters)       ----------------------------------------------------
                    [2024 vs 2023   ] [2025 so far vs 2024] [5-year average] [Gap vs Finance]
                    [$478  +1.7%    ] [$451  -5.6%*       ] [$466          ] [$0.00         ]
                                      *2025 ends 22 Dec

                    Yearly revenue moved between -5.6% and +7.1%   <- Q4
                    Revenue by calendar year, 2021-2025
                    [line, 5 points, labeled with $ values]
                    Year | Revenue | Change from prior year
                    2021 | $449    | none
                    2022 | $481    | +7.1%    ... (5 rows)

                    Monthly revenue swings around $35-$40           <- Q5
                    Revenue by calendar month, Jan 2021-Dec 2025
                    [line, 60 points]

                    > Check against Finance (collapsed)             <- Q10
```

**Screen 3. Customers** (questions 6, 7, 10)

```
 SIDEBAR            The top 10 customers bring in 19.4% of revenue
 (no filters)       ----------------------------------------------------
                    [Top-10 share    ] [Top-10 revenue] [Bought all 5 years] [Gap vs Finance]
                    [19.4%           ] [$451          ] [2 of 10           ] [$0.00         ]
                    [vs 16.9% if even]

                    Top 10 customers bring in $451, 19.4% of total  <- Q6, ranked bars
                    Revenue by customer, full period, top 10 (ties included)
                    Customer A  ████████  $__
                    ...

                    2 of the top 10 bought in all 5 years         <- Q7, table
                    Years with at least one invoice, top 10 customers
                    Customer | Years bought (of 5)
                    ...

                    > Check against Finance (collapsed)              <- Q10
```

The even-split figure is 10 divided by the customer count (10 of 59 = 16.9%).

**Screen 4. Sales reps** (questions 8, 9, 10)

```
 SIDEBAR            Jane's customers bring in the most: $833
 (no filters)       ----------------------------------------------------
                    [Avg per customer ] [Top per customer ] [Avg customers/rep] [Gap vs Finance]
                    [$39.47           ] [Steve $40.01     ] [20               ] [$0.00         ]
                                        [+$0.54 vs avg  ]

                    Jane's customers bring in $833, Steve's $720    <- Q8, ranked bars
                    Revenue from each rep's customers, full period
                    Jane     ████████████  $833
                    Margaret ███████████   $775
                    Steve    ██████████    $720

                    Revenue per customer is within $1.24 across reps <- Q9, table
                    Customers and revenue per customer, full period
                    Rep      | Customers | Revenue per customer
                    Jane     | 21        | $39.67   ... (3 rows)

                    > Check against Finance (collapsed)              <- Q10
```

**Check against Finance** (the collapsed section on every screen, question 10):
a table with one row per breakdown (by genre, by country, by year, by rep,
sum of invoice totals), each total beside $2,328.60 and a gap column that
reads 0.00.

**Back to top** (the floating button on every screen): a small button fixed in
the bottom-right corner, labeled "Back to top", in the accent color. One click
returns the page to the top. It stays clear of every tile and the year picker,
and of the end of the page; while the viewer scrolls it may briefly pass over
the edge of a full-width chart on a phone-width screen.

---

## Style rules

### Page

- Each screen opens with one sentence stating the main takeaway, then a row
  of three or four headline numbers (`charts.kpi_row`), each shown against a
  comparison: last year, a target, or the average.
- Then one section per framed question, in the order the stakeholder's
  decision needs them.
- Filters sit in the sidebar and apply to the whole screen. The year picker
  on Screen 1 defaults to All years, as `spec.md` says.

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
- Averages per customer keep cents ($39.67) whatever their size, so close
  values can be told apart (`kind="cents"`).
- Bars start at zero.
- Line axes start at zero.
- On a short line every point is labeled; otherwise the latest value is
  labeled.

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
