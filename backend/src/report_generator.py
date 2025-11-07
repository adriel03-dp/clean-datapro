import datetime
import json
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def generate_pdf_report(
    summary: dict, output_path: str, title: str = "Data Summary Report"
) -> None:
    """
    Generate a simple PDF report summarizing cleaning results.

    `summary` is the dict returned by `clean_dataframe` in `cleaner.py`.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(str(output), pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(title, styles["Title"]))
    meta = [
        f"Generated: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ')} UTC",
    ]
    meta.append(f"Original rows: {summary.get('original_rows')}")
    meta.append(f"Cleaned rows: {summary.get('cleaned_rows')}")
    meta.append(f"Dropped duplicates: {summary.get('dropped_duplicates')}")

    for line in meta:
        elements.append(Paragraph(line, styles["Normal"]))
    elements.append(Spacer(1, 12))

    # Table of per-column before/after missing %
    headers = ["Column", "Missing % (before)", "Missing % (after)", "Dtype (after)"]
    data = [headers]

    before = {r["column"]: r for r in summary.get("missing_summary_before", [])}
    after = {r["column"]: r for r in summary.get("missing_summary_after", [])}

    for col in sorted(set(list(before.keys()) + list(after.keys()))):
        b = before.get(col, {})
        a = after.get(col, {})
        row = [
            col,
            f"{b.get('missing_pct', '')}%",
            f"{a.get('missing_pct', '')}%",
            a.get("dtype", ""),
        ]
        data.append(row)

    table = Table(data, colWidths=[150, 100, 100, 150], repeatRows=1)
    style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003f5c")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]
    )
    table.setStyle(style)
    elements.append(table)

    doc.build(elements)


def save_json_summary(summary: dict, output_path: str) -> None:
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)


if __name__ == "__main__":
    # demo
    sample = {
        "original_rows": 5,
        "cleaned_rows": 5,
        "dropped_duplicates": 0,
        "missing_summary_before": [{"column": "a", "missing_pct": 20}],
        "missing_summary_after": [{"column": "a", "missing_pct": 0}],
    }
    generate_pdf_report(sample, "demo_report.pdf")
    save_json_summary(sample, "demo_summary.json")
    print("Wrote demo_report.pdf and demo_summary.json")
