import os
from dotenv import load_dotenv

load_dotenv()

def env_str(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()

def env_float(key: str, default: float) -> float:
    try:
        return float(os.getenv(key, str(default)))
    except Exception:
        return default

def env_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except Exception:
        return default

TELEGRAM_BOT_TOKEN = env_str("TELEGRAM_BOT_TOKEN")
TELEGRAM_USER_ID = env_str("TELEGRAM_USER_ID")

LOOP_SECONDS = env_int("LOOP_SECONDS", 30)

LIVE_TRADING_ENABLED = env_str("LIVE_TRADING_ENABLED", "false").lower() == "true"
RPC_URL = env_str("RPC_URL", "https://api.mainnet-beta.solana.com")
SOLANA_PRIVATE_KEY = env_str("SOLANA_PRIVATE_KEY", "")

MAX_SOL_PER_TRADE = env_float("MAX_SOL_PER_TRADE", 0.05)
MIN_SOL_RESERVE_SOL = env_float("MIN_SOL_RESERVE_SOL", 0.5)

# Paper trade defaults
PAPER_MAX_OPEN_TRADES = env_int("PAPER_MAX_OPEN_TRADES", 3)
PAPER_TP_PCT = env_float("PAPER_TP_PCT", 0.40)   # +40%
PAPER_SL_PCT = env_float("PAPER_SL_PCT", 0.25)   # -25%
PAPER_MAX_HOLD_MIN = env_int("PAPER_MAX_HOLD_MIN", 240)  # 4 hours

# Live gate requirements
GATE_MIN_TRADES = env_int("GATE_MIN_TRADES", 30)
GATE_MIN_WINRATE = env_float("GATE_MIN_WINRATE", 0.45)
GATE_MIN_AVG_RETURN = env_float("GATE_MIN_AVG_RETURN", 0.05)  # +5% average