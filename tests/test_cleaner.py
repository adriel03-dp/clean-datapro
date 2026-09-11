import pandas as pd
from src.cleaner import analyze_missing_summary, clean_csv, clean_dataframe


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


def test_clean_dataframe_coerces_mostly_numeric_text():
    """Pandas string dtypes with one malformed value should be repaired."""
    df = pd.DataFrame({"score": ["10", "20", "bad", None]})

    cleaned, summary = clean_dataframe(df)

    assert cleaned["score"].dtype.kind in "fi"
    assert cleaned["score"].tolist() == [10.0, 20.0, 15.0, 15.0]
    assert summary["missing_after_total"] == 0


def test_clean_dataframe_preserves_dates_and_fills_all_placeholders():
    df = pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-02-01", ""],
            "empty": ["", "UNKNOWN", "N/A"],
        }
    )

    cleaned, summary = clean_dataframe(df)

    assert str(cleaned["date"].dtype).startswith("datetime")
    assert cleaned.isna().sum().sum() == 0
    assert summary["missing_after_total"] == 0


def test_clean_csv_writes_output_and_reports_real_progress(tmp_path):
    source = tmp_path / "source.csv"
    output = tmp_path / "cleaned.csv"
    source.write_text("name,score\nAlice,10\nUNKNOWN,20\nAlice,10\n", encoding="utf-8")
    events = []

    summary = clean_csv(source, output, progress_callback=lambda value, text: events.append((value, text)))
    cleaned = pd.read_csv(output)

    assert output.exists()
    assert summary["missing_after_total"] == 0
    assert cleaned["name"].isna().sum() == 0
    assert [value for value, _ in events] == [5, 18, 28, 78, 88, 100]
    assert events[-1][1] == "Cleaned CSV written successfully."
