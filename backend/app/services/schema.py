"""Optional schema validation for the canonical AML workbook layout.

Set STRICT_SCHEMA=true in env to reject uploads that don't match.
Default is loose (warnings only, in returned metadata) so the dashboard
remains generic for other workbooks.
"""
from __future__ import annotations
import pandas as pd

# Canonical sheet -> required columns (subset; extra columns allowed)
EXPECTED_SCHEMA: dict[str, list[str]] = {
    "Risk Rating Summary": [
        "Cust ID", "Customer", "Country", "PEP", "Final AML Score", "Rating",
    ],
    "Customer Master": [
        "Cust ID", "Customer", "Country", "PEP", "Account Open Date",
        "Customer Type", "Industry",
    ],
    "Transactions": [
        "Txn ID", "Cust ID", "Date", "Amount ₹", "Channel", "Type",
        "Is Cash", "Is Offshore",
    ],
    "KYC Documents": [
        "Cust ID", "Document", "Required", "Submitted", "Verified", "Status",
    ],
    "Network & Devices": [
        "Cust ID", "Device ID", "Linked Account ID", "Risk Flag",
    ],
    "Trading Activity": [
        "Cust ID", "Trade Date", "Security", "Type", "Trade Value ₹",
        "Is Penny Stock", "Is Corporate Action",
    ],
    "Adverse Media": [
        "Cust ID", "Date", "Source", "Headline", "Category", "Severity",
    ],
    "Aggregation Check": [
        "Cust ID", "Total Txns (calc)", "Cash %", "KYC %",
    ],
}


def validate(sheets: dict[str, pd.DataFrame], strict: bool) -> dict[str, list[str]]:
    """Return {'errors': [...], 'warnings': [...]}. Raise ValueError when strict and errors exist."""
    errors: list[str] = []
    warnings: list[str] = []

    missing_sheets = [s for s in EXPECTED_SCHEMA if s not in sheets]
    if missing_sheets:
        msg = f"Missing expected sheets: {missing_sheets}"
        (errors if strict else warnings).append(msg)

    for sheet_name, required_cols in EXPECTED_SCHEMA.items():
        df = sheets.get(sheet_name)
        if df is None:
            continue
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            msg = f"Sheet '{sheet_name}' missing columns: {missing_cols}"
            (errors if strict else warnings).append(msg)

    if strict and errors:
        raise ValueError(" | ".join(errors))

    return {"errors": errors, "warnings": warnings}
