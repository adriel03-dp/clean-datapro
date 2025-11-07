from typing import List, Any
import pandas as pd


def analyze_missing_summary(df: pd.DataFrame, top_values: int = 3) -> pd.DataFrame:
    """
    Analyze missing values per column in a pandas DataFrame.

    Returns a DataFrame with the following columns:
      - column: column name
      - missing_count: number of missing values (NaN/None)
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
        missing = int(s.isna().sum())
        missing_pct = round((missing / total) * 100, 2) if total else 0.0
        dtype = str(s.dtype)
        unique_count = int(s.nunique(dropna=True))

        # pick up to top_values sample non-null values (converted to Python primitives)
        non_null = s.dropna().astype(object)
        sample_values: List[Any] = []
        if not non_null.empty:
            # keep order of appearance, but unique
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
