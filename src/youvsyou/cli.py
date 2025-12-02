from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from .models import DayLog, DaySummary, Trade, parse_date
from .storage import Journal, load_rules


DEFAULT_JOURNAL = Path("data/journal.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="You vs You trading journal")
    parser.add_argument(
        "--journal",
        type=Path,
        default=DEFAULT_JOURNAL,
        help="Path to the journal JSON file (default: data/journal.json)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # init
    init_parser = subparsers.add_parser("init", help="Initialize a new journal with rules")
    init_parser.add_argument("--rules", type=Path, required=True, help="Path to rules JSON file")

    # rules
    subparsers.add_parser("rules", help="List configured rules")

    # add-day
    add_day_parser = subparsers.add_parser("add-day", help="Log a trading day")
    add_day_parser.add_argument("--date", required=True, help="Trading date (YYYY-MM-DD)")
    add_day_parser.add_argument("--trades", type=Path, required=True, help="Trades JSON file")
    add_day_parser.add_argument("--notes", help="Optional notes for the day")

    # compare
    compare_parser = subparsers.add_parser("compare", help="Compare actual vs perfect for a date")
    compare_parser.add_argument("--date", required=True, help="Trading date (YYYY-MM-DD)")

    # summary
    summary_parser = subparsers.add_parser("summary", help="Roll up discipline gaps")
    summary_parser.add_argument(
        "--period",
        required=True,
        choices=["day", "week", "month", "year"],
        help="Aggregation period",
    )

    return parser


def load_trades_file(path: Path) -> List[Trade]:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    trades = []
    for raw in payload.get("trades", []):
        trades.append(
            Trade(
                symbol=raw["symbol"],
                actual_pnl=float(raw["actual_pnl"]),
                planned_pnl=float(raw["planned_pnl"]),
                violated_rules=list(raw.get("violated_rules", [])),
                notes=raw.get("notes"),
            )
        )
    return trades


def load_or_init_journal(path: Path) -> Journal:
    journal = Journal(path)
    if path.exists():
        journal.load()
    return journal


def cmd_init(args: argparse.Namespace) -> None:
    journal = Journal(args.journal)
    rules = load_rules(args.rules)
    if not rules:
        raise SystemExit("Rule list is empty; add at least one rule")
    journal.set_rules(rules)
    journal.save()
    print(f"Initialized journal at {args.journal}")


def cmd_rules(args: argparse.Namespace) -> None:
    journal = load_or_init_journal(args.journal)
    if not journal.rules:
        print("No rules configured")
        return
    for rule in journal.rules.values():
        print(f"[{rule.id}] {rule.name} - {rule.description} ({rule.category or 'uncategorized'})")


def cmd_add_day(args: argparse.Namespace) -> None:
    journal = load_or_init_journal(args.journal)
    trades = load_trades_file(args.trades)
    if not trades:
        raise SystemExit("No trades provided")

    day_log = DayLog(date=parse_date(args.date), trades=trades, notes=args.notes)
    summary = journal.add_day(day_log)
    journal.save()

    print("Saved day:")
    print(json.dumps(_summary_to_dict(summary), indent=2))


def cmd_compare(args: argparse.Namespace) -> None:
    journal = load_or_init_journal(args.journal)
    day = journal.find_day(parse_date(args.date))
    if not day:
        raise SystemExit(f"No entry for {args.date}. Add it with 'add-day'.")
    print(json.dumps(_summary_to_dict(day), indent=2))


def cmd_summary(args: argparse.Namespace) -> None:
    journal = load_or_init_journal(args.journal)
    rollup = journal.rollup(args.period)
    print(json.dumps(rollup, indent=2))


def _summary_to_dict(summary: DaySummary) -> Dict[str, Any]:
    return {
        "date": summary.date.isoformat(),
        "actual_total": summary.actual_total,
        "perfect_total": summary.perfect_total,
        "discipline_gap": summary.discipline_gap,
        "rule_impacts": summary.rule_impacts,
    }


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = args.command
    if command == "init":
        cmd_init(args)
    elif command == "rules":
        cmd_rules(args)
    elif command == "add-day":
        cmd_add_day(args)
    elif command == "compare":
        cmd_compare(args)
    elif command == "summary":
        cmd_summary(args)
    else:
        parser.error(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
