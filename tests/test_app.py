import io
from datetime import datetime

import pytest

pytest.importorskip("flask")

from app import app
from transaction_summary import Transaction


def test_index_page():
    client = app.test_client()
    res = client.get("/")
    assert res.status_code == 200
    assert "PDF 거래내역 월별 합산기" in res.get_data(as_text=True)


def test_analyze_page_renders_summary(monkeypatch):
    client = app.test_client()

    def fake_extract(_):
        return [
            Transaction(datetime(2025, 3, 4), 270000),
            Transaction(datetime(2025, 3, 11), 160000),
        ]

    monkeypatch.setattr("app.extract_transactions_from_pdf", fake_extract)

    data = {"pdf": (io.BytesIO(b"dummy"), "statement.pdf")}
    res = client.post("/analyze", data=data, content_type="multipart/form-data")

    text = res.get_data(as_text=True)
    assert res.status_code == 200
    assert "2025-03" in text
    assert "430,000" in text


def test_download_csv():
    client = app.test_client()
    res = client.post("/download", data={"csv_data": "거래월,거래금액 합계\n2025-03,430000\n"})
    assert res.status_code == 200
    assert "attachment; filename=monthly_summary.csv" in res.headers["Content-Disposition"]
