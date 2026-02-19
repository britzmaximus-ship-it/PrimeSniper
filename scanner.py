import requests
from typing import List, Dict

DEX_TRENDING_SOL = "https://api.dexscreener.com/latest/dex/search?q=solana"

def fetch_candidates(limit: int = 30) -> List[Dict]:
    """
    DexScreener search isn't perfect trending, but works as a practical start.
    You can later swap this with specific endpoints or pump.fun feeds.
    """
    r = requests.get(DEX_TRENDING_SOL, timeout=20)
    r.raise_for_status()
    data = r.json()
    pairs = data.get("pairs", [])[:limit]

    out = []
    for p in pairs:
        if p.get("chainId") != "solana":
            continue
        base = p.get("baseToken", {}) or {}
        quote = p.get("quoteToken", {}) or {}
        if quote.get("symbol") not in ["SOL", "USDC", "USDT"]:
            # still allow some, but prefer SOL stables
            pass

        liq = (p.get("liquidity", {}) or {}).get("usd") or 0
        fdv = p.get("fdv") or 0
        price_change_5m = (p.get("priceChange", {}) or {}).get("m5") or 0
        vol_5m = (p.get("volume", {}) or {}).get("m5") or 0
        txns_5m = (p.get("txns", {}) or {}).get("m5") or {}
        buys = txns_5m.get("buys") or 0
        sells = txns_5m.get("sells") or 0

        mint = base.get("address") or ""
        symbol = base.get("symbol") or ""
        name = base.get("name") or symbol

        buysells_ratio = (buys + 1) / (sells + 1)

        out.append({
            "pairAddress": p.get("pairAddress", ""),
            "dexId": p.get("dexId", ""),
            "url": p.get("url", ""),
            "mint": mint,
            "symbol": symbol,
            "name": name,
            "liquidity_usd": float(liq),
            "fdv_usd": float(fdv),
            "volume_5m_usd": float(vol_5m),
            "buys_5m": int(buys),
            "sells_5m": int(sells),
            "buysells_ratio": float(buysells_ratio),
            "price_change_5m": float(price_change_5m),
            "price_usd": float(p.get("priceUsd") or 0),
        })
    return out