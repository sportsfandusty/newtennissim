# functions/sim_prep/baseline_estimation.py

import logging
from .config import DEBUG

def baseline_stats():
    """
    Our default baseline for unknown players.
    You can refine or do dynamic approach.
    """
    return {
        "Elo": 1500,
        "ServiceGamesWon": 0.60,
        "ReturnGamesWon": 0.35
    }

def tune_stats_for_implied_wp(base_stats, implied_wp):
    """
    Example approach:
    factor = (implied_wp / 100.0) + 0.5
    so 50 => 1.0, 30 => 0.8, 80 => 1.3
    """
    factor = (implied_wp / 100.0) + 0.5
    stats = dict(base_stats)
    stats["Elo"] = int(stats["Elo"] * factor)
    stats["ServiceGamesWon"] *= factor
    stats["ReturnGamesWon"] *= factor

    if DEBUG:
        logging.debug(
            f"Tuning stats: WP={implied_wp}, factor={round(factor,2)}, "
            f"Elo={stats['Elo']}, SGW={round(stats['ServiceGamesWon'],2)}, "
            f"RGW={round(stats['ReturnGamesWon'],2)}"
        )
    return stats
