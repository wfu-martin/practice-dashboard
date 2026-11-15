# Vinyl Vault dashboard spec

## Stakeholder and decision

- **Reader:** Morgan Ellis, Director of Sales, Vinyl Vault Music. Opens the dashboard before the annual planning meeting.
- **Main decision:** Where next year's marketing budget goes: which kinds of music (genres) to push and which countries to spend in.
- **Related decision:** Whether to hire another sales support rep or put that money into marketing.

## Framed questions

**Brief question A: Where does our money come from (which music, which countries)?**

1. Which five genres earn the most revenue, and what share of total revenue is each?
2. Which five countries earn the most revenue, and what share of total revenue is each?
3. Which genre-and-country combinations earn the most revenue?

**Brief question B: Are we really growing?**

4. What was total revenue in each year 2021-2025, and what is the percent change from the prior year?
5. What is monthly revenue across the full period (the pattern behind the yearly totals)?

**Brief question C: Does a small group of customers carry the business, and do they keep coming back?**

6. What share of total revenue comes from the top 10 customers?
7. Of the top 10 customers, in how many of the five years did each one buy?

**Brief question D: Are the sales support reps making a difference?**

8. For each sales support rep, what is the total revenue from their customers?
9. For each rep, how many customers do they have, and what is the average revenue per customer?

**Brief question E: Do the numbers tie out with Finance?**

10. Does total revenue by genre, by country, by year, and by rep add up to the same grand total, and does that equal the sum of invoice totals?

## Metric definitions

**Revenue** means one thing everywhere: unit_price × quantity on each invoice line, summed. It equals the sum of invoice totals (2,328.60 across all 412 invoices), so the dashboard ties to Finance. **Country** means the invoice's billing country. The data runs 2021-01-01 to 2025-12-22, so 2025 is a few days short of a full year.

| Metric | Formula | Granularity | Filters | Source |
|---|---|---|---|---|
| Revenue | SUM(unit_price × quantity) | One row per invoice line | None | invoice_line.unit_price, invoice_line.quantity |
| Genre revenue | Revenue grouped by genre name | One row per genre | None | invoice_line → track.genre_id → genre.name |
| Country revenue | Revenue grouped by billing country | One row per country | None | invoice.billing_country, invoice_line |
| Genre-country revenue | Revenue grouped by billing country and genre | One row per country and genre | None | invoice.billing_country, genre.name, invoice_line |
| Revenue share | Group revenue ÷ total revenue | One row per genre or country | None | Derived from the metrics above |
| Yearly revenue | Revenue grouped by calendar year | One row per year | 2025 ends 22 Dec | invoice.invoice_date, invoice_line |
| Year-over-year change | (This year − prior year) ÷ prior year | One row per year | 2021 has no prior year | Derived from Yearly revenue |
| Monthly revenue | Revenue grouped by calendar month | One row per month | None | invoice.invoice_date, invoice_line |
| Customer revenue | Revenue grouped by customer | One row per customer | None | invoice.customer_id, invoice_line |
| Top-10 customer share | Sum of Customer revenue for customers ranked in the top 10 ÷ total revenue | One row | Customers tied for 10th place are all included, so the list can show 11 | Derived from Customer revenue |
| Years active | Count of distinct calendar years with at least one invoice | One row per customer | Top 10 customers, including any tied for 10th | invoice.customer_id, invoice.invoice_date |
| Rep revenue | Revenue from customers whose support_rep_id is the rep | One row per rep | Employees titled Sales Support Agent | customer.support_rep_id, employee.title, invoice_line |
| Rep customers | Count of customers whose support_rep_id is the rep | One row per rep | Employees titled Sales Support Agent | customer.support_rep_id, employee.title |
| Revenue per customer | Rep revenue ÷ Rep customers | One row per rep | Employees titled Sales Support Agent | Derived from the two rep metrics |
| Reconciliation gap | SUM(invoice.total) − Revenue | One row | Must equal 0.00 | invoice.total, invoice_line |

## Data sources

| Table | Columns used |
|---|---|
| invoice | invoice_id, customer_id, invoice_date, billing_country, total |
| invoice_line | invoice_id, track_id, unit_price, quantity |
| track | track_id, genre_id |
| genre | genre_id, name |
| customer | customer_id, support_rep_id |
| employee | employee_id, first_name, title |

## Screens and interactions

Every screen shows the grand total revenue and the date range it covers, so Morgan can quote one number that ties to Finance (question 10). Question 10's totals-by-group check is applied to every screen that breaks revenue into groups.

| Screen | Answers | Filters |
|---|---|---|
| 1. Where the money comes from | Questions 1, 2, 3 | Year picker (default: all years). The grand total, shares and combinations change with the year chosen. |
| 2. Growth | Questions 4, 5 | None. Always the full period. |
| 3. Customers | Questions 6, 7 | None. Always the full period. |
| 4. Sales reps | Questions 8, 9 | None. Always the full period. |

## Acceptance criteria

- **AC-1** (question 1): Given all years are selected, when Screen 1 loads, then the top five genres by revenue are Rock 826.65 (35.5%), Latin 382.14 (16.4%), Metal 261.36 (11.2%), Alternative & Punk 241.56 (10.4%), and TV Shows 93.53 (4.0%).
- **AC-2** (question 1): Given the year 2023 is selected, when Screen 1 loads, then the grand total is 469.58 and the top genre is Rock at 156.42.
- **AC-3** (question 2): Given all years are selected, when Screen 1 loads, then the top five countries by revenue are USA 523.06 (22.5%), Canada 303.96 (13.1%), France 195.10 (8.4%), Brazil 190.10 (8.2%), and Germany 156.48 (6.7%).
- **AC-4** (question 3): Given all years are selected, when Screen 1 loads, then the top three genre-and-country combinations are USA Rock 155.43, Canada Rock 105.93, and USA Latin 90.09.
- **AC-5** (question 4): Given the Growth screen, when it loads, then yearly revenue is 2021: 449.46, 2022: 481.45, 2023: 469.58, 2024: 477.53, 2025: 450.58, with change from the prior year of none, +7.1%, -2.5%, +1.7%, and -5.6%.
- **AC-6** (question 5): Given the Growth screen, when it loads, then monthly revenue shows 60 months from January 2021 to December 2025, and January 2021 is 35.64.
- **AC-7** (question 6): Given the Customers screen, when it loads, then the top 10 customers account for 451.20 of revenue, which is 19.4% of the total.
- **AC-8** (question 7): Given the Customers screen, when it loads, then of the top 10 customers 3 bought in 3 of the 5 years, 5 bought in 4 years, and 2 bought in all 5 years.
- **AC-9** (question 8): Given the Sales reps screen, when it loads, then revenue from each rep's customers is Jane 833.04, Margaret 775.40, and Steve 720.16.
- **AC-10** (question 9): Given the Sales reps screen, when it loads, then customers per rep are Jane 21, Margaret 20, Steve 18, and revenue per customer is Jane 39.67, Margaret 38.77, Steve 40.01.
- **AC-11** (question 10): Given any screen with all years in view, when it loads, then the grand total shown is 2,328.60, equal to the sum of invoice totals, and the reconciliation gap is 0.00.
- **AC-12** (question 10): Given all years are selected, when revenue is broken out by genre, by country, by year, and by rep, then each breakdown adds up to 2,328.60.
- **AC-13** (question 1): Given the year 2023 is selected on Screen 1, when the user opens Screens 2, 3, or 4, then they still show the full period (for example the Growth screen still shows all five years).

## Out of scope

- **Forecasts and budget advice.** The dashboard shows what happened. It does not predict next year or recommend how to split the marketing budget.
- **Proving reps cause sales.** The Sales reps screen shows revenue and customers per rep as context. It cannot show that a rep caused the sales, so it makes no hiring recommendation.
- **Exports and extras.** No downloads, email reports, logins, or editing of data. It is a read-only view.
- **Extra breakdowns.** No artist, album, city, or product-level views, and no filters beyond the year picker on Screen 1.
