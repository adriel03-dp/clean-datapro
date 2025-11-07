from typing import Any, Dict, Tuple
from pathlib import Path
import pandas as pd


def analyze_missing_summary(df: pd.DataFrame, top_values: int = 3) -> pd.DataFrame:
    """Return a DataFrame summarizing missing values and basic stats per column."""
    total = len(df)
    rows = []

    for col in df.columns:
        s = df[col]
        missing = int(s.isna().sum())
        missing_pct = round((missing / total) * 100, 2) if total else 0.0
        dtype = str(s.dtype)
        unique_count = int(s.nunique(dropna=True))

        non_null = s.dropna().astype(object)
        sample_values = []
        if not non_null.empty:
            seen = set()
            for v in non_null.tolist():
                if v not in seen:
                    sample_values.append(v)
                    seen.add(v)
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


def _fill_column(s: pd.Series) -> pd.Series:
    """Fill NaNs in a single Series based on dtype heuristics."""
    if pd.api.types.is_numeric_dtype(s):
        # use median to be robust
        if s.dropna().empty:
            return s.fillna(0)
        return s.fillna(s.median())
    if pd.api.types.is_datetime64_any_dtype(s):
        # fill with earliest date or leave as NaT
        if s.dropna().empty:
            return s
        return s.fillna(s.min())
    # treat as categorical/object
    if s.dropna().empty:
        return s.fillna("")
    try:
        mode = s.mode(dropna=True)
        if not mode.empty:
            return s.fillna(mode.iloc[0])
    except Exception:
        pass
    return s.fillna("")


def clean_dataframe(
    df: pd.DataFrame, drop_duplicates: bool = True
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Clean a DataFrame and return (cleaned_df, summary_dict).

    Cleaning steps:
      - record original row count
      - drop exact duplicate rows (if requested)
      - fill NaNs per-column using simple heuristics

    Summary contains counts before/after and per-column missing info.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")

    original_rows = len(df)
    missing_before = int(df.isna().sum().sum())

    working = df.copy()

    dropped_dupes = 0
    if drop_duplicates:
        before = len(working)
        working = working.drop_duplicates()
        dropped_dupes = before - len(working)

    # attempt to coerce numeric columns where possible
    for col in working.columns:
        s = working[col]
        # try numeric
        if s.dtype == object:
            # try to convert to numeric safely
            try:
                converted = pd.to_numeric(s, errors="raise")
                working[col] = converted
            except Exception:
                # leave as-is
                pass

    # fill missing values per column
    for col in working.columns:
        working[col] = _fill_column(working[col])

    missing_after = int(working.isna().sum().sum())
    cleaned_rows = len(working)

    # per-column summaries
    missing_summary_before = analyze_missing_summary(df)
    missing_summary_after = analyze_missing_summary(working)

    summary = {
        "original_rows": original_rows,
        "cleaned_rows": cleaned_rows,
        "dropped_duplicates": dropped_dupes,
        "missing_before_total": missing_before,
        "missing_after_total": missing_after,
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
            pd.api.types.is_numeric_dtype(df[c]) for c in df.columns
        )
    )

    categorical_cols = int(len(df.columns) - numeric_cols)

    summary = {
        "rows": len(df),
        "columns": len(df.columns),
        "missing_pct": missing_pct,
        "numeric_cols": numeric_cols,
        "categorical_cols": categorical_cols,
        # include the more detailed cleaning summary
        **inner_summary,
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
