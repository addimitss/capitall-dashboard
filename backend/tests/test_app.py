"""Backend tests. Run: cd backend && pip install pytest httpx && pytest -q"""
from __future__ import annotations
import io
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.state import store
from app.services import excel_service as svc
from app.services import insights_service as ins
from app.services import schema as schema_svc
from app.services import auth as auth_svc

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_store():
    store.clear()
    yield
    store.clear()


def _make_workbook() -> bytes:
    """Build a tiny canonical-format workbook in memory for tests."""
    rrs = pd.DataFrame({
        "Cust ID": ["CUST001", "CUST002", "CUST003"],
        "Customer": ["A", "B", "C"],
        "Country": ["India", "Singapore", "India"],
        "PEP": ["No", "Yes", "No"],
        "Cash %": [0.10, 0.05, 0.30],
        "KYC %": [0.9, 1.0, 0.6],
        "Offshore Txns": [0, 1, 2],
        "Linked Accts": [1, 0, 3],
        "Corp Action Trades": [0, 2, 0],
        "Penny Stock %": [0.0, 0.0, 0.1],
        "Media Hits": [0, 0, 4],
        "Final AML Score": [12.5, 28.0, 65.0],
        "Rating": ["Low", "Medium", "High"],
    })
    cm = pd.DataFrame({
        "Cust ID": ["CUST001", "CUST002", "CUST003"],
        "Customer": ["A", "B", "C"],
        "Country": ["India", "Singapore", "India"],
        "PEP": ["No", "Yes", "No"],
        "Account Open Date": ["01-Jan-2020"] * 3,
        "Customer Type": ["Corporate", "Individual", "Corporate"],
        "Industry": ["Pharma", "IT", "Real Estate"],
    })
    txn = pd.DataFrame({
        "Txn ID": [f"TXN{i}" for i in range(6)],
        "Cust ID": ["CUST001"] * 2 + ["CUST002"] * 2 + ["CUST003"] * 2,
        "Date": ["02-Apr-2026", "18-Apr-2026"] * 3,
        "Amount ₹": [1000, 2000, 5000, 7500, 12000, 30000],
        "Channel": ["NEFT"] * 6,
        "Type": ["Credit"] * 6,
        "Is Cash": ["Yes", "No", "No", "No", "Yes", "Yes"],
        "Is Offshore": ["No", "No", "No", "Yes", "Yes", "No"],
    })
    kyc = pd.DataFrame({
        "Cust ID": ["CUST001", "CUST002", "CUST003"],
        "Document": ["PAN", "PAN", "PAN"],
        "Required": ["Yes"] * 3,
        "Submitted": ["Yes"] * 3,
        "Verified": ["Yes", "Yes", "No"],
        "Status": ["Verified", "Verified", "Pending"],
    })
    nd = pd.DataFrame({
        "Cust ID": ["CUST001"], "Device ID": ["D1"],
        "Linked Account ID": ["-"], "Risk Flag": ["Low"],
    })
    trades = pd.DataFrame({
        "Cust ID": ["CUST001"], "Trade Date": ["12-Apr-2026"],
        "Security": ["X"], "Type": ["Buy"], "Trade Value ₹": [10000],
        "Is Penny Stock": ["No"], "Is Corporate Action": ["No"],
    })
    media = pd.DataFrame({
        "Cust ID": ["CUST003"], "Date": ["29-Apr-2026"], "Source": ["RBI"],
        "Headline": ["Test"], "Category": ["Negative PR"], "Severity": ["Medium"],
    })
    # Aggregation Check intentionally has a mismatch on CUST003 KYC %
    agg = pd.DataFrame({
        "Cust ID": ["CUST001", "CUST002", "CUST003"],
        "Total Txns (calc)": [2, 2, 2],
        "Cash %": [0.10, 0.05, 0.30],
        "KYC %": [0.9, 1.0, 0.5],  # CUST003 differs (0.6 vs 0.5)
    })

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        rrs.to_excel(w, "Risk Rating Summary", index=False)
        cm.to_excel(w, "Customer Master", index=False)
        txn.to_excel(w, "Transactions", index=False)
        kyc.to_excel(w, "KYC Documents", index=False)
        nd.to_excel(w, "Network & Devices", index=False)
        trades.to_excel(w, "Trading Activity", index=False)
        media.to_excel(w, "Adverse Media", index=False)
        agg.to_excel(w, "Aggregation Check", index=False)
    return buf.getvalue()


# ---------- Service-level tests ----------

def test_parse_workbook_roundtrip():
    sheets = svc.parse_workbook(_make_workbook())
    assert "Risk Rating Summary" in sheets
    assert len(sheets["Risk Rating Summary"]) == 3


def test_apply_query_search_sort_paginate():
    sheets = svc.parse_workbook(_make_workbook())
    df = sheets["Risk Rating Summary"]
    sub, total = svc.apply_query(df, "CUST", "Final AML Score", "desc", {}, 1, 2)
    assert total == 3
    assert len(sub) == 2
    assert sub.iloc[0]["Cust ID"] == "CUST003"


def test_schema_validate_loose_warnings():
    sheets = svc.parse_workbook(_make_workbook())
    res = schema_svc.validate(sheets, strict=False)
    assert res["errors"] == []


def test_schema_validate_strict_failure():
    sheets = svc.parse_workbook(_make_workbook())
    sheets.pop("Risk Rating Summary")
    with pytest.raises(ValueError):
        schema_svc.validate(sheets, strict=True)


def test_insights_overview_and_mismatches():
    sheets = svc.parse_workbook(_make_workbook())
    o = ins.overview(sheets)
    assert any(c["label"] == "Customers" for c in o["cards"])
    assert o["top_risks"][0]["Cust ID"] == "CUST003"
    mm = ins.mismatches(sheets)
    assert mm["count"] >= 1
    assert any(r["Cust ID"] == "CUST003" for r in mm["rows"])


# ---------- Auth tests ----------

def test_auth_token_roundtrip():
    tok = auth_svc.issue_token("alice", "analyst", ttl_seconds=60)
    payload = auth_svc.verify_token(tok)
    assert payload["sub"] == "alice"
    assert payload["role"] == "analyst"


def test_auth_bad_signature_rejected():
    tok = auth_svc.issue_token("alice", "analyst", ttl_seconds=60)
    body, _sig = tok.split(".")
    forged = body + "." + "AAAA"
    with pytest.raises(Exception):
        auth_svc.verify_token(forged)


# ---------- HTTP integration tests ----------

def test_health_endpoint():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_upload_rejects_non_xlsx():
    r = client.post("/api/upload", files={"file": ("foo.txt", b"hello", "text/plain")})
    assert r.status_code == 400


def test_full_flow_upload_then_query():
    wb = _make_workbook()
    r = client.post("/api/upload", files={"file": ("test.xlsx", wb,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "Risk Rating Summary" in data["sheets"]

    r = client.get("/api/sheets/Risk Rating Summary/meta")
    assert r.status_code == 200
    assert r.json()["rows"] == 3

    r = client.get("/api/sheets/Risk Rating Summary/summary")
    assert r.status_code == 200
    assert r.json()["rows"] == 3
    assert len(r.json()["cards"]) > 0

    r = client.post("/api/sheets/Risk Rating Summary/data",
                    json={"page": 1, "page_size": 10, "sort_by": "Final AML Score", "sort_dir": "desc"})
    assert r.status_code == 200
    rows = r.json()["rows"]
    assert rows[0]["Cust ID"] == "CUST003"


def test_insights_overview_endpoint():
    wb = _make_workbook()
    client.post("/api/upload", files={"file": ("test.xlsx", wb,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    r = client.get("/api/insights/overview")
    assert r.status_code == 200
    assert r.json()["top_risks"][0]["Cust ID"] == "CUST003"

    r = client.get("/api/insights/mismatches")
    assert r.status_code == 200
    assert r.json()["count"] >= 1


def test_chat_requires_workbook():
    r = client.post("/api/chat", json={"message": "hi"})
    assert r.status_code == 400


def test_auth_config_is_public():
    r = client.get("/api/auth/config")
    assert r.status_code == 200
    assert "auth_enabled" in r.json()
