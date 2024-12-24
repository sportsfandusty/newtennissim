# simulation.py

import pandas as pd
import numpy as np
import logging
from csvs.tennis_sim.dk_scoring import calculate_draftkings_points

logging.basicConfig(level=logging.INFO)

def simulate_match_with_stats(row):
    """
    Use the row's Elo to compute a probability that 'Name' wins.
    """
    # If Elo columns exist
    player_elo = row.get("Elo", 1500)        # from 'FuzzyPlayer'
    opponent_elo = row.get("OpponentElo", 1500)

    # Example logistic formula
    elo_diff = player_elo - opponent_elo
    player_win_prob = 1 / (1 + np.exp(-elo_diff / 400))

    return simulate_match_generic(row, player_win_prob)

def simulate_match_with_odds(row):
    """
    If you have an ImpliedWinPercentage or something similar, you can do that here.
    Or default to 50-50 if unknown.
    """
    implied_wp = row.get("ImpliedWinPercentage", 50)
    player_win_prob = implied_wp / 100.0

    return simulate_match_generic(row, player_win_prob)

def simulate_match_generic(row, player_win_prob):
    """
    Generate random match events for 'Name' vs. 'Opponent' using player_win_prob.
    """
    player = row["Name"]
    opponent = row["Opponent"]
    salary = row["Salary"]
    # We'll guess Opponent salary from the same DataFrame or default
    opponent_salary = row.get("OpponentSalary", 4500)

    # Decide winner
    winner = player if np.random.rand() < player_win_prob else opponent

    # Random events
    aces_player = np.random.poisson(lam=0.65 * 12)
    aces_opponent = np.random.poisson(lam=0.65 * 12)
    double_faults_player = np.random.poisson(lam=0.05 * 12)
    double_faults_opponent = np.random.poisson(lam=0.05 * 12)
    breaks_player = np.random.poisson(lam=0.3 * 5)
    breaks_opponent = np.random.poisson(lam=0.3 * 5)

    games_won_player = np.random.poisson(lam=0.65 * 12)
    # Assume a total of 12 games for demonstration
    games_won_opponent = 12 - games_won_player

    sets_won_player = 2 if winner == player else 0
    sets_won_opponent = 2 if winner == opponent else 0

    events_player = {
        'games_won': games_won_player,
        'games_lost': games_won_opponent,
        'sets_won': sets_won_player,
        'sets_lost': sets_won_opponent,
        'match_won': 1 if winner == player else 0,
        'aces': aces_player,
        'double_faults': double_faults_player,
        'breaks': breaks_player,
        'clean_sets': 1 if sets_won_player == 2 and games_won_opponent == 0 else 0,
        'straight_sets': (sets_won_player == 2)
    }
    points_player = calculate_draftkings_points(events_player)

    events_opponent = {
        'games_won': games_won_opponent,
        'games_lost': games_won_player,
        'sets_won': sets_won_opponent,
        'sets_lost': sets_won_player,
        'match_won': 1 if winner == opponent else 0,
        'aces': aces_opponent,
        'double_faults': double_faults_opponent,
        'breaks': breaks_opponent,
        'clean_sets': 1 if sets_won_opponent == 2 and games_won_player == 0 else 0,
        'straight_sets': (sets_won_opponent == 2)
    }
    points_opponent = calculate_draftkings_points(events_opponent)

    return [
        {
            'Player': player,
            'Salary': salary,
            'DK_Score': points_player,
        },
        {
            'Player': opponent,
            'Salary': opponent_salary,
            'DK_Score': points_opponent,
        }
    ]

def simulate_match(row):
    """
    Dispatcher that decides if we have stats-based (Elo in row),
    otherwise fallback to odds-based or 50-50.
    """
    # If 'Elo' in row is not null, we assume stats-based
    if pd.notnull(row.get("Elo", None)):
        return simulate_match_with_stats(row)
    else:
        return simulate_match_with_odds(row)

def simulate_all_matches(df):
    """
    Iterate over each row in df, simulate match. Return a DataFrame of player-level results.
    """
    results = []
    for _, row in df.iterrows():
        # Attempt to find Opponent Salary from DF if needed
        # (That can be done in data prep if you like.)
        sim_outcomes = simulate_match(row)
        results.append(sim_outcomes)

    # Flatten the list of lists
    flattened = [player for match in results for player in match]
    return pd.DataFrame(flattened)
