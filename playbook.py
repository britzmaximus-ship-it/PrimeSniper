from storage import read_json, write_json_atomic

PLAYBOOK_PATH = "data/playbook.json"

DEFAULT_PLAYBOOK = {
    "version": 1,
    "thresholds": {
        "min_liquidity_usd": 15000,
        "min_volume_5m_usd": 5000,
        "min_buysells_ratio": 1.2,
        "max_fdv_usd": 2000000
    },
    "weights": {
        "liquidity_usd": 0.15,
        "volume_5m_usd": 0.35,
        "buysells_ratio": 0.35,
        "price_change_5m": 0.15
    },
    "pattern_stats": {
        # tag -> {wins, losses, avg_return}
    },
    "blacklist": {
        "mints": [],
        "symbols": []
    }
}

def load_playbook() -> dict:
    pb = read_json(PLAYBOOK_PATH, DEFAULT_PLAYBOOK)
    # ensure keys exist
    for k, v in DEFAULT_PLAYBOOK.items():
        if k not in pb:
            pb[k] = v
    return pb

def save_playbook(pb: dict) -> None:
    write_json_atomic(PLAYBOOK_PATH, pb)