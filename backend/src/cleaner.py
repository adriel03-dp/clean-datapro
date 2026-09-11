from typing import Any, Dict, Tuple
from pathlib import Path
import warnings
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
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif isinstance(obj, np.bool_):
        return bool(obj)
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
    missing = pd.isna(val)
    if isinstance(missing, (bool, np.bool_)) and bool(missing):
        return True
    
    # Check for placeholder strings (case-insensitive)
    if isinstance(val, str):
        if val.lower().strip() in PLACEHOLDER_VALUES:
            return True
    
    return False


def _missing_mask(series: pd.Series) -> pd.Series:
    """Build a vectorized missing/placeholder mask for a CSV column."""
    mask = series.isna()
    if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
        normalized = series.astype("string").str.strip().str.lower()
        mask = mask | normalized.isin(PLACEHOLDER_VALUES)
    return mask.astype(bool)


def _is_numeric_column(s: pd.Series) -> bool:
    """Detect if a column should be numeric by checking non-missing values."""
    non_missing = s[~_missing_mask(s)]

    if non_missing.empty:
        return False

    # Datetime values can be represented as integers internally, but must
    # remain dates so the date-specific fill strategy can run.
    if pd.api.types.is_datetime64_any_dtype(s):
        return False
    
    # Use pandas' native conversion instead of a Python loop over every cell.
    numeric_count = int(pd.to_numeric(non_missing, errors="coerce").notna().sum())
    
    # A mostly numeric column with one malformed value should still be cleaned
    # as numeric. Require at least two numeric observations and a 60% ratio for
    # mixed columns; native numeric dtypes are handled by pandas directly.
    ratio = numeric_count / len(non_missing) if non_missing.shape[0] > 0 else 0
    return numeric_count >= 2 and ratio >= 0.6


def _replace_placeholders(df: pd.DataFrame, copy: bool = True) -> pd.DataFrame:
    """Replace placeholder values with actual NaN so they can be properly filled."""
    # The cleaning pipeline can opt out of copying because it owns the frame.
    working = df.copy() if copy else df
    
    for col in working.columns:
        s = working[col]
        # Pandas 3 may infer CSV text as ``str``/StringDtype rather than object.
        # Apply the same placeholder rule to every scalar column type.
        mask = _missing_mask(s)
        if bool(mask.any()):
            working.loc[mask, col] = np.nan
    
    return working


def _infer_datetime_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Parse mostly-date text columns so date-specific filling can run."""
    working = df
    copied = False
    for col in working.columns:
        series = working[col]
        if not pd.api.types.is_string_dtype(series):
            continue
        non_missing = series[~_missing_mask(series)]
        if len(non_missing) < 2:
            continue
        # Sampling is enough to identify date-shaped text and keeps large CSVs
        # from being parsed repeatedly during type detection.
        sample = non_missing.iloc[:5000]
        # Numeric identifiers and year columns are not dates just because
        # pandas can parse them. Keeping them numeric prevents an expensive,
        # surprising conversion on large health/finance exports.
        if sample.astype("string").str.fullmatch(r"[+-]?\d+(?:\.\d+)?").all():
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            parsed = pd.to_datetime(sample, errors="coerce")
        if parsed.notna().mean() >= 0.8:
            if not copied:
                working = df.copy()
                copied = True
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                working[col] = pd.to_datetime(series, errors="coerce")
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
        missing_mask = _missing_mask(s)
        missing = int(missing_mask.sum())
        missing_pct = round((missing / total) * 100, 2) if total else 0.0
        dtype = str(s.dtype)
        
        # Count unique non-missing values
        non_missing = s[~missing_mask]
        unique_count = int(non_missing.nunique())

        # ALSO: Detect type inconsistencies in columns that SHOULD be numeric
        type_issues = 0
        if _is_numeric_column(s):
            # This is a numeric column with type issues
            # Count non-numeric values (excluding missing values already counted)
            type_issues = int(
                pd.to_numeric(non_missing, errors="coerce").isna().sum()
            )
        
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
    mask = _missing_mask(s)
    s = s.mask(mask, np.nan)
    
    if pd.api.types.is_numeric_dtype(s):
        # Use median for numeric columns (robust to outliers)
        if s.dropna().empty:
            return s.fillna(0)
        return s.fillna(s.median())
    
    if pd.api.types.is_datetime64_any_dtype(s):
        # Fill with earliest date for datetime columns
        if s.dropna().empty:
            return s.fillna(pd.Timestamp("1970-01-01"))
        return s.fillna(s.min())
    
    # Treat as categorical/object
    if s.dropna().empty:
        # Do not use the literal "Unknown" here: it is intentionally treated
        # as a missing placeholder by the quality checks.
        return s.fillna("Not provided")
    
    try:
        mode = s.mode(dropna=True)
        if not mode.empty:
            return s.fillna(mode.iloc[0])
    except Exception:
        pass
    
    return s.fillna("Not provided")


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

    df = _infer_datetime_columns(df)
    original_rows = len(df)
    
    # Detect which columns should be numeric (based on majority non-missing values)
    numeric_cols_to_fix = {}
    for col in df.columns:
        if _is_numeric_column(df[col]):
            numeric_cols_to_fix[col] = True
    
    # Analyze BEFORE replacing placeholders to show what was actually wrong
    missing_summary_before = analyze_missing_summary(df)
    
    # Now replace placeholder values with NaN
    working = _replace_placeholders(df, copy=False)
    missing_before = int(missing_summary_before["total_issues"].sum())

    # Drop exact duplicates if requested
    dropped_dupes = 0
    if drop_duplicates:
        before = len(working)
        working = working.drop_duplicates()
        dropped_dupes = before - len(working)

    # Attempt to coerce numeric columns where possible
    for col in working.columns:
        s = working[col]
        if col in numeric_cols_to_fix and not pd.api.types.is_numeric_dtype(s):
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

    missing_after = int(sum(_missing_mask(working[col]).sum() for col in working.columns))
    cleaned_rows = len(working)

    # Per-column summaries are calculated from the actual cleaned data. Do not
    # overwrite the values: unresolved values should remain visible.
    missing_summary_after = analyze_missing_summary(working)

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

    return working, _convert_numpy_types(summary)


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

    df = pd.read_csv(p_in, keep_default_na=False, low_memory=False)
    cleaned_df, inner_summary = clean_dataframe(df, drop_duplicates=drop_duplicates)

    # ensure output dir exists
    p_out.parent.mkdir(parents=True, exist_ok=True)
    cleaned_df.to_csv(p_out, index=False)

    total_cells = df.size
    missing_cells = int(
        sum(_is_missing_value(value) for column in df.columns for value in df[column])
    )
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
