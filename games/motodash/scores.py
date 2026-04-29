import json
from pathlib import Path

from logger import log

import config


_SCORE_PATH = Path.home() / ".config" / "pokedex" / "motodash.json"


def _empty_state():
    return {"best_times": {}}


def load():
    try:
        if not _SCORE_PATH.exists():
            return _empty_state()
        with _SCORE_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "best_times" not in data:
            log("[motodash] scores.json malformed, resetting", "warning")
            return _empty_state()
        return data
    except Exception as e:
        log(f"[motodash] scores load failed: {e}", "warning")
        return _empty_state()


def save(state):
    try:
        _SCORE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _SCORE_PATH.open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        log(f"[motodash] scores save failed: {e}", "error")


def medal_for_time(level, time_seconds):
    if time_seconds <= level["gold"]:
        return config.MEDAL_GOLD
    if time_seconds <= level["silver"]:
        return config.MEDAL_SILVER
    if time_seconds <= level["bronze"]:
        return config.MEDAL_BRONZE
    return config.MEDAL_NONE


def record_time(state, level_id, time_seconds, medal):
    bt = state.setdefault("best_times", {})
    prev = bt.get(level_id)
    if prev is None or time_seconds < prev["time"]:
        bt[level_id] = {"time": time_seconds, "medal": medal}
        return True
    return False
