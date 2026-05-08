from __future__ import annotations
import io
import math
import re
from typing import Any
import numpy as np
import pandas as pd


# ---------- Parsing ----------

def parse_workbook(content: bytes) -> dict[str, pd.DataFrame]:
    """Parse all sheets from an uploaded Excel file. Raises ValueError on invalid input."""
    try:
        xl = pd.ExcelFile(io.BytesIO(content), engine="openpyxl")
    except Exception as e:
        raise ValueError(f"Unable to read Excel file: {e}") from e
    if not xl.sheet_names:
        raise ValueError("Workbook contains no sheets.")
    sheets: dict[str, pd.DataFrame] = {}
    for name in xl.sheet_names:
        df = pd.read_excel(xl, sheet_name=name, dtype=object)
        df = _coerce_types(df)
        sheets[name] = df
    return sheets


def _coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    """Best-effort type coercion: numeric where possible, else string. Keeps NaNs."""
    out = pd.DataFrame()
    for col in df.columns:
        s = df[col]
        # try numeric
        num = pd.to_numeric(s, errors="coerce")
        non_null = s.notna().sum()
        if non_null > 0 and num.notna().sum() / max(non_null, 1) >= 0.9:
            out[col] = num
        else:
            out[col] = s.astype(object).where(s.notna(), None)
    return out


# ---------- JSON-safe helpers ----------

def _safe(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    if isinstance(v, (np.floating,)):
        f = float(v)
        return None if (math.isnan(f) or math.isinf(f)) else f
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.bool_,)):
        return bool(v)
    if isinstance(v, pd.Timestamp):
        return v.isoformat()
    return v


def df_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    rows = df.to_dict(orient="records")
    return [{k: _safe(v) for k, v in r.items()} for r in rows]


def column_kind(s: pd.Series) -> str:
    if pd.api.types.is_numeric_dtype(s):
        return "number"
    sample = s.dropna().astype(str).head(20)
    if not sample.empty and sample.str.match(r"^\d{1,2}-[A-Za-z]{3}-\d{4}$").all():
        return "date"
    if not sample.empty and sample.str.match(r"^\d{4}-\d{2}-\d{2}").all():
        return "date"
    return "string"


def column_meta(df: pd.DataFrame) -> list[dict[str, str]]:
    return [
        {"name": c, "dtype": str(df[c].dtype), "kind": column_kind(df[c])}
        for c in df.columns
    ]


# ---------- Filtering / sorting / pagination ----------

def apply_query(
    df: pd.DataFrame,
    search: str | None,
    sort_by: str | None,
    sort_dir: str,
    filters: dict[str, Any],
    page: int,
    page_size: int,
) -> tuple[pd.DataFrame, int]:
    out = df

    if filters:
        for col, val in filters.items():
            if col not in out.columns or val in (None, "", []):
                continue
            s = out[col]
            if isinstance(val, dict) and ("min" in val or "max" in val):
                ser = pd.to_numeric(s, errors="coerce")
                if val.get("min") is not None:
                    out = out[ser >= float(val["min"])]
                if val.get("max") is not None:
                    out = out[ser <= float(val["max"])]
            elif isinstance(val, list):
                out = out[s.isin(val)]
            else:
                out = out[s.astype(str).str.contains(str(val), case=False, na=False)]

    if search:
        mask = pd.Series(False, index=out.index)
        for col in out.columns:
            mask = mask | out[col].astype(str).str.contains(search, case=False, na=False)
        out = out[mask]

    total = len(out)

    if sort_by and sort_by in out.columns:
        out = out.sort_values(by=sort_by, ascending=(sort_dir == "asc"), kind="mergesort", na_position="last")

    start = (page - 1) * page_size
    end = start + page_size
    return out.iloc[start:end], total


# ---------- Auto summary / charts ----------

_AMOUNT_RE = re.compile(r"(amount|value|volume|score|txn|count|hits|trades|qty|quantity|price)", re.I)
_RATING_HINT = ("Rating", "Severity", "Status", "Risk Flag", "Category", "Country", "Customer Type", "Industry", "Channel", "Type")


def numeric_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]


def categorical_columns(df: pd.DataFrame, max_card: int = 30) -> list[str]:
    cats = []
    for c in df.columns:
        if pd.api.types.is_numeric_dtype(df[c]):
            continue
        nun = df[c].nunique(dropna=True)
        if 1 < nun <= max_card:
            cats.append(c)
    return cats


def build_summary(sheet_name: str, df: pd.DataFrame) -> dict[str, Any]:
    cards: list[dict[str, Any]] = [{"label": "Rows", "value": int(len(df))}]
    nums = numeric_columns(df)

    # Heuristic monetary/score cards
    money_like = [c for c in nums if _AMOUNT_RE.search(c)]
    for c in money_like[:5]:
        s = df[c].dropna()
        if s.empty:
            continue
        cards.append({"label": f"Sum {c}", "value": _safe(s.sum())})
        cards.append({"label": f"Avg {c}", "value": _safe(round(float(s.mean()), 2))})

    # Top categorical breakdown for a card (e.g. Rating distribution)
    for c in df.columns:
        if c in _RATING_HINT and not pd.api.types.is_numeric_dtype(df[c]):
            vc = df[c].astype(str).value_counts().head(5).to_dict()
            cards.append({"label": f"{c} breakdown", "value": {k: int(v) for k, v in vc.items()}})
            break

    charts: list[dict[str, Any]] = []

    # Pie/bar of first low-cardinality categorical
    cats = categorical_columns(df)
    if cats:
        cat = cats[0]
        vc = df[cat].astype(str).value_counts().head(10)
        charts.append({
            "type": "pie",
            "title": f"{cat} distribution",
            "data": [{"name": k, "value": int(v)} for k, v in vc.items()],
        })

    # Bar of numeric mean by first categorical
    if cats and nums:
        cat = cats[0]
        num = next((n for n in nums if _AMOUNT_RE.search(n)), nums[0])
        agg = df.groupby(df[cat].astype(str))[num].mean().sort_values(ascending=False).head(10)
        charts.append({
            "type": "bar",
            "title": f"Avg {num} by {cat}",
            "xKey": cat,
            "yKey": num,
            "data": [{cat: k, num: _safe(round(float(v), 2))} for k, v in agg.items()],
        })

    # Time-series if date column found
    date_col = next((c for c in df.columns if column_kind(df[c]) == "date"), None)
    if date_col and nums:
        try:
            tmp = df[[date_col]].copy()
            tmp["_dt"] = pd.to_datetime(tmp[date_col], errors="coerce", dayfirst=True)
            num = next((n for n in nums if _AMOUNT_RE.search(n)), nums[0])
            tmp[num] = pd.to_numeric(df[num], errors="coerce")
            tmp = tmp.dropna(subset=["_dt", num])
            if not tmp.empty:
                tmp["_period"] = tmp["_dt"].dt.to_period("M").dt.to_timestamp()
                ts = tmp.groupby("_period")[num].sum().sort_index()
                charts.append({
                    "type": "line",
                    "title": f"{num} over time (monthly)",
                    "xKey": "period",
                    "yKey": num,
                    "data": [{"period": p.strftime("%Y-%m"), num: _safe(float(v))} for p, v in ts.items()],
                })
        except Exception:
            pass

    return {"sheet": sheet_name, "rows": int(len(df)), "cards": cards, "charts": charts}


# ---------- Chatbot context builder ----------

def build_chat_context(sheets: dict[str, pd.DataFrame], focus: str | None) -> str:
    """Return a compact textual digest of the workbook for LLM grounding."""
    parts: list[str] = []
    parts.append("WORKBOOK OVERVIEW:")
    for name, df in sheets.items():
        parts.append(f"- Sheet '{name}': {len(df)} rows, columns={list(df.columns)}")

    def digest(name: str, df: pd.DataFrame, max_rows: int = 25) -> str:
        nums = numeric_columns(df)
        lines = [f"\n[SHEET: {name}] rows={len(df)}"]
        if nums:
            desc = df[nums].describe().round(3).to_dict()
            lines.append(f"NUMERIC_STATS={desc}")
        cats = categorical_columns(df, max_card=15)
        for c in cats[:4]:
            vc = df[c].astype(str).value_counts().head(8).to_dict()
            lines.append(f"TOP_{c}={vc}")
        sample = df.head(max_rows)
        lines.append(f"SAMPLE_ROWS={df_to_records(sample)}")
        return "\n".join(lines)

    if focus and focus in sheets:
        parts.append(digest(focus, sheets[focus], max_rows=40))
    else:
        for n, d in sheets.items():
            parts.append(digest(n, d, max_rows=10))

    text = "\n".join(parts)
    # cap to keep prompts bounded
    return text[:24000]
