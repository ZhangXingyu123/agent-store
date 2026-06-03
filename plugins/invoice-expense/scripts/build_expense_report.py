#!/usr/bin/env python3
"""Build a reimbursement CSV from simple invoice CSV or JSON input."""

from __future__ import annotations

import argparse
import csv
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


ALIASES = {
    "invoice_no": ["invoice_no", "invoice_number", "number", "发票号码", "发票号", "票号"],
    "date": ["date", "invoice_date", "开票日期", "日期"],
    "seller": ["seller", "vendor", "merchant", "销售方", "商家", "供应商"],
    "amount": ["amount", "subtotal", "金额", "不含税金额"],
    "tax": ["tax", "tax_amount", "税额"],
    "total": ["total", "total_amount", "价税合计", "合计", "总额"],
    "currency": ["currency", "币种"],
    "reimbursee": ["reimbursee", "employee", "报销人", "员工"],
    "category": ["category", "expense_category", "类别", "费用类别"],
    "note": ["note", "memo", "备注"],
}

OUTPUT_COLUMNS = [
    "line_no",
    "invoice_no",
    "date",
    "seller",
    "category",
    "amount",
    "tax",
    "total",
    "currency",
    "reimbursee",
    "note",
    "warnings",
]


def parse_money(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    text = str(value).strip()
    if not text:
        return Decimal("0")
    text = re.sub(r"[^0-9.\-]", "", text)
    if text in {"", "-", "."}:
        return Decimal("0")
    try:
        return Decimal(text)
    except InvalidOperation:
        return Decimal("0")


def format_money(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01'))}"


def canonicalize(row: dict[str, Any]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    lower_map = {str(key).strip().lower(): value for key, value in row.items()}
    original_map = {str(key).strip(): value for key, value in row.items()}

    for target, aliases in ALIASES.items():
        value = ""
        for alias in aliases:
            if alias in original_map:
                value = original_map[alias]
                break
            if alias.lower() in lower_map:
                value = lower_map[alias.lower()]
                break
        normalized[target] = "" if value is None else str(value).strip()

    amount = parse_money(normalized["amount"])
    tax = parse_money(normalized["tax"])
    total = parse_money(normalized["total"])
    if total == 0 and (amount != 0 or tax != 0):
        total = amount + tax

    normalized["amount"] = format_money(amount)
    normalized["tax"] = format_money(tax)
    normalized["total"] = format_money(total)
    normalized["currency"] = normalized["currency"] or "CNY"
    return normalized


def read_input(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".json":
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, dict):
            payload = payload.get("invoices", [])
        if not isinstance(payload, list):
            raise ValueError("JSON input must be an array or an object with an 'invoices' array.")
        return [item for item in payload if isinstance(item, dict)]

    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def build_report(rows: list[dict[str, Any]]) -> tuple[list[dict[str, str]], dict[str, Any]]:
    seen_invoice_numbers: set[str] = set()
    output_rows: list[dict[str, str]] = []
    warnings: list[str] = []
    total_amount = Decimal("0")

    for index, row in enumerate(rows, start=1):
        normalized = canonicalize(row)
        row_warnings: list[str] = []
        invoice_no = normalized["invoice_no"]

        if not invoice_no:
            row_warnings.append("missing invoice_no")
        elif invoice_no in seen_invoice_numbers:
            row_warnings.append("duplicate invoice_no")
        else:
            seen_invoice_numbers.add(invoice_no)

        for field in ("date", "seller"):
            if not normalized[field]:
                row_warnings.append(f"missing {field}")

        if parse_money(normalized["total"]) == 0:
            row_warnings.append("missing total")

        total_amount += parse_money(normalized["total"])
        warnings.extend([f"line {index}: {item}" for item in row_warnings])
        normalized["line_no"] = str(index)
        normalized["warnings"] = "; ".join(row_warnings)
        output_rows.append({column: normalized.get(column, "") for column in OUTPUT_COLUMNS})

    summary = {
        "invoice_count": len(output_rows),
        "total": format_money(total_amount),
        "currency": "CNY",
        "warnings": warnings,
    }
    return output_rows, summary


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input CSV or JSON file.")
    parser.add_argument("--output", required=True, help="Output reimbursement CSV file.")
    parser.add_argument("--summary", help="Optional output summary JSON file.")
    args = parser.parse_args()

    rows = read_input(Path(args.input))
    output_rows, summary = build_report(rows)
    write_csv(Path(args.output), output_rows)

    if args.summary:
        summary_path = Path(args.summary)
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        with summary_path.open("w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2, ensure_ascii=False)
            handle.write("\n")

    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()

