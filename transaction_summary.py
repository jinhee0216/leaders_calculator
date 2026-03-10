from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

DATE_PATTERN = re.compile(r"\b(\d{4})[./-](\d{1,2})[./-](\d{1,2})\b")
TIME_PATTERN = re.compile(r"\b\d{1,2}:\d{2}:\d{2}\b")
AMOUNT_TOKEN_PATTERN = re.compile(r"-?\d[\d,]*")


@dataclass(frozen=True)
class Transaction:
    transaction_date: datetime
    amount: int


def parse_amount(value: str) -> int:
    if value is None:
        raise ValueError("Amount is empty")

    text = str(value).strip()
    if not text:
        raise ValueError("Amount is empty")

    normalized = re.sub(r"[^0-9-]", "", text)
    if not normalized or normalized == "-":
        raise ValueError(f"Cannot parse amount: {value}")

    return int(normalized)


def parse_date(value: str) -> datetime:
    if value is None:
        raise ValueError("Date is empty")

    text = str(value).strip()
    match = DATE_PATTERN.search(text)
    if not match:
        raise ValueError(f"Cannot parse date: {value}")

    year, month, day = map(int, match.groups())
    return datetime(year, month, day)




def _looks_like_amount(text: str) -> bool:
    raw = str(text).strip()
    if not raw:
        return False
    if DATE_PATTERN.search(raw):
        return False
    return bool(AMOUNT_TOKEN_PATTERN.fullmatch(raw.replace(" ", "")))

def _find_column_index(header: list[str], includes: tuple[str, ...]) -> int | None:
    for idx, cell in enumerate(header):
        text = cell.replace(" ", "")
        if all(token in text for token in includes):
            return idx
    return None


def _parse_tx_from_row(row: list[str], header: list[str] | None = None) -> Transaction | None:
    cells = [str(c).strip() if c is not None else "" for c in row]

    if header:
        payout_type_idx = _find_column_index(header, ("지급", "구분"))
        payout_date_idx = _find_column_index(header, ("지급", "일자"))
        payout_amount_idx = _find_column_index(header, ("지급", "금액"))

        if (
            payout_type_idx is not None
            and payout_date_idx is not None
            and payout_amount_idx is not None
            and payout_type_idx < len(cells)
            and payout_date_idx < len(cells)
            and payout_amount_idx < len(cells)
        ):
            # 요청사항: [지급] 섹션의 [구분=지급, 일자, 금액]만 합산
            if cells[payout_type_idx].replace(" ", "") != "지급":
                return None

            date_cell = cells[payout_date_idx]
            amount_cell = cells[payout_amount_idx]
            if not date_cell or not amount_cell:
                return None

            try:
                return Transaction(parse_date(date_cell), parse_amount(amount_cell))
            except ValueError:
                return None

    # 헤더를 못 읽은 경우에도 '지급' 키워드 이후의 날짜/금액만 사용
    pay_idx = next((i for i, c in enumerate(cells) if str(c).replace(" ", "") == "지급"), None)
    if pay_idx is not None:
        date_cell = next((c for c in cells[pay_idx + 1 :] if DATE_PATTERN.search(c)), None)
        amount_cell = next((c for c in cells[pay_idx + 1 :] if _looks_like_amount(c)), None)
        if date_cell and amount_cell:
            try:
                return Transaction(parse_date(date_cell), parse_amount(amount_cell))
            except ValueError:
                return None

    return None

def _parse_tx_from_text_line(line: str) -> Transaction | None:
    compact = line.replace(" ", "")

    # "지급 일자 2024-11-19 금액 45,340" 형태 우선 처리
    labeled = re.search(
        r"지급(?:일자)?\s*[:：]?\s*(\d{4}[./-]\d{1,2}[./-]\d{1,2}).{0,20}?금액\s*[:：]?\s*(-?\d[\d,]*)",
        compact,
    )
    if labeled:
        try:
            return Transaction(parse_date(labeled.group(1)), parse_amount(labeled.group(2)))
        except ValueError:
            return None

    # 요청사항: '선지급' 제외, 독립된 '지급' 뒤의 날짜/금액만 합산
    if "선지급" in compact:
        return None

    standalone_pay = re.search(r"(?:^|\s|\[)지급(?:\s|\]|$)", line)
    if standalone_pay:
        after_pay = line[standalone_pay.end() :]
        pay_date = DATE_PATTERN.search(after_pay)
        pay_amount = AMOUNT_TOKEN_PATTERN.search(after_pay[pay_date.end() :] if pay_date else after_pay)
        if pay_date and pay_amount:
            try:
                return Transaction(parse_date(pay_date.group(0)), parse_amount(pay_amount.group(0)))
            except ValueError:
                return None

    return None

def _extract_transactions_from_text(text: str) -> list[Transaction]:
    transactions: list[Transaction] = []
    for line in text.splitlines():
        tx = _parse_tx_from_text_line(line)
        if tx:
            transactions.append(tx)
    return transactions


def _extract_transactions_with_ocr(pdf_path: str | Path) -> list[Transaction]:
    try:
        from pdf2image import convert_from_path
        import pytesseract
    except Exception:
        return []

    transactions: list[Transaction] = []

    try:
        images = convert_from_path(str(pdf_path), dpi=300)
    except Exception:
        return []

    for image in images:
        text = ""
        try:
            text = pytesseract.image_to_string(image, lang="kor+eng")
        except Exception:
            try:
                text = pytesseract.image_to_string(image, lang="eng")
            except Exception:
                text = ""

        if text:
            transactions.extend(_extract_transactions_from_text(text))

    return transactions


def extract_transactions_from_pdf(pdf_path: str | Path, enable_ocr_fallback: bool = True) -> list[Transaction]:
    transactions: list[Transaction] = []

    import pdfplumber

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            page_transactions: list[Transaction] = []
            tables = page.extract_tables() or []

            for table in tables:
                if not table:
                    continue

                header = [str(cell).strip() if cell is not None else "" for cell in table[0]]
                rows = table[1:] if any(header) else table

                for row in rows:
                    if not row:
                        continue
                    tx = _parse_tx_from_row(row, header)
                    if tx:
                        page_transactions.append(tx)

            if not page_transactions:
                page_text = page.extract_text() or ""
                page_transactions.extend(_extract_transactions_from_text(page_text))

            transactions.extend(page_transactions)

    if not transactions and enable_ocr_fallback:
        transactions = _extract_transactions_with_ocr(pdf_path)

    return transactions


def summarize_monthly_amount(transactions: Iterable[Transaction]) -> dict[str, int]:
    summary: dict[str, int] = defaultdict(int)
    for tx in transactions:
        month_key = tx.transaction_date.strftime("%Y-%m")
        summary[month_key] += tx.amount
    return dict(sorted(summary.items()))
