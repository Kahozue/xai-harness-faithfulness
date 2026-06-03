"""基本統計。"""
from __future__ import annotations
from typing import Sequence


def mean(xs: Sequence[float]) -> float:
    if not xs:
        raise ValueError("empty sequence")
    return sum(xs) / len(xs)


def median(xs: Sequence[float]) -> float:
    if not xs:
        raise ValueError("empty sequence")
    ordered = sorted(xs)
    n = len(ordered)
    mid = n // 2
    if n % 2 == 1:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2
