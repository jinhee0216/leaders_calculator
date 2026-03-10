from datetime import datetime

from transaction_summary import (
    Transaction,
    _extract_transactions_from_text,
    _extract_transactions_with_ocr,
    _parse_tx_from_row,
    _parse_tx_from_text_line,
    parse_amount,
    parse_date,
    summarize_monthly_amount,
)


def test_parse_amount():
    assert parse_amount("270,000") == 270000
    assert parse_amount(" 410000 ") == 410000


def test_parse_date():
    assert parse_date("2025.03.04") == datetime(2025, 3, 4)
    assert parse_date("2025-03-11") == datetime(2025, 3, 11)


def test_summarize_monthly_amount():
    txs = [
        Transaction(datetime(2024, 11, 19), 45340),
        Transaction(datetime(2024, 11, 20), 10000),
        Transaction(datetime(2024, 12, 1), 5000),
    ]

    assert summarize_monthly_amount(txs) == {
        "2024-11": 55340,
        "2024-12": 5000,
    }


def test_extract_transactions_from_text_lines_only_payout_section():
    text = """
지급 일자 2024-11-19 금액 45,340
접수(청구) 일자 2024-10-30 금액 46,880
""".strip()

    txs = _extract_transactions_from_text(text)
    assert len(txs) == 1
    assert txs[0] == Transaction(datetime(2024, 11, 19), 45340)


def test_parse_payout_row_with_header():
    header = ["업무구분", "접수(청구) 일자", "접수(청구) 금액", "지급 구분", "지급 일자", "지급 금액", "미지급금액"]
    row = ["선지급", "2024-10-30", "46,880", "지급", "2024-11-19", "45,340", "0"]
    tx = _parse_tx_from_row(row, header)
    assert tx == Transaction(datetime(2024, 11, 19), 45340)


def test_parse_row_ignores_non_payout_type():
    header = ["업무구분", "지급 구분", "지급 일자", "지급 금액"]
    row = ["선지급", "취소", "2024-11-19", "45,340"]
    assert _parse_tx_from_row(row, header) is None


def test_ocr_fallback_without_dependencies(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name in {"pdf2image", "pytesseract"}:
            raise ImportError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    assert _extract_transactions_with_ocr("dummy.pdf") == []


def test_parse_row_ignores_prepayment_type():
    header = ["업무구분", "지급 구분", "지급 일자", "지급 금액"]
    row = ["선지급", "선지급", "2024-08-21", "9,890"]
    assert _parse_tx_from_row(row, header) is None


def test_parse_text_ignores_prepayment_line():
    assert _parse_tx_from_text_line("선지급 2024-08-21 9,890") is None


def test_parse_text_standalone_payout_line():
    tx = _parse_tx_from_text_line("지급 2024-08-21 9,890")
    assert tx == Transaction(datetime(2024, 8, 21), 9890)
