from __future__ import annotations

import tempfile
from pathlib import Path

from flask import Flask, Response, render_template, request

from transaction_summary import extract_transactions_from_pdf, summarize_monthly_amount

app = Flask(__name__)


def _build_csv(summary: dict[str, int]) -> str:
    lines = ["지급월,매출 합계"]
    for month, amount in summary.items():
        lines.append(f"{month},{amount}")
    return "\n".join(lines) + "\n"


@app.get("/")
def index() -> str:
    return render_template("index.html")


@app.post("/analyze")
def analyze() -> str:
    file = request.files.get("pdf")
    if not file or file.filename == "":
        return render_template("index.html", error="PDF 파일을 선택해주세요.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file.read())
        tmp_path = Path(tmp.name)

    try:
        transactions = extract_transactions_from_pdf(tmp_path)
        if not transactions:
            return render_template(
                "index.html",
                error="거래 데이터를 찾지 못했습니다. 스캔(이미지) PDF라면 OCR 환경(Tesseract) 설정이 필요할 수 있습니다.",
            )

        monthly_summary = summarize_monthly_amount(transactions)
        rows = [{"month": m, "total": v} for m, v in monthly_summary.items()]
        csv_data = _build_csv(monthly_summary)

        return render_template(
            "index.html",
            rows=rows,
            tx_count=len(transactions),
            csv_data=csv_data,
        )
    finally:
        tmp_path.unlink(missing_ok=True)


@app.post("/download")
def download() -> Response:
    csv_data = request.form.get("csv_data", "")
    return Response(
        csv_data,
        headers={"Content-Disposition": "attachment; filename=monthly_summary.csv"},
        mimetype="text/csv; charset=utf-8",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
