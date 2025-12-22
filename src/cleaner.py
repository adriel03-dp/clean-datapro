from typing import List, Any
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
    """
    Analyze missing values per column in a pandas DataFrame.

    Detects both actual NaN values and placeholder strings (UNKNOWN, ERROR, etc).

    Returns a DataFrame with the following columns:
      - column: column name
      - missing_count: number of missing values (NaN/None/placeholders)
      - missing_pct: percentage of missing values (0-100, rounded to 2 decimals)
      - dtype: inferred dtype (string)
      - unique_count: number of distinct non-null values
      - sample_values: list of up to `top_values` sample non-null values

    Parameters:
      df: pandas DataFrame to analyze
      top_values: how many example non-null values to include per column
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")

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

        sample_values: List[Any] = []
        if not non_missing.empty:
            # keep order of appearance, but unique
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
                "missing_pct": missing_pct,
                "dtype": dtype,
                "unique_count": unique_count,
                "sample_values": sample_values,
            }
        )

    result = pd.DataFrame(rows)
    result = result.sort_values("missing_pct", ascending=False).reset_index(drop=True)
    return result


if __name__ == "__main__":
    # small demo when run directly
    demo = pd.DataFrame(
        {
            "id": [1, 2, 3, 4, None],
            "name": ["Alice", "Bob", None, "Diana", "Eve"],
            "age": [25, None, 37, 29, 40],
            "city": ["NY", "SF", "NY", None, "LA"],
        }
    )
    print("Input DataFrame:\n", demo)
    summary = analyze_missing_summary(demo)
    print("\nMissing summary:\n", summary)

