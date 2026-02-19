from typing import List, Dict
from playbook import save_playbook

def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def update_playbook(pb: dict, closed_trades: List[Dict]) -> dict:
    """
    Simple, auditable learning:
    - Track tag win/loss/avg_return
    - Slightly adjust thresholds + weights based on recent performance
    """
    if not closed_trades:
        return pb

    # Update pattern stats
    for tr in closed_trades:
        tags = tr.get("tags", [])
        ret = float(tr.get("return_pct", 0.0))
        win = ret > 0

        for tag in tags:
            ps = pb["pattern_stats"].get(tag, {"wins": 0, "losses": 0, "avg_return": 0.0, "n": 0})
            ps["wins"] += 1 if win else 0
            ps["losses"] += 0 if win else 1
            ps["n"] += 1
            # incremental average
            ps["avg_return"] = ps["avg_return"] + (ret - ps["avg_return"]) / ps["n"]
            pb["pattern_stats"][tag] = ps

    # Recent performance
    recent = closed_trades[-20:]
    wins = sum(1 for t in recent if float(t.get("return_pct", 0)) > 0)
    avg_ret = sum(float(t.get("return_pct", 0)) for t in recent) / max(1, len(recent))

    # If recent is bad, tighten filters; if good, loosen slightly
    th = pb["thresholds"]

    if avg_ret < 0:
        th["min_liquidity_usd"] = int(_clamp(th["min_liquidity_usd"] * 1.05, 5000, 200000))
        th["min_volume_5m_usd"] = int(_clamp(th["min_volume_5m_usd"] * 1.05, 1000, 500000))
        th["min_buysells_ratio"] = float(_clamp(th["min_buysells_ratio"] * 1.02, 1.0, 3.0))
    else:
        th["min_liquidity_usd"] = int(_clamp(th["min_liquidity_usd"] * 0.99, 5000, 200000))
        th["min_volume_5m_usd"] = int(_clamp(th["min_volume_5m_usd"] * 0.99, 1000, 500000))
        th["min_buysells_ratio"] = float(_clamp(th["min_buysells_ratio"] * 0.995, 1.0, 3.0))

    # Nudge weights toward features that correlated with wins recently
    # (very simple: if wins > losses recently, slightly increase momentum-related weights)
    w = pb["weights"]
    if wins > (len(recent) - wins):
        w["volume_5m_usd"] = _clamp(w["volume_5m_usd"] + 0.01, 0.1, 0.6)
        w["buysells_ratio"] = _clamp(w["buysells_ratio"] + 0.01, 0.1, 0.6)
        w["price_change_5m"] = _clamp(w["price_change_5m"] + 0.005, 0.05, 0.4)
    else:
        w["volume_5m_usd"] = _clamp(w["volume_5m_usd"] - 0.01, 0.1, 0.6)
        w["buysells_ratio"] = _clamp(w["buysells_ratio"] - 0.01, 0.1, 0.6)
        w["price_change_5m"] = _clamp(w["price_change_5m"] - 0.005, 0.05, 0.4)

    # Normalize weights to sum to 1
    s = sum(w.values())
    for k in list(w.keys()):
        w[k] = float(w[k] / s)

    pb["thresholds"] = th
    pb["weights"] = w

    save_playbook(pb)
    return pb