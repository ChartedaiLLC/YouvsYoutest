from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from datetime import date
from typing import Dict, Iterable, List

from .models import DayLog, DaySummary, Trade


class DayComparer:
    """Compare actual trades against a perfect rule-following baseline."""

    @staticmethod
    def summarize(day: DayLog) -> DaySummary:
        actual_total = sum(t.actual_pnl for t in day.trades)
        perfect_total = sum(t.planned_pnl for t in day.trades)
        discipline_gap = perfect_total - actual_total

        rule_impacts: Dict[str, float] = defaultdict(float)
        for trade in day.trades:
            delta = trade.planned_pnl - trade.actual_pnl
            for rule_id in trade.violated_rules:
                rule_impacts[rule_id] += delta

        return DaySummary(
            date=day.date,
            actual_total=actual_total,
            perfect_total=perfect_total,
            discipline_gap=discipline_gap,
            rule_impacts=dict(rule_impacts),
            trades=day.trades,
            notes=day.notes,
        )


class Rollup:
    """Aggregate performance over configurable periods."""

    def __init__(self, days: Iterable[DaySummary]):
        self.days = list(days)

    def by_day(self) -> Dict[str, float]:
        return {day.date.isoformat(): day.discipline_gap for day in self.days}

    def by_week(self) -> Dict[str, float]:
        rollup: Dict[str, float] = defaultdict(float)
        for day in self.days:
            rollup[day.iso_year_week] += day.discipline_gap
        return dict(rollup)

    def by_month(self) -> Dict[str, float]:
        rollup: Dict[str, float] = defaultdict(float)
        for day in self.days:
            rollup[day.month_key] += day.discipline_gap
        return dict(rollup)

    def by_year(self) -> Dict[str, float]:
        rollup: Dict[str, float] = defaultdict(float)
        for day in self.days:
            rollup[day.year_key] += day.discipline_gap
        return dict(rollup)


def serialize_day_summary(day: DaySummary) -> Dict:
    """Serialize a DaySummary to a JSON-friendly dict."""

    payload = asdict(day)
    payload["date"] = day.date.isoformat()
    # Dataclasses do not automatically convert nested date objects; trades are already serializable.
    return payload


def deserialize_trade(raw: Dict) -> Trade:
    return Trade(
        symbol=raw["symbol"],
        actual_pnl=float(raw["actual_pnl"]),
        planned_pnl=float(raw["planned_pnl"]),
        violated_rules=list(raw.get("violated_rules", [])),
        notes=raw.get("notes"),
    )


def deserialize_day_log(raw: Dict) -> DayLog:
    return DayLog(
        date=date.fromisoformat(raw["date"]),
        trades=[deserialize_trade(t) for t in raw.get("trades", [])],
        notes=raw.get("notes"),
    )
