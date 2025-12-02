from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .analysis import DayComparer, Rollup, deserialize_day_log, serialize_day_summary
from .models import DayLog, DaySummary, Rule


class Journal:
    """Manage the persistent trading journal."""

    def __init__(self, path: Path):
        self.path = path
        self.rules: Dict[str, Rule] = {}
        self.days: List[DaySummary] = []

    # Loading / saving -----------------------------------------------------
    def load(self) -> None:
        if not self.path.exists():
            raise FileNotFoundError(f"Journal not found: {self.path}")

        with self.path.open("r", encoding="utf-8") as f:
            payload = json.load(f)

        self.rules = {rule["id"]: Rule(**rule) for rule in payload.get("rules", [])}
        self.days = [self._deserialize_day(day) for day in payload.get("days", [])]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "rules": [asdict(rule) for rule in self.rules.values()],
            "days": [serialize_day_summary(day) for day in self.days],
        }
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def _deserialize_day(self, raw: Dict) -> DaySummary:
        day_log = deserialize_day_log(raw)
        # Preserve computed fields if they already exist, otherwise recompute.
        if {
            "actual_total",
            "perfect_total",
            "discipline_gap",
            "rule_impacts",
        }.issubset(raw.keys()):
            return DaySummary(
                date=day_log.date,
                actual_total=float(raw["actual_total"]),
                perfect_total=float(raw["perfect_total"]),
                discipline_gap=float(raw["discipline_gap"]),
                rule_impacts={k: float(v) for k, v in raw.get("rule_impacts", {}).items()},
                trades=day_log.trades,
                notes=day_log.notes,
            )
        return DayComparer.summarize(day_log)

    # Rule management ------------------------------------------------------
    def set_rules(self, rules: Iterable[Rule]) -> None:
        self.rules = {rule.id: rule for rule in rules}

    # Day management -------------------------------------------------------
    def add_day(self, day: DayLog) -> DaySummary:
        summary = DayComparer.summarize(day)
        self.days = [d for d in self.days if d.date != summary.date]
        self.days.append(summary)
        self.days.sort(key=lambda d: d.date)
        return summary

    # Queries --------------------------------------------------------------
    def find_day(self, target_date: date) -> Optional[DaySummary]:
        for day in self.days:
            if day.date == target_date:
                return day
        return None

    def rollup(self, period: str) -> Dict[str, float]:
        roller = Rollup(self.days)
        if period == "day":
            return roller.by_day()
        if period == "week":
            return roller.by_week()
        if period == "month":
            return roller.by_month()
        if period == "year":
            return roller.by_year()
        raise ValueError("Period must be one of: day, week, month, year")


def load_rules(path: Path) -> List[Rule]:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    return [Rule(**rule) for rule in payload.get("rules", [])]


def load_trades(path: Path) -> List[DayLog]:
    # Utility kept for future expansion; not used directly.
    raise NotImplementedError
