# You vs You - Trading Journal Assistant

You vs You is a lightweight command-line assistant for journaling day-trading performance. It lets you capture the rules you intend to follow, log trades for the day, and compare your real performance against a "perfect" version of yourself that followed every rule. Daily entries roll up into weekly, monthly, and yearly metrics so you can see how much edge is being left on the table when rules are missed.

## Concepts
- **Rules**: The checklist you want to follow every session. Each rule can include a description and category (risk, execution, sizing, etc.).
- **Trades**: Every trade captures real P&L plus the P&L you would have earned if the trade had been executed exactly according to plan. Any violated rules are listed so the tool can highlight where discipline slipped.
- **Journal**: A JSON file (`data/journal.json` by default) that stores rules and each trading day with summary metrics.

## Quick start
1. Install dependencies (standard library only):
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

2. Seed the journal with your rules:
   ```bash
   youvsyou init --rules sample/rules.json
   ```

3. Log a trading day with your trades and which rules you broke:
   ```bash
   youvsyou add-day --date 2024-12-02 --trades sample/trades_2024-12-02.json
   ```

4. Compare your results against the perfect-rule-following version of you:
   ```bash
   youvsyou compare --date 2024-12-02
   ```

5. Review rollups by period:
   ```bash
   youvsyou summary --period month
   ```

See the [sample data](sample/) for formats you can customize for your own setup.

## Data formats
### Rules file (`rules.json`)
```json
{
  "rules": [
    {"id": "risk-01", "name": "Respect max daily loss", "description": "Stop once loss limit hit", "category": "risk"},
    {"id": "setup-01", "name": "Trade only A-setups", "description": "Skip trades outside playbook", "category": "selection"}
  ]
}
```

### Trades file (`trades_YYYY-MM-DD.json`)
Each trade includes the actual P&L and the P&L you would have earned if you had followed your playbook perfectly. If a trade should have been skipped when a rule was violated, set `planned_pnl` to `0` to model the avoided loss.
```json
{
  "trades": [
    {
      "symbol": "AAPL",
      "actual_pnl": -150.0,
      "planned_pnl": 120.0,
      "violated_rules": ["setup-01"],
      "notes": "Chased breakout before confirmation"
    },
    {
      "symbol": "MSFT",
      "actual_pnl": 320.0,
      "planned_pnl": 320.0,
      "violated_rules": [],
      "notes": "Followed plan"
    }
  ]
}
```

## Key commands
- `youvsyou init --rules <rules.json>`: create a new journal file.
- `youvsyou rules`: list the current rule set.
- `youvsyou add-day --date <YYYY-MM-DD> --trades <trades.json> [--notes "..."]`: log a trading day and compute perfect-vs-actual metrics.
- `youvsyou compare --date <YYYY-MM-DD>`: show metrics for a specific date.
- `youvsyou summary --period <day|week|month|year>`: roll up performance over the selected period.

## How the comparison works
For each trade, the tool captures:
- **Actual P&L**: what you booked.
- **Perfect P&L**: what would have been earned if you had followed every rule (provided as `planned_pnl`).
- **Rule impact**: if any rules were violated, the impact is tracked so you can see which rules cost the most.

The daily summary adds these up to produce:
- `actual_total`: sum of actual P&L.
- `perfect_total`: sum of perfect P&L.
- `discipline_gap`: `perfect_total - actual_total`.

Rollups group daily results by ISO week, month, or year using the trading date.

## Extending
This starter focuses on transparency and simplicity. You can extend it by:
- Exporting results to CSV/Notion.
- Adding notebook-based visualizations.
- Using LLMs to suggest rule tweaks based on repeated violations.

