import time
from typing import Dict, List
from storage import read_json, write_json_atomic
from config import PAPER_TP_PCT, PAPER_SL_PCT, PAPER_MAX_OPEN_TRADES, PAPER_MAX_HOLD_MIN

PAPER_PATH = "data/paper_trades.json"

def load_state() -> dict:
    return read_json(PAPER_PATH, {"open": [], "closed": []})

def save_state(state: dict) -> None:
    write_json_atomic(PAPER_PATH, state)

def _now() -> int:
    return int(time.time())

def open_paper_trades(picks: List[Dict], state: dict) -> List[Dict]:
    opened = []
    open_trades = state["open"]
    if len(open_trades) >= PAPER_MAX_OPEN_TRADES:
        return opened

    existing_mints = set(t["mint"] for t in open_trades)

    for c in picks:
        if len(open_trades) >= PAPER_MAX_OPEN_TRADES:
            break
        if not c.get("mint") or c["mint"] in existing_mints:
            continue
        entry = float(c.get("price_usd") or 0)
        if entry <= 0:
            continue

        trade = {
            "id": f"paper_{_now()}_{c['symbol']}",
            "opened_ts": _now(),
            "closed_ts": None,
            "mint": c["mint"],
            "symbol": c["symbol"],
            "name": c.get("name", c["symbol"]),
            "entry_price": entry,
            "last_price": entry,
            "peak_price": entry,
            "tp_price": entry * (1.0 + PAPER_TP_PCT),
            "sl_price": entry * (1.0 - PAPER_SL_PCT),
            "return_pct": 0.0,
            "reason_close": None,
            "tags": _tags_from_candidate(c),
            "snapshot": {
                "liquidity_usd": c["liquidity_usd"],
                "fdv_usd": c["fdv_usd"],
                "volume_5m_usd": c["volume_5m_usd"],
                "buysells_ratio": c["buysells_ratio"],
                "price_change_5m": c["price_change_5m"],
                "url": c.get("url", "")
            }
        }
        open_trades.append(trade)
        existing_mints.add(c["mint"])
        opened.append(trade)

    state["open"] = open_trades
    save_state(state)
    return opened

def _tags_from_candidate(c: Dict) -> List[str]:
    tags = []
    if c["volume_5m_usd"] > 20000:
        tags.append("vol_spike")
    if c["buysells_ratio"] > 1.6:
        tags.append("buy_pressure")
    if c["price_change_5m"] > 10:
        tags.append("momentum_up")
    if c["liquidity_usd"] > 50000:
        tags.append("decent_liquidity")
    return tags or ["baseline"]

def update_prices(open_trades: List[Dict], price_lookup: Dict[str, float]) -> None:
    for t in open_trades:
        p = float(price_lookup.get(t["mint"], t["last_price"]))
        if p <= 0:
            continue
        t["last_price"] = p
        t["peak_price"] = max(t["peak_price"], p)
        t["return_pct"] = (p / t["entry_price"]) - 1.0

def close_logic(state: dict) -> List[Dict]:
    closed = []
    still_open = []

    now = _now()

    for t in state["open"]:
        age_min = (now - t["opened_ts"]) / 60.0
        price = t["last_price"]

        if price >= t["tp_price"]:
            t["closed_ts"] = now
            t["reason_close"] = "TP"
            closed.append(t)
            continue
        if price <= t["sl_price"]:
            t["closed_ts"] = now
            t["reason_close"] = "SL"
            closed.append(t)
            continue
        if age_min >= PAPER_MAX_HOLD_MIN:
            t["closed_ts"] = now
            t["reason_close"] = "TIME"
            closed.append(t)
            continue

        still_open.append(t)

    state["open"] = still_open
    state["closed"].extend(closed)
    save_state(state)
    return closed