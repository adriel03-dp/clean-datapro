import pandas as pd
from src.cleaner import analyze_missing_summary


def test_analyze_missing_summary_basic():
    df = pd.DataFrame({"a": [1, None, 3], "b": [None, None, "x"]})
    summary = analyze_missing_summary(df, top_values=2)

    # basic structure
    assert "column" in summary.columns
    assert "missing_count" in summary.columns

    # check values for column 'a'
    row_a = summary[summary["column"] == "a"].iloc[0]
    assert int(row_a["missing_count"]) == 1
    assert int(row_a["unique_count"]) == 2
