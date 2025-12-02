from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, List, Optional


@dataclass
class Rule:
    """A trading rule the trader wants to follow."""

    id: str
    name: str
    description: str
    category: Optional[str] = None


@dataclass
class Trade:
    """A single trade with actual and plan-aligned P&L."""

    symbol: str
    actual_pnl: float
    planned_pnl: float
    violated_rules: List[str] = field(default_factory=list)
    notes: Optional[str] = None


@dataclass
class DayLog:
    """Input record for a trading day."""

    date: date
    trades: List[Trade]
    notes: Optional[str] = None


@dataclass
class DaySummary:
    """Computed summary comparing real vs perfect rule adherence."""

    date: date
    actual_total: float
    perfect_total: float
    discipline_gap: float
    rule_impacts: Dict[str, float]
    trades: List[Trade]
    notes: Optional[str] = None

    @property
    def iso_year_week(self) -> str:
        iso_year, iso_week, _ = self.date.isocalendar()
        return f"{iso_year}-W{iso_week:02d}"

    @property
    def month_key(self) -> str:
        return self.date.strftime("%Y-%m")

    @property
    def year_key(self) -> str:
        return self.date.strftime("%Y")


def parse_date(raw: str) -> date:
    return datetime.strptime(raw, "%Y-%m-%d").date()
