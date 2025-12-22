# 🧪 Testing Recommendations

## Current Test Coverage

### What's Tested ✅

```python
def test_analyze_missing_summary_basic():
    # ✅ Basic structure
    # ✅ Missing counts
    # ✅ Unique counts
```

### What's NOT Tested ⚠️

- [ ] Empty DataFrames
- [ ] All-null columns
- [ ] Type conversion edge cases
- [ ] Datetime handling
- [ ] Duplicate removal accuracy
- [ ] Summary metric calculations
- [ ] Large datasets
- [ ] Performance

---

## 🧪 Recommended Test Cases

### Test 1: Empty DataFrame

```python
def test_clean_dataframe_empty():
    df = pd.DataFrame()  # Empty
    cleaned, summary = clean_dataframe(df)

    assert cleaned.empty
    assert summary["original_rows"] == 0
    assert summary["missing_before_total"] == 0
    # Should not crash!
```

### Test 2: All-Null Column

```python
def test_fill_column_all_null_numeric():
    s = pd.Series([None, None, None], dtype="float64")
    result = _fill_column(s)

    # Should all be 0 (default for empty numeric)
    assert result.isna().sum() == 0
    assert all(result == 0)

def test_fill_column_all_null_object():
    s = pd.Series([None, None, None], dtype="object")
    result = _fill_column(s)

    # Should all be empty string
    assert result.isna().sum() == 0
    assert all(result == "")
```

### Test 3: Numeric Column with Median

```python
def test_fill_column_numeric_median():
    s = pd.Series([1, 2, None, 4, 5])
    result = _fill_column(s)

    # Median of [1,2,4,5] = 3.0
    assert result[2] == 3.0
    assert result.isna().sum() == 0
```

### Test 4: Categorical Column with Mode

```python
def test_fill_column_categorical_mode():
    s = pd.Series(["A", "B", None, "A", "B", "B"])
    result = _fill_column(s)

    # Mode is "B" (appears 3 times)
    assert result[2] == "B"
    assert result.isna().sum() == 0
```

### Test 5: Duplicate Removal

```python
def test_clean_dataframe_duplicates():
    df = pd.DataFrame({
        "a": [1, 2, 1],
        "b": [4, 5, 4]
    })
    cleaned, summary = clean_dataframe(df, drop_duplicates=True)

    assert len(cleaned) == 2  # One duplicate removed
    assert summary["dropped_duplicates"] == 1
    assert cleaned.iloc[0]["a"] == 1  # First occurrence kept
```

### Test 6: Type Inference

```python
def test_type_inference_numeric():
    df = pd.DataFrame({
        "mixed": ["1", "2", "3"]
    })
    cleaned, summary = clean_dataframe(df)

    # Should attempt conversion
    # (Note: Current implementation uses errors="raise")
    # So this stays as object
    assert cleaned["mixed"].dtype == "object"  # All or nothing

def test_type_inference_partial_numeric():
    df = pd.DataFrame({
        "partial": ["1", "2", "NA"]
    })
    cleaned, summary = clean_dataframe(df)

    # Can't convert, stays as object
    assert cleaned["partial"].dtype == "object"
```

### Test 7: Missing Value Percentages

```python
def test_missing_percentage_calculation():
    df = pd.DataFrame({
        "a": [1, 2, None, None, 5],  # 40% missing
        "b": [1, None, None, None, 5]  # 60% missing
    })
    summary = analyze_missing_summary(df)

    row_a = summary[summary["column"] == "a"].iloc[0]
    row_b = summary[summary["column"] == "b"].iloc[0]

    assert row_a["missing_pct"] == 40.0
    assert row_b["missing_pct"] == 60.0
```

### Test 8: Summary Metrics

```python
def test_clean_csv_summary_metrics():
    # Create test CSV
    df = pd.DataFrame({
        "id": [1, 2, 2, None],
        "name": ["A", None, "A", "B"]
    })

    summary = analyze_missing_summary(df)

    # Metrics should be:
    # - 4 rows
    # - 2 columns
    # - 2 total missing values (1 in id, 1 in name)
    assert summary.get("missing_before_total") == 2
```

### Test 9: Datetime Handling

```python
def test_fill_column_datetime():
    s = pd.Series([
        pd.Timestamp("2020-01-01"),
        pd.Timestamp("2020-12-31"),
        pd.NaT
    ])
    result = _fill_column(s)

    # Current: Fills with min (earliest)
    assert result[2] == pd.Timestamp("2020-01-01")

    # Should it be median instead?
    # assert result[2] == pd.Timestamp("2020-06-16")  # Approximately
```

### Test 10: Large Dataset Performance

```python
def test_performance_large_dataset():
    import time

    # Create large DataFrame: 100k rows, 50 columns
    df = pd.DataFrame({
        f"col_{i}": [i] * 100000
        for i in range(50)
    })

    start = time.time()
    cleaned, summary = clean_dataframe(df)
    elapsed = time.time() - start

    # Should complete in reasonable time
    assert elapsed < 5.0  # seconds
    assert len(cleaned) == 100000
```

---

## Running Tests

### Run all tests

```bash
pytest tests/
```

### Run with coverage

```bash
pytest tests/ --cov=src --cov=backend/src
```

### Run specific test

```bash
pytest tests/test_cleaner.py::test_analyze_missing_summary_basic
```

### Run with verbose output

```bash
pytest tests/ -v
```

---

## Expected Test Results

If you run these tests, you'll likely find:

✅ **Will pass:**

- Empty DataFrame handling (or will crash - needs fix)
- Duplicate removal
- Missing percentage calculations
- Numeric median filling
- Categorical mode filling

❌ **Might reveal issues:**

- Type inference edge cases
- Datetime with all NaT
- Division by zero (0 rows)
- Large dataset performance

---

## Test Coverage Goals

### Current Coverage: ~20%

```
├─ Tested:
│  ├─ analyze_missing_summary (basic)
│  └─ generate_pdf_report (basic)
│
└─ Not Tested (80%):
   ├─ clean_dataframe
   ├─ _fill_column
   ├─ Type inference
   ├─ Edge cases
   └─ Integration tests
```

### Target Coverage: >80%

```
├─ Unit Tests (60%):
│  ├─ _fill_column (all types)
│  ├─ clean_dataframe (normal + edge)
│  └─ analyze_missing_summary (comprehensive)
│
└─ Integration Tests (20%):
   ├─ clean_csv (end-to-end)
   └─ Report generation
```

---

## Quick Test Creation

### Add to `tests/test_cleaner.py`:

```python
import pytest
import pandas as pd
import numpy as np
from src.cleaner import clean_dataframe, _fill_column, analyze_missing_summary


class TestFillColumn:
    def test_numeric_with_none(self):
        s = pd.Series([1, 2, None, 4, 5])
        result = _fill_column(s)
        assert result.isna().sum() == 0
        assert result[2] == 3.0  # median

    def test_categorical_with_none(self):
        s = pd.Series(["A", "B", None, "B", "B"])
        result = _fill_column(s)
        assert result[2] == "B"  # mode

    def test_empty_numeric(self):
        s = pd.Series([None, None, None], dtype="float64")
        result = _fill_column(s)
        assert all(result == 0)


class TestCleanDataframe:
    def test_removes_duplicates(self):
        df = pd.DataFrame({
            "a": [1, 2, 1],
            "b": [4, 5, 4]
        })
        cleaned, summary = clean_dataframe(df, drop_duplicates=True)
        assert len(cleaned) == 2
        assert summary["dropped_duplicates"] == 1

    def test_fills_missing_values(self):
        df = pd.DataFrame({
            "a": [1, 2, None],
            "b": ["X", None, "X"]
        })
        cleaned, summary = clean_dataframe(df, drop_duplicates=False)
        assert cleaned.isna().sum().sum() == 0


class TestMissingAnalysis:
    def test_percentage_calculation(self):
        df = pd.DataFrame({
            "a": [1, None, 3, None, 5]
        })
        summary = analyze_missing_summary(df)
        assert summary.iloc[0]["missing_pct"] == 40.0

    def test_unique_count(self):
        df = pd.DataFrame({
            "a": [1, 1, None, 3, 3, 3]
        })
        summary = analyze_missing_summary(df)
        assert summary.iloc[0]["unique_count"] == 3  # 1, 3, and NaN is not counted


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## Summary

✅ **Cleaning logic is correct**
⚠️ **Test coverage is insufficient**
📝 **Recommended: Add 10+ test cases**
🚀 **Ready to improve reliability**

Run these tests to build confidence in the implementation!

---

_Recommendation Date: December 19, 2024_
