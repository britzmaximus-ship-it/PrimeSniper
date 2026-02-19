from typing import List, Dict, Tuple

def passes_filters(c: Dict, pb: Dict) -> bool:
    th = pb["thresholds"]
    if c["liquidity_usd"] < th["min_liquidity_usd"]:
        return False
    if c["volume_5m_usd"] < th["min_volume_5m_usd"]:
        return False
    if c["buysells_ratio"] < th["min_buysells_ratio"]:
        return False
    if c["fdv_usd"] > th["max_fdv_usd"] and th["max_fdv_usd"] > 0:
        return False

    bl = pb.get("blacklist", {})
    if c["mint"] in set(bl.get("mints", [])):
        return False
    if c["symbol"] in set(bl.get("symbols", [])):
        return False

    return True

def score_candidate(c: Dict, pb: Dict) -> float:
    w = pb["weights"]
    # normalize-ish
    liq = min(c["liquidity_usd"] / 200000, 1.0)
    vol = min(c["volume_5m_usd"] / 100000, 1.0)
    ratio = min(c["buysells_ratio"] / 3.0, 1.0)
    mom = max(min((c["price_change_5m"] + 30) / 60, 1.0), 0.0)  # map -30..+30 into 0..1

    return (
        w["liquidity_usd"] * liq +
        w["volume_5m_usd"] * vol +
        w["buysells_ratio"] * ratio +
        w["price_change_5m"] * mom
    )

def pick_top(cands: List[Dict], pb: Dict, k: int = 5) -> List[Dict]:
    filtered = [c for c in cands if passes_filters(c, pb)]
    scored: List[Tuple[float, Dict]] = [(score_candidate(c, pb), c) for c in filtered]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for s, c in scored[:k]]