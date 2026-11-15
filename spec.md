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

## Out of scope
