---
name: invoice-expense
description: Use when the user wants to turn invoices, receipts, invoice OCR text, or invoice CSV/JSON data into an expense reimbursement table. Trigger on invoice, receipt, reimbursement, expense report, bill整理, 发票, 票据, 报销, 报销单, and 费用明细. Do not use for unrelated tax, accounting, or legal advice.
---

# Invoice Expense

Use this skill to help the user convert invoice data into a reimbursement table.

## What this demo skill does

- Accepts already-extracted invoice fields in CSV or JSON.
- Generates a normalized reimbursement CSV.
- Detects duplicate invoice numbers.
- Warns about missing dates, sellers, and totals.

This minimal demo does not run OCR on image or PDF files. If the user provides raw images or PDFs, explain that the production version would call an OCR or invoice-recognition MCP/API first, then run the table-generation step.

## Inputs

Prefer one of these inputs:

- CSV with columns such as `invoice_no`, `date`, `seller`, `amount`, `tax`, `total`, `currency`, `reimbursee`, `category`, `note`.
- JSON array with equivalent fields.
- Chinese column aliases are supported by the demo script, including `发票号码`, `日期`, `销售方`, `金额`, `税额`, `价税合计`, `报销人`, `类别`, `备注`.

## Workflow

1. Confirm the user wants a reimbursement table.
2. If the user supplied invoice images or PDFs, first extract invoice fields with available OCR/tooling. If no OCR tool is available, ask the user for OCR text or a CSV/JSON export.
3. Run the helper script from the plugin root:

```bash
python3 plugins/invoice-expense/scripts/build_expense_report.py --input <input.csv-or-json> --output <expense-report.csv> --summary <summary.json>
```

When running from inside the plugin skill directory, the script is at `../../scripts/build_expense_report.py`.

4. Return the output CSV path, total reimbursement amount, duplicate invoice warnings, and any missing-field warnings.
5. If the user needs Excel, convert the CSV to XLSX with available spreadsheet tooling.

## Output

Return:

- `expense-report.csv`
- optional `summary.json`
- a short explanation of totals and warnings

