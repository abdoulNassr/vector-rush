"""Persistent best score and the last 10 completed runs (scores.json)."""
import json
from pathlib import Path

SCORE_FILE = Path(__file__).resolve().parent / "scores.json"
MAX_RECENT = 10


def _clean(values):
    return [int(s) for s in values if isinstance(s, (int, float)) and not isinstance(s, bool)]


def load_scores():
    """Return {"best": int, "recent": [oldest ... newest]}. Never raises."""
    try:
        data = json.loads(SCORE_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError
        recent = _clean(data.get("recent", data.get("scores", [])))  # old files used "scores"
        best = data.get("best", 0)
        best = int(best) if isinstance(best, (int, float)) else 0
        return {"best": max([best] + recent), "recent": recent[-MAX_RECENT:]}
    except (OSError, ValueError, TypeError):
        return {"best": 0, "recent": []}


def save_score(score):
    """Add a finished run, update the best score, write the file, return the data."""
    board = load_scores()
    board["recent"] = (board["recent"] + [int(score)])[-MAX_RECENT:]
    board["best"] = max(board["best"], int(score))
    try:
        SCORE_FILE.write_text(json.dumps(board, indent=2), encoding="utf-8")
    except OSError:
        pass  # keep playing even if the disk is read-only
    return board
