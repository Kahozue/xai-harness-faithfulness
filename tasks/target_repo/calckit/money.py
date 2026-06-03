"""金額字串處理。"""
from __future__ import annotations


def parse_amount(s: str) -> float:
    """把 '$1,234.50' 解析成 1234.50。"""
    cleaned = s.replace("$", "").replace(",", "").strip()
    return float(cleaned)


def format_amount(value: float) -> str:
    """把 1234.5 格式化成 '$1,234.50'。"""
    return f"${value:,.2f}"
