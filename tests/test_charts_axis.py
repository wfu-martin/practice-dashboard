"""Issue #26: the yearly line shows whole years only (no 2021.5 ticks)."""

import pandas as pd

from dashboard import charts


def test_yearly_line_axis_is_categories_not_numbers():
    # Years kept as text must give one tick per year, never 2,021.5.
    years = pd.DataFrame({"year": ["2021", "2022", "2023"], "revenue": [449.0, 481.0, 470.0]})
    assert charts.trend_line(years, "year", "revenue", label_points=True).layout.xaxis.type == "category"


def test_monthly_line_axis_stays_a_date_axis():
    months = pd.DataFrame({"month": pd.to_datetime(["2021-01-01", "2021-02-01"]), "revenue": [35.6, 37.5]})
    assert charts.trend_line(months, "month", "revenue").layout.xaxis.type != "category"
