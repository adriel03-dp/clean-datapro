import pandas as pd
from src.cleaner import analyze_missing_summary, clean_dataframe


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


def test_placeholder_detection():
    """Test that placeholder values (UNKNOWN, ERROR, etc) are detected as missing."""
    df = pd.DataFrame({
        "id": [1, 2, 3, 4],
        "name": ["Alice", "UNKNOWN", "ERROR", "Diana"],
        "status": ["Active", "N/A", "Inactive", "na"]
    })
    
    summary = analyze_missing_summary(df, top_values=2)
    
    # name column should have 2 missing (UNKNOWN, ERROR)
    row_name = summary[summary["column"] == "name"].iloc[0]
    assert int(row_name["missing_count"]) == 2
    
    # status column should have 2 missing (N/A, na)
    row_status = summary[summary["column"] == "status"].iloc[0]
    assert int(row_status["missing_count"]) == 2


def test_clean_dataframe_fills_missing():
    """Test that clean_dataframe properly fills missing values including placeholders."""
    df = pd.DataFrame({
        "id": [1, 2, 3, 4],
        "name": ["Alice", "UNKNOWN", "ERROR", "Diana"],
        "age": [25, None, 30, 35]
    })
    
    cleaned, summary = clean_dataframe(df)
    
    # All missing values should be filled
    assert summary["missing_after_total"] == 0
    assert cleaned.isna().sum().sum() == 0
    # Should have found and fixed 3 issues (2 in name, 1 in age)
    assert summary["missing_before_total"] == 3
