"""연/월 산술 헬퍼 (datetime 의존 없이 (year, month) 튜플로 처리)."""

from __future__ import annotations


def month_index(year: int, month: int) -> int:
    """비교/정렬용 절대 월 인덱스."""
    return year * 12 + (month - 1)


def from_index(idx: int) -> tuple[int, int]:
    return idx // 12, idx % 12 + 1


def add_months(year: int, month: int, delta: int) -> tuple[int, int]:
    return from_index(month_index(year, month) + delta)


def ym_label(year: int, month: int) -> str:
    return f"{year}-{month:02d}"
