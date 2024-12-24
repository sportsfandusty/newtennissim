# functions/sim_prep/run_sim_prep.py

import os
import logging
import pandas as pd
from rapidfuzz import process, fuzz

from .config import (CONTEXT_FILE, OUTPUT_FILE, MIN_SCORE, FUZZY_THRESHOLD)
from .name_mapping import load_name_mapping, append_name_mapping
from .pending_approvals import save_pending_approval
from .stats_db import load_player_stats
from .baseline_estimation import baseline_stats, tune_stats_for_implied_wp

def run_sim_prep():
    """
    1) Load match_context.csv => [Name, Opponent, Surface, ImpliedWinPercentage]
    2) Use name_mapping + fuzzy logic => find stats or estimate
    3) Store borderline matches in pending_approvals
    4) Write final data/sim_ready.csv with "StatsSource" column
    5) Validate match count: Ensure all matches from context are included.
    Returns final DataFrame.
    """
    if not os.path.exists(CONTEXT_FILE):
        err = f"{CONTEXT_FILE} missing. Cannot do sim prep."
        logging.error(err)
        raise FileNotFoundError(err)

    df_context = pd.read_csv(CONTEXT_FILE)
    logging.debug(f"Loaded context from {CONTEXT_FILE}, shape={df_context.shape}")

    # Load name mapping
    name_map = load_name_mapping()
    # Load stats DB
    stats_db = load_player_stats()
    if "Player" not in stats_db.columns:
        logging.warning("Stats DB lacks 'Player' => always estimate.")
        stats_db = pd.DataFrame(columns=["Player", "Elo", "ServiceGamesWonPercentage", "ReturnGamesWonPercentage"])

    final_rows = []

    for _, row in df_context.iterrows():
        raw_name = row["Name"]
        opp_name = row["Opponent"]
        surface = row["Surface"]
        implied_wp = float(row["ImpliedWinPercentage"])

        logging.debug(f"Preparing {raw_name} vs {opp_name}, surface={surface}, wp={implied_wp}")

        # (A) If raw_name is in name_map => no fuzzy needed
        if raw_name in name_map:
            approved_name = name_map[raw_name]
            logging.debug(f"Mapping found: {raw_name} -> {approved_name}")
        else:
            # (B) Fuzzy match
            player_list = stats_db["Player"].unique()
            if len(player_list) == 0:
                approved_name = None
                logging.debug("Empty stats DB => no fuzzy match possible.")
            else:
                candidates = process.extract(raw_name, player_list, scorer=fuzz.ratio, limit=3)
                if not candidates:
                    approved_name = None
                else:
                    top_name, top_score, _ = candidates[0]
                    logging.debug(f"Fuzzy best: {top_name} (score={top_score})")

                    if top_score >= FUZZY_THRESHOLD:
                        # auto-approve
                        approved_name = top_name
                        append_name_mapping(raw_name, approved_name)
                    elif top_score >= MIN_SCORE:
                        # borderline => pending
                        cands_clean = [(c[0], c[1]) for c in candidates]
                        save_pending_approval(raw_name, cands_clean)
                        approved_name = None
                    else:
                        approved_name = None

        # (C) Determine stats and stats source
        stats_source = "Estimated"  # Default to estimated stats

        if approved_name:
            sub = stats_db[stats_db["Player"] == approved_name]
            if not sub.empty:
                ps = sub.iloc[0]
                out_elo = ps.get("Elo", 1500)
                out_sgw = ps.get("ServiceGamesWonPercentage", 0.60)
                out_rgw = ps.get("ReturnGamesWonPercentage", 0.35)
                stats_source = "Database"  # Use database stats
                logging.debug(f"Using DB stats for {approved_name}: Elo={out_elo}, SGW={out_sgw}, RGW={out_rgw}")
            else:
                # No row in DB => estimate stats
                base = baseline_stats()
                tuned = tune_stats_for_implied_wp(base, implied_wp)
                out_elo = tuned["Elo"]
                out_sgw = tuned["ServiceGamesWon"]
                out_rgw = tuned["ReturnGamesWon"]
        else:
            # No approved name => baseline + estimate
            base = baseline_stats()
            tuned = tune_stats_for_implied_wp(base, implied_wp)
            out_elo = tuned["Elo"]
            out_sgw = tuned["ServiceGamesWon"]
            out_rgw = tuned["ReturnGamesWon"]

        final_rows.append({
            "Name": raw_name,
            "Opponent": opp_name,
            "Surface": surface,
            "ImpliedWinPercentage": implied_wp,
            "Elo": int(out_elo),
            "ServiceGamesWon": round(out_sgw, 3),
            "ReturnGamesWon": round(out_rgw, 3),
            "StatsSource": stats_source  # Add stats source
        })

    df_final = pd.DataFrame(final_rows)
    df_final.to_csv(OUTPUT_FILE, index=False)
    logging.info(f"Sim prep complete. Wrote {len(df_final)} rows to {OUTPUT_FILE}.")

    # Validation step: Ensure match counts align
    context_matches = len(df_context) // 2  # Each match is listed twice
    prepped_matches = len(df_final) // 2

    if context_matches != prepped_matches:
        logging.error(f"Mismatch in match count! Context: {context_matches}, Prepared: {prepped_matches}")
        raise ValueError(
            f"Match count mismatch! Context has {context_matches} matches, but only {prepped_matches} were prepped."
        )
    else:
        logging.info(f"Match count validation passed. Matches: {context_matches}")

    return df_final
