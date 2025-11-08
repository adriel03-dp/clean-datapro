from pathlib import Path
import pandas as pd
from src.report_generator import generate_pdf_report


def test_generate_pdf_report_creates_file(tmp_path: Path):
    sample = pd.DataFrame(
        [
            {
                "column": "id",
                "missing_pct": 0.0,
                "missing_count": 0,
                "dtype": "int64",
                "unique_count": 3,
                "sample_values": [1, 2, 3],
            }
        ]
    )
    out = tmp_path / "report_test.pdf"
    generate_pdf_report(
        sample,
        str(out),
        title="Test Report",
        dataset_name="unit-test",
        generated_by="pytest",
    )

    assert out.exists()
    # rough sanity: file size should be > 100 bytes
    assert out.stat().st_size > 100
