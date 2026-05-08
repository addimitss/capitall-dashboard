"""Cross-sheet analytics: AML-specific insights (rating mix, top risks, mismatches, alerts)."""
from __future__ import annotations
from typing import Any
import math
import pandas as pd
from .excel_service import _safe, numeric_columns


def _g(df: pd.DataFrame | None, col: str) -> pd.Series:
    if df is None or col not in df.columns:
        return pd.Series(dtype=object)
    return df[col]


def overview(sheets: dict[str, pd.DataFrame]) -> dict[str, Any]:
    """Workbook-wide KPIs combining several sheets. Best-effort; gracefully degrades."""
    rrs = sheets.get("Risk Rating Summary")
    cm = sheets.get("Customer Master")
    txn = sheets.get("Transactions")
    media = sheets.get("Adverse Media")
    kyc = sheets.get("KYC Documents")
    agg = sheets.get("Aggregation Check")

    cards: list[dict[str, Any]] = []
    charts: list[dict[str, Any]] = []
    alerts: list[dict[str, Any]] = []

    # Customer count
    n_cust = len(cm) if cm is not None else (len(rrs) if rrs is not None else 0)
    cards.append({"label": "Customers", "value": int(n_cust)})

    # Total txns + volume
    if txn is not None and len(txn):
        cards.append({"label": "Transactions", "value": int(len(txn))})
        if "Amount ₹" in txn.columns:
            vol = pd.to_numeric(txn["Amount ₹"], errors="coerce").sum()
            cards.append({"label": "Total Volume ₹", "value": _safe(vol)})
        if "Is Cash" in txn.columns:
            cash_pct = (txn["Is Cash"].astype(str).str.lower() == "yes").mean()
            cards.append({"label": "Cash Txn %", "value": _safe(round(float(cash_pct) * 100, 2))})
        if "Is Offshore" in txn.columns:
            off = (txn["Is Offshore"].astype(str).str.lower() == "yes").sum()
            cards.append({"label": "Offshore Txns", "value": int(off)})

    # Adverse media
    if media is not None and len(media):
        cards.append({"label": "Adverse Media Hits", "value": int(len(media))})

    # Rating mix + top risk
    if rrs is not None and "Rating" in rrs.columns:
        vc = rrs["Rating"].astype(str).value_counts().to_dict()
        cards.append({"label": "Rating Mix", "value": {k: int(v) for k, v in vc.items()}})
        charts.append({
            "type": "pie", "title": "Customer Rating Distribution",
            "data": [{"name": k, "value": int(v)} for k, v in vc.items()],
        })
        # High/Critical alert
        crit_ratings = {"High", "Critical"}
        flagged = rrs[rrs["Rating"].astype(str).isin(crit_ratings)]
        if len(flagged):
            alerts.append({
                "severity": "high",
                "title": f"{len(flagged)} customers rated High/Critical",
                "detail": f"Review immediately. Top score: {float(flagged['Final AML Score'].max()):.1f}"
                          if "Final AML Score" in flagged.columns else "Review immediately.",
            })

    # Top 10 highest-risk customers
    top_risks: list[dict[str, Any]] = []
    if rrs is not None and "Final AML Score" in rrs.columns:
        cols = [c for c in ["Cust ID", "Customer", "Country", "Rating", "Final AML Score", "PEP"] if c in rrs.columns]
        top = rrs.sort_values("Final AML Score", ascending=False).head(10)[cols]
        top_risks = [{k: _safe(v) for k, v in r.items()} for r in top.to_dict(orient="records")]

    # Avg AML score by country
    if rrs is not None and "Country" in rrs.columns and "Final AML Score" in rrs.columns:
        by_country = (
            rrs.groupby(rrs["Country"].astype(str))["Final AML Score"]
               .mean().sort_values(ascending=False).head(10)
        )
        charts.append({
            "type": "bar",
            "title": "Avg AML Score by Country (top 10)",
            "xKey": "Country", "yKey": "Score",
            "data": [{"Country": k, "Score": _safe(round(float(v), 2))} for k, v in by_country.items()],
        })

    # Monthly transaction volume trend
    if txn is not None and "Date" in txn.columns and "Amount ₹" in txn.columns:
        try:
            tmp = pd.DataFrame({
                "_dt": pd.to_datetime(txn["Date"], errors="coerce", dayfirst=True),
                "amt": pd.to_numeric(txn["Amount ₹"], errors="coerce"),
            }).dropna()
            if not tmp.empty:
                tmp["m"] = tmp["_dt"].dt.to_period("M").dt.to_timestamp()
                ts = tmp.groupby("m")["amt"].sum().sort_index()
                charts.append({
                    "type": "line", "title": "Transaction Volume — Monthly",
                    "xKey": "period", "yKey": "Amount",
                    "data": [{"period": p.strftime("%Y-%m"), "Amount": _safe(float(v))} for p, v in ts.items()],
                })
        except Exception:
            pass

    # KYC completion alert
    if kyc is not None and "Status" in kyc.columns:
        verified = (kyc["Status"].astype(str).str.lower() == "verified").mean()
        cards.append({"label": "KYC Verified %", "value": _safe(round(float(verified) * 100, 2))})
        if verified < 0.9:
            alerts.append({
                "severity": "medium",
                "title": f"KYC verification at {verified*100:.1f}%",
                "detail": "Below 90% threshold. Review Customer Master + KYC Documents.",
            })

    # Aggregation Check vs RRS mismatches
    mm = mismatches(sheets)
    if mm["count"]:
        alerts.append({
            "severity": "medium",
            "title": f"{mm['count']} customers with Risk Summary vs Aggregation mismatches",
            "detail": "See 'Aggregation Check' tab or ask the assistant for details.",
        })

    return {
        "cards": cards,
        "charts": charts,
        "alerts": alerts,
        "top_risks": top_risks,
    }


def mismatches(sheets: dict[str, pd.DataFrame], tolerance: float = 0.01) -> dict[str, Any]:
    """Compare Risk Rating Summary vs Aggregation Check on shared metrics."""
    rrs = sheets.get("Risk Rating Summary")
    agg = sheets.get("Aggregation Check")
    if rrs is None or agg is None or "Cust ID" not in rrs.columns or "Cust ID" not in agg.columns:
        return {"count": 0, "rows": [], "checked": 0, "fields": []}

    # Map RRS cols -> Aggregation Check cols
    pairs = [
        ("Cash %", "Cash %"),
        ("KYC %", "KYC %"),
        ("Offshore Txns", "Offshore Txns"),
        ("Linked Accts", "Linked Accts"),
        ("Corp Action Trades", "Corp Action Trades"),
        ("Penny Stock %", None),  # derive from Aggregation Check if Penny Stock Trades / Total Txns ratio available
        ("Media Hits", "Media Hits"),
    ]

    merged = rrs.merge(agg, on="Cust ID", suffixes=(" (sum)", " (agg)"))

    diffs: list[dict[str, Any]] = []
    fields_checked: list[str] = []

    for left, right in pairs:
        if right is None:
            continue
        l_col = left + " (sum)" if left in rrs.columns and left in agg.columns else left
        r_col = right + " (agg)" if right in rrs.columns and right in agg.columns else right
        if l_col not in merged.columns or r_col not in merged.columns:
            continue
        fields_checked.append(left)
        l = pd.to_numeric(merged[l_col], errors="coerce")
        r = pd.to_numeric(merged[r_col], errors="coerce")
        delta = (l - r).abs()
        # tolerance: relative for fractional fields, absolute for counts
        if "%" in left:
            mismatched = (delta > tolerance)
        else:
            mismatched = (delta > 0)
        for idx in merged.index[mismatched.fillna(False)]:
            diffs.append({
                "Cust ID": str(merged.at[idx, "Cust ID"]),
                "Field": left,
                "Summary": _safe(merged.at[idx, l_col]),
                "Aggregation": _safe(merged.at[idx, r_col]),
                "Delta": _safe(float(delta.at[idx])) if not math.isnan(float(delta.at[idx])) else None,
            })

    # group by Cust ID for output
    by_cust: dict[str, list[dict[str, Any]]] = {}
    for d in diffs:
        by_cust.setdefault(d["Cust ID"], []).append(d)

    return {
        "count": len(by_cust),
        "checked": int(len(merged)),
        "fields": fields_checked,
        "rows": [{"Cust ID": k, "issues": v} for k, v in list(by_cust.items())[:100]],
    }
