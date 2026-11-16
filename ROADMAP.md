# Roadmap

Phases in critical-path order: each one needs the one before it. Every task
is a GitHub Issue small enough to finish in one fresh session, with its
acceptance criteria and the tests that prove it.

| Phase | Goal | Issues |
|---|---|---|
| 1. Data connection | The app reads the team's database, locally and on Community Cloud | #4, #5 |
| 2. Data layer | Every metric in the spec has a tested function in `dashboard/metrics.py` | #6, #7, #8, #9, #10, #11, #12, #13, #14, #15, #16 |
| 3. Views | Each stakeholder question has a screen section that answers it, built as `design.md` draws it | #17, #18, #19, #20, #21, #22, #23 |
| 4. Filters | The interactions the spec lists work, and the numbers still reconcile | #24, #25, #48 |
| 5. Polish and deploy | The app follows every rule in `design.md`; `mockup.py` is gone; the live app link is in the README | #26, #27 |

## Critical path

Longest chain, which sets the pace: #4 → #6 → #7 → #16 → #18 → #19 → #20 → #24 → #25 → #48 → #26 → #27.

Which Issues block which:

- #4 (local connection) blocks #5 (hello-world deploy) and #6 (grand total).
- #6 (grand total) blocks the rest of the data layer: #7, #8, #9, #10, #11, #12, #14.
- Within the data layer: #12 blocks #13; #14 blocks #15; #7, #8, #10, and #14 block #16 (group totals against Finance).
- #5 and #6 block #17 (app shell). #16 and #17 block #18 (Finance section).
- #18 blocks every screen: #19, #20, #21, #22, #23. Each screen also needs its own data Issues: #19 needs #7, #8; #20 needs #9, #19; #21 needs #10, #11; #22 needs #12, #13; #23 needs #14, #15.
- #19 and #20 block #24 (year picker); #21, #22, #23, and #24 block #25 (screens 2-4 ignore the picker).
- #25 blocks #48 (back-to-top button); #48 blocks #26 (style audit); #26 blocks #27 (final deploy).

---

## Dashboard review

When the dashboard is finished, the Pitch Lead runs the final review. Each fix
becomes a GitHub Issue labeled `phase-1` through `phase-5`, for the phase it
belongs to, and each review adds one line below.

<Filled in by /dashkit:review-dashboard: one line per review, "- YYYY-MM-DD: fixes in #n, #n".>
