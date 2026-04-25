from pathlib import Path
import json

SCORES_FILE = Path(__file__).parent.parent / 'utils' / 'scores.json'
"""The scores JSON file path."""

DEFAULT_SCORES: dict[str, int] = {
    'player_wins': 0,
    'opponent_wins': 0,
}
"""The default scores object."""

def load_scores() -> dict[str, int]:
    """Loads scores from disk, returning defaults if the file doesn't exist."""

    try:
        return json.loads(SCORES_FILE.read_text())
    except:
        return DEFAULT_SCORES.copy()

def save_scores(stats: dict[str, int]) -> None:
    """Saves scores to disk."""

    SCORES_FILE.write_text(json.dumps(stats, indent=2))

def record_win(*, player: bool) -> None:
    """Increments the win counter for the player or opponent."""

    scores = load_scores()

    key = 'player_wins' if player else 'opponent_wins'
    scores[key] = scores.get(key, 0) + 1

    save_scores(scores)