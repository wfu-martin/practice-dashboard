# Roadmap

Phases in critical-path order: each one needs the one before it. Every task
is a GitHub Issue small enough to finish in one fresh session, with its
acceptance criteria and the tests that prove it.

| Phase | Goal | Issues |
|---|---|---|
| 1. Data connection | The app reads the team's database, locally and on Community Cloud | |
| 2. Data layer | Every metric in the spec has a tested function in `dashboard/metrics.py` | |
| 3. Views | Each stakeholder question has a screen section that answers it, built as `design.md` draws it | |
| 4. Filters | The interactions the spec lists work, and the numbers still reconcile | |
| 5. Polish and deploy | The app follows every rule in `design.md`; `mockup.py` is gone; the live app link is in the README | |

## Critical path

<Which Issues block which; filled in from the spec.>

---

## Dashboard review

When the dashboard is finished, the Pitch Lead runs the final review. Each fix
becomes a GitHub Issue labeled `phase-1` through `phase-5`, for the phase it
belongs to, and each review adds one line below.

<Filled in by /dashkit:review-dashboard: one line per review, "- YYYY-MM-DD: fixes in #n, #n".>

---

## Task draft

| # | Phase | Task | AC IDs | Tests that prove it | Depends on | Owner | Issue |
|---|---|---|---|---|---|---|---|
| 1 | 1 | App reads the database locally (smoke query through `dashboard/db.py`) | none; task criteria | Tests: none new; suite stays green | none | Tomás Rivera (Data) | #4 |
| 2 | 1 | Hello-world deploy on Community Cloud with the Secrets box filled | none; task criteria | Tests: none new; suite stays green | 1 | Tomás Rivera (Data) | #5 |
| 3 | 2 | Grand total revenue and Finance gap | AC-11 | `test_ac11_grand_total_is_2328_60`, `test_ac11_gap_is_zero` | 1 | Tomás Rivera (Data) | #6 |
| 4 | 2 | Genre revenue and share (optional year) | AC-1, AC-2 | `test_ac1_top5_genres_and_shares`, `test_ac2_2023_total_and_top_genre` | 3 | Avery Chen (Spec) | #7 |
| 5 | 2 | Country revenue and share (optional year) | AC-3 | `test_ac3_top5_countries_and_shares` | 3 | Tomás Rivera (Data) | #8 |
| 6 | 2 | Genre-and-country combinations (optional year) | AC-4 | `test_ac4_top3_combinations` | 3 | Avery Chen (Spec) | #9 |
| 7 | 2 | Yearly revenue and % change from prior year | AC-5 | `test_ac5_yearly_revenue_and_change` | 3 | Tomás Rivera (Data) | #10 |
| 8 | 2 | Monthly revenue, 60 months | AC-6 | `test_ac6_monthly_60_months_jan_2021` | 3 | Avery Chen (Spec) | #11 |
| 9 | 2 | Top-10 customers: revenue and share (ties included) | AC-7 | `test_ac7_top10_revenue_and_share` | 3 | Marcus Bell (Delivery) | #12 |
| 10 | 2 | Years bought for the top 10 customers | AC-8 | `test_ac8_years_active_distribution` | 9 | Avery Chen (Spec) | #13 |
| 11 | 2 | Revenue per sales support rep | AC-9 | `test_ac9_rep_revenue` | 3 | Marcus Bell (Delivery) | #14 |
| 12 | 2 | Customers and revenue per customer, per rep | AC-10 | `test_ac10_rep_customers_and_per_customer` | 11 | Avery Chen (Spec) | #15 |
| 13 | 2 | Group totals by genre, country, year, and rep, each against 2,328.60 | AC-12 | `test_ac12_each_breakdown_sums_to_total` | 4, 5, 7, 11 | Marcus Bell (Delivery) | #16 |
| 14 | 3 | App shell: four screens with navigation, each opening with a takeaway line and tile row | none; task criteria | Tests: none new; suite stays green | 2, 3 | Priya Raman (Design) | #17 |
| 15 | 3 | "Check against Finance" section and gap tile, reused on every screen | AC-11, AC-12 | `test_ac11_finance_gap_tile_shows_zero`, `test_ac12_finance_table_rows_sum_to_total` | 13, 14 | Sofia Nakamura (Pitch) | #18 |
| 16 | 3 | Screen 1: genre and country share bars (all years) | AC-1, AC-3 | `test_ac1_screen1_genre_bars`, `test_ac3_screen1_country_bars` | 4, 5, 15 | Priya Raman (Design) | #19 |
| 17 | 3 | Screen 1: top-10 genre-and-country combinations | AC-4 | `test_ac4_screen1_combination_bars` | 6, 16 | Sofia Nakamura (Pitch) | #20 |
| 18 | 3 | Screen 2 Growth: yearly line with table, and monthly line | AC-5, AC-6 | `test_ac5_screen2_yearly_table`, `test_ac6_screen2_monthly_line` | 7, 8, 15 | Priya Raman (Design) | #21 |
| 19 | 3 | Screen 3 Customers: top-10 bars and years-bought table | AC-7, AC-8 | `test_ac7_screen3_top10_share`, `test_ac8_screen3_years_table` | 9, 10, 15 | Sofia Nakamura (Pitch) | #22 |
| 20 | 3 | Screen 4 Sales reps: revenue bars and customers table | AC-9, AC-10 | `test_ac9_screen4_rep_bars`, `test_ac10_screen4_rep_table` | 11, 12, 15 | Priya Raman (Design) | #23 |
| 21 | 4 | Year picker on Screen 1 (default all years; a year with no rows shows a note) | AC-2 | `test_ac2_screen1_year_2023_total_and_top_genre` | 16, 17 | Sofia Nakamura (Pitch) | #24 |
| 22 | 4 | Screens 2-4 ignore the year picker | AC-13 | `test_ac13_other_screens_show_full_period` | 18, 19, 20, 21 | Marcus Bell (Delivery) | #25 |
| 23 | 5 | Style audit against every rule in `design.md` (headlines, captions, number formats, color) | none; task criteria | Tests: none new; suite stays green | 22 | Marcus Bell (Delivery) | #26 |
| 24 | 5 | Delete `mockup.py`, put the live link in the README, final deploy | none; task criteria | Tests: none new; suite stays green | 23 | Priya Raman (Design) | #27 |
