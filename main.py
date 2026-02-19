import time
from typing import Dict

from config import LOOP_SECONDS, LIVE_TRADING_ENABLED
from telegram import send
from playbook import load_playbook
from learner import update_playbook
from scanner import fetch_candidates
from scorer import pick_top
from paper import load_state, open_paper_trades, update_prices, close_logic
from risk import live_gate_ok

# Optional live
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID

def build_price_lookup(candidates) -> Dict[str, float]:
    # candidate mint -> price_usd
    return {c["mint"]: float(c.get("price_usd") or 0) for c in candidates if c.get("mint")}

def fmt_trade(t: dict) -> str:
    return f"{t['symbol']} | entry ${t['entry_price']:.8f} | now ${t['last_price']:.8f} | PnL {t['return_pct']:+.2%} | {t.get('snapshot', {}).get('url','')}"

def main():
    send("🤖 Bot starting (paper trading + learning). Live trading is OFF unless enabled.")

    while True:
        try:
            pb = load_playbook()
            state = load_state()

            cands = fetch_candidates(limit=40)
            picks = pick_top(cands, pb, k=6)

            # Update paper trade prices using latest scan prices
            price_lookup = build_price_lookup(cands)
            update_prices(state["open"], price_lookup)

            opened = open_paper_trades(picks, state)
            closed = close_logic(state)

            # Learning step
            if closed:
                pb = update_playbook(pb, closed)

            # Telegram updates
            if picks:
                top = picks[0]
                send(f"🔍 Scan: {len(cands)} cands | {len(picks)} picks | Top: {top['symbol']} liq ${top['liquidity_usd']:.0f} vol5m ${top['volume_5m_usd']:.0f} ratio {top['buysells_ratio']:.2f} chg5m {top['price_change_5m']:+.1f}%\n{top.get('url','')}")
            if opened:
                for t in opened:
                    send("📄 PAPER OPEN ✅ " + fmt_trade(t))
            if state["open"]:
                # brief status for first 2
                for t in state["open"][:2]:
                    send("📈 PAPER UPDATE " + fmt_trade(t))
            if closed:
                for t in closed:
                    send(f"📌 PAPER CLOSED ({t['reason_close']}) {t['symbol']} PnL {t['return_pct']:+.2%}")

            # Gate check for live
            gate = live_gate_ok(state["closed"])
            if not gate["ok"]:
                if LIVE_TRADING_ENABLED:
                    send(f"🧯 Live enabled but gate FAILED: {gate['reason']}")
            else:
                if LIVE_TRADING_ENABLED:
                    send(f"✅ Live gate PASSED: {gate['reason']}\n(Next step: mirror only new best entries)")

                    # NOTE: keeping live mirroring minimal by default.
                    # You can implement "mirror top opened paper trade" logic here safely.
                    # I left it intentionally conservative so you don't accidentally trade.

            time.sleep(LOOP_SECONDS)

        except Exception as e:
            send(f"❌ Error: {type(e).__name__}: {e}")
            time.sleep(max(10, LOOP_SECONDS))

if __name__ == "__main__":
    # quick sanity check env
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_USER_ID:
        print("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_USER_ID. Telegram sends will be skipped.")
    main()