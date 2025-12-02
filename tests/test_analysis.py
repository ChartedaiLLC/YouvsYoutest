from datetime import date

from youvsyou.analysis import DayComparer, Rollup
from youvsyou.models import DayLog, Trade


def test_day_comparer_calculates_gap_and_rule_impacts():
    day = DayLog(
        date=date(2024, 12, 2),
        trades=[
            Trade(symbol="AAPL", actual_pnl=-150.0, planned_pnl=120.0, violated_rules=["setup-01"]),
            Trade(symbol="MSFT", actual_pnl=320.0, planned_pnl=320.0),
            Trade(symbol="TSLA", actual_pnl=-75.0, planned_pnl=0.0, violated_rules=["risk-02"]),
        ],
        notes="Example day",
    )

    summary = DayComparer.summarize(day)

    assert summary.actual_total == 95.0
    assert summary.perfect_total == 440.0
    assert summary.discipline_gap == 345.0
    assert summary.rule_impacts == {"setup-01": 270.0, "risk-02": 75.0}


def test_rollup_groups_by_period():
    day1 = DayComparer.summarize(
        DayLog(
            date=date(2024, 12, 2),
            trades=[Trade(symbol="AAPL", actual_pnl=10, planned_pnl=20, violated_rules=["a"])],
        )
    )
    day2 = DayComparer.summarize(
        DayLog(
            date=date(2024, 12, 3),
            trades=[Trade(symbol="MSFT", actual_pnl=5, planned_pnl=8, violated_rules=["b"])],
        )
    )

    roll = Rollup([day1, day2])
    assert roll.by_day() == {"2024-12-02": 10.0, "2024-12-03": 3.0}
    assert roll.by_week()["2024-W49"] == 13.0
    assert roll.by_month()["2024-12"] == 13.0
    assert roll.by_year()["2024"] == 13.0
