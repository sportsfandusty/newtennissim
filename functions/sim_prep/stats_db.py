# functions/sim_prep/stats_db.py

import os
import logging
import pandas as pd
from .config import ATP_FILE, WTA_FILE

def load_player_stats():
    """Combine atp.csv + wta.csv into one DataFrame with standard columns."""
    if not os.path.exists(ATP_FILE) or not os.path.exists(WTA_FILE):
        logging.warning("ATP/WTA file missing => returning empty stats DB.")
        return pd.DataFrame(columns=["Player","Elo","ServiceGamesWonPercentage","ReturnGamesWonPercentage"])

    atp_df = pd.read_csv(ATP_FILE)
    wta_df = pd.read_csv(WTA_FILE)
    combined = pd.concat([atp_df, wta_df], ignore_index=True)
    logging.debug(f"Loaded stats: combined shape={combined.shape}")
    return combined
