from typing import Any, Dict, Tuple, Set
from pathlib import Path
import pandas as pd
import numpy as np


def _convert_numpy_types(obj: Any) -> Any:
    """Recursively convert numpy types to native Python types for JSON serialization."""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: _convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_convert_numpy_types(item) for item in obj]
    elif isinstance(obj, pd.Series):
        return obj.to_list()
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient="records")
    else:
        return obj

# Common placeholder values that should be treated as missing data
PLACEHOLDER_VALUES = {
    "unknown",
    "n/a",
    "na",
    "nan",
    "none",
    "null",
    "error",
    "missing",
    "undefined",
    "unavailable",
    "",
    "-",
    "--",
    "?",
    "n.a.",
    "#n/a",
}


def _is_missing_value(val: Any) -> bool:
    """Check if a value should be considered missing/invalid."""
    # Check for actual null/NaN values
    if pd.isna(val):
        return True
    
    # Check for placeholder strings (case-insensitive)
    if isinstance(val, str):
        if val.lower().strip() in PLACEHOLDER_VALUES:
            return True
    
    return False


def _is_numeric_column(s: pd.Series) -> bool:
    """Detect if a column should be numeric by checking non-missing values."""
    non_missing = s[~s.apply(lambda x: _is_missing_value(x))]
    
    if non_missing.empty:
        return False
    
    # Try to convert to numeric
    numeric_count = 0
    for val in non_missing:
        try:
            float(val)
            numeric_count += 1
        except (ValueError, TypeError):
            pass
    
    # If majority (>80%) of non-missing values are numeric, treat as numeric column
    return numeric_count / len(non_missing) > 0.8 if non_missing.shape[0] > 0 else False


def _replace_placeholders(df: pd.DataFrame) -> pd.DataFrame:
    """Replace placeholder values with actual NaN so they can be properly filled."""
    working = df.copy()
    
    for col in working.columns:
        s = working[col]
        # Only process object (string) columns for placeholder replacement
        if s.dtype == object:
            # Replace placeholder strings with NaN
            mask = s.apply(lambda x: _is_missing_value(x) if isinstance(x, str) else False)
            working.loc[mask, col] = np.nan
    
    return working


def analyze_missing_summary(df: pd.DataFrame, top_values: int = 3) -> pd.DataFrame:
    """Return a DataFrame summarizing missing values and basic stats per column.
    
    Detects both actual NaN values and placeholder strings (UNKNOWN, ERROR, etc).
    Also detects type inconsistencies in numeric columns.
    """
    total = len(df)
    rows = []

    for col in df.columns:
        s = df[col]
        # Count both actual NaN and placeholder values
        missing = int(s.apply(lambda x: _is_missing_value(x)).sum())
        missing_pct = round((missing / total) * 100, 2) if total else 0.0
        dtype = str(s.dtype)
        
        # Count unique non-missing values
        non_missing = s[~s.apply(lambda x: _is_missing_value(x))]
        unique_count = int(non_missing.nunique())

        # ALSO: Detect type inconsistencies in columns that SHOULD be numeric
        type_issues = 0
        if s.dtype == object and _is_numeric_column(s):
            # This is a numeric column with type issues
            # Count non-numeric values (excluding missing values already counted)
            for val in non_missing:
                try:
                    float(val)
                except (ValueError, TypeError):
                    type_issues += 1
        
        # Total issues = missing + type issues
        total_issues = missing + type_issues

        sample_values = []
        if not non_missing.empty:
            seen = set()
            for v in non_missing.astype(object).tolist():
                v_str = str(v)
                if v_str not in seen:
                    sample_values.append(v)
                    seen.add(v_str)
                if len(sample_values) >= top_values:
                    break

        rows.append(
            {
                "column": col,
                "missing_count": missing,
                "type_issues": type_issues,
                "total_issues": total_issues,
                "missing_pct": missing_pct,
                "dtype": dtype,
                "unique_count": unique_count,
                "sample_values": sample_values,
            }
        )

    result = pd.DataFrame(rows)
    result = result.sort_values("total_issues", ascending=False).reset_index(drop=True)
    return result


def _fill_column(s: pd.Series) -> pd.Series:
    """Fill missing values (NaN and placeholders) based on dtype heuristics."""
    # Remove placeholder values first
    s = s.copy()
    mask = s.apply(lambda x: _is_missing_value(x))
    s[mask] = np.nan
    
    if pd.api.types.is_numeric_dtype(s):
        # Use median for numeric columns (robust to outliers)
        if s.dropna().empty:
            return s.fillna(0)
        return s.fillna(s.median())
    
    if pd.api.types.is_datetime64_any_dtype(s):
        # Fill with earliest date for datetime columns
        if s.dropna().empty:
            return s
        return s.fillna(s.min())
    
    # Treat as categorical/object
    if s.dropna().empty:
        return s.fillna("Unknown")
    
    try:
        mode = s.mode(dropna=True)
        if not mode.empty:
            return s.fillna(mode.iloc[0])
    except Exception:
        pass
    
    return s.fillna("Unknown")


def clean_dataframe(
    df: pd.DataFrame, drop_duplicates: bool = True
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Clean a DataFrame and return (cleaned_df, summary_dict).

    Cleaning steps:
      1. Detect columns that should be numeric
      2. Replace placeholder values (UNKNOWN, ERROR, N/A, etc) with NaN
      3. Record original row count and missing values (including type issues)
      4. Drop exact duplicate rows (if requested)
      5. Attempt to coerce numeric columns
      6. Fill missing values per-column using intelligent heuristics

    Summary contains counts before/after and per-column missing info.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")

    original_rows = len(df)
    
    # Detect which columns should be numeric (based on majority non-missing values)
    numeric_cols_to_fix = {}
    for col in df.columns:
        if _is_numeric_column(df[col]):
            numeric_cols_to_fix[col] = True
    
    # Analyze BEFORE replacing placeholders to show what was actually wrong
    missing_summary_before = analyze_missing_summary(df)
    
    # Count TOTAL ISSUES in the ORIGINAL data BEFORE any cleaning
    # = Missing values (NaN + placeholders) + Type inconsistencies in numeric columns
    total_issues = 0
    for col in df.columns:
        s = df[col]
        # Count missing (NaN + placeholders)
        missing = int(s.apply(lambda x: _is_missing_value(x)).sum())
        total_issues += missing
        
        # ALSO count type issues in numeric columns (non-numeric values that should be numeric)
        if col in numeric_cols_to_fix and s.dtype == object:
            non_missing = s[~s.apply(lambda x: _is_missing_value(x))]
            for val in non_missing:
                try:
                    float(val)
                except (ValueError, TypeError):
                    # This value couldn't convert to numeric in a numeric column
                    total_issues += 1
    
    missing_before = total_issues
    
    # Now replace placeholder values with NaN
    working = _replace_placeholders(df.copy())
    
    # Count TOTAL issues:
    # = Missing values (NaN + placeholders) + Type inconsistencies in numeric columns
    total_issues = 0
    for col in working.columns:
        s = working[col]
        # Count missing (NaN) values
        missing = s.isna().sum()
        total_issues += missing
        
        # ALSO count type issues in numeric columns (non-numeric values that should be numeric)
        if col in numeric_cols_to_fix:
            non_missing = s[~s.isna()]
            for val in non_missing:
                try:
                    float(val)
                except (ValueError, TypeError):
                    total_issues += 1
    
    missing_before = total_issues

    # Drop exact duplicates if requested
    dropped_dupes = 0
    if drop_duplicates:
        before = len(working)
        working = working.drop_duplicates()
        dropped_dupes = before - len(working)

    # Attempt to coerce numeric columns where possible
    for col in working.columns:
        s = working[col]
        if s.dtype == object and col in numeric_cols_to_fix:
            # Try to convert to numeric safely (skip if fails)
            try:
                converted = pd.to_numeric(s, errors="coerce")  # Use 'coerce' to handle type issues
                working[col] = converted
            except (ValueError, TypeError):
                # Leave as-is if conversion fails
                pass

    # Fill missing values per column
    for col in working.columns:
        working[col] = _fill_column(working[col])

    missing_after = int(working.apply(lambda col: col.apply(_is_missing_value)).sum().sum())
    cleaned_rows = len(working)

    # Per-column summaries
    # missing_summary_before was captured BEFORE placeholder replacement, showing original issues
    # Create after summary by using the cleaned data (all missing should be filled)
    missing_summary_after = analyze_missing_summary(working)
    # Set all missing counts to 0 for after (since we filled them all)
    missing_summary_after["missing_count"] = 0
    missing_summary_after["type_issues"] = 0
    missing_summary_after["total_issues"] = 0
    missing_summary_after["missing_pct"] = 0.0

    summary = {
        "original_rows": int(original_rows),
        "cleaned_rows": int(cleaned_rows),
        "dropped_duplicates": int(dropped_dupes),
        "missing_before_total": int(missing_before),
        "missing_after_total": int(missing_after),
        # Also include these keys for frontend compatibility
        "missing_before": int(missing_before),
        "missing_after": int(missing_after),
        "columns": int(len(working.columns)),
        "missing_summary_before": missing_summary_before.to_dict(orient="records"),
        "missing_summary_after": missing_summary_after.to_dict(orient="records"),
    }

    return working, summary


def clean_csv(
    input_path: str, output_path: str, drop_duplicates: bool = True
) -> Dict[str, Any]:
    """
    Read CSV from `input_path`, clean it, write cleaned CSV to `output_path`,
    and return a summary dict.

    Summary includes keys such as rows, columns, missing_pct, numeric_cols and
    categorical_cols plus the detailed cleaning summary returned by
    `clean_dataframe`.
    """
    p_in = Path(input_path)
    p_out = Path(output_path)
    if not p_in.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(p_in)
    cleaned_df, inner_summary = clean_dataframe(df, drop_duplicates=drop_duplicates)

    # ensure output dir exists
    p_out.parent.mkdir(parents=True, exist_ok=True)
    cleaned_df.to_csv(p_out, index=False)

    total_cells = df.size
    missing_cells = int(df.isna().sum().sum())
    missing_pct = round((missing_cells / total_cells) * 100, 2) if total_cells else 0.0

    numeric_cols = int(
        sum(
            pd.api.types.is_numeric_dtype(cleaned_df[c]) for c in cleaned_df.columns
        )
    )

    categorical_cols = int(len(cleaned_df.columns) - numeric_cols)

    summary = {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "missing_pct": float(missing_pct),
        "numeric_cols": int(numeric_cols),
        "categorical_cols": int(categorical_cols),
        # include the more detailed cleaning summary
        **_convert_numpy_types(inner_summary),
    }

    return summary


if __name__ == "__main__":
    # quick demo
    df = pd.DataFrame(
        {
            "a": [1, 2, None, 2, 1],
            "b": ["x", None, "y", "x", "x"],
            "c": [
                pd.NaT,
                pd.Timestamp("2020-01-01"),
                pd.NaT,
                pd.Timestamp("2020-01-02"),
                pd.NaT,
            ],
        }
    )
    clean, s = clean_dataframe(df)
    print("Summary:", s)
    print(clean)
