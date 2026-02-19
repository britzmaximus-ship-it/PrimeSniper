from typing import List, Dict
from config import GATE_MIN_TRADES, GATE_MIN_WINRATE, GATE_MIN_AVG_RETURN

def live_gate_ok(closed_trades: List[Dict]) -> Dict:
    n = len(closed_trades)
    if n < GATE_MIN_TRADES:
        return {"ok": False, "reason": f"Need {GATE_MIN_TRADES} closed paper trades (have {n})"}

    recent = closed_trades[-GATE_MIN_TRADES:]
    wins = sum(1 for t in recent if float(t.get("return_pct", 0)) > 0)
    winrate = wins / max(1, len(recent))
    avg_ret = sum(float(t.get("return_pct", 0)) for t in recent) / max(1, len(recent))

    if winrate < GATE_MIN_WINRATE:
        return {"ok": False, "reason": f"Winrate too low: {winrate:.2%} < {GATE_MIN_WINRATE:.2%}"}
    if avg_ret < GATE_MIN_AVG_RETURN:
        return {"ok": False, "reason": f"Avg return too low: {avg_ret:.2%} < {GATE_MIN_AVG_RETURN:.2%}"}

    return {"ok": True, "reason": f"Gate passed (winrate {winrate:.2%}, avg {avg_ret:.2%})"}