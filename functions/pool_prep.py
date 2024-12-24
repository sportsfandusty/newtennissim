# data_preparation.py

import pandas as pd
import re
from rapidfuzz import process, fuzz

def parse_opponent(game_info, player_team):
    """
    Extract the opponent from strings like:
      "Jimenez Kasintseva@Kalinskaya 03/21/2023 12:15PM ET"
    Steps:
      1) Use a regex to capture everything before the date/time (MM/DD/YYYY).
      2) Split on '@' to separate the two names.
      3) Check which side matches 'player_team' (directly or via fuzzy).
      4) Return the other side as the opponent.
    """

    # Regex to capture everything up to the first date in the format MM/DD/YYYY
    match = re.match(r"^(.*?)\s*\d{2}/\d{2}/\d{4}", game_info)
    if match:
        main_part = match.group(1).strip()  # e.g. "Jimenez Kasintseva@Kalinskaya"
    else:
        # If we can't find the date pattern, just use the entire "Game Info"
        main_part = game_info

    # Split on '@'
    parts = main_part.split('@')
    if len(parts) == 2:
        home = parts[0].strip()
        away = parts[1].strip()

        # 1) Direct match
        if player_team == home:
            return away
        elif player_team == away:
            return home

        # 2) Fuzzy approach if direct match doesn't work
        best_match = process.extractOne(
            player_team, [home, away], scorer=fuzz.ratio
        )
        if best_match:
            matched_side, score, _ = best_match
            # If we matched 'home' better, then 'away' is the opponent
            # If we matched 'away', then 'home' is the opponent
            return away if matched_side == home else home

    # If parsing fails or the format is unexpected, return None
    return None


def fuzzy_match_names(raw_name, valid_names, threshold=90, potential_warn=75):
    """
    Attempt fuzzy matching between raw_name and a list of valid_names.
    Returns the best match if >= threshold; else None.
    Prints a note if match is above potential_warn but below threshold.
    """
    if not isinstance(raw_name, str):
        return None
    best_match = process.extractOne(raw_name, valid_names, scorer=fuzz.ratio)
    if best_match:
        name, score, _ = best_match
        if score >= threshold:
            return name
        elif score >= potential_warn:
            print(f"[FYI] Potential fuzzy match for '{raw_name}': '{name}' (score: {score})")
    return None


def load_player_stats(atp_file, wta_file):
    """
    Combine stats from ATP & WTA CSVs (both must have a 'Player' column).
    Return a DataFrame with all rows from both.
    """
    atp_df = pd.read_csv(atp_file)
    wta_df = pd.read_csv(wta_file)
    combined = pd.concat([atp_df, wta_df], ignore_index=True)
    return combined


def deduplicate_matches(df):
    """
    Deduplicate so that each (Name, Opponent) pair appears only once.
    Drops rows where Opponent is None (failed parsing).
    """
    # Remove rows where Opponent is None/NaN
    df = df.dropna(subset=["Opponent"]).copy()

    df["MatchKey"] = df.apply(
        lambda row: tuple(sorted([row["Name"], row["Opponent"]])), axis=1
    )
    df = df.drop_duplicates(subset="MatchKey").reset_index(drop=True)
    return df


def load_and_clean_data(
    raw_csv_path,
    atp_file=None,
    wta_file=None,
    do_fuzzy_match=False,
    threshold=90,
    potential_warn=75
):
    """
    1) Load the raw DFS CSV (e.g. with columns: [Name, Salary, Game Info, TeamAbbrev, ...])
    2) Parse Opponent from 'Game Info' (handles multi-word last names)
    3) (Optional) fuzzy match Name & Opponent to unify with Elo stats from ATP/WTA
    4) Return the DataFrame (not yet deduplicated - call deduplicate_matches if desired)
    """

    # 1) Load raw DFS file
    raw_df = pd.read_csv(raw_csv_path)

    # 2) Parse Opponent
    raw_df["Opponent"] = raw_df.apply(
        lambda row: parse_opponent(
            str(row["Game Info"]),
            str(row["TeamAbbrev"])
        ),
        axis=1
    )

    # 3) (Optional) fuzzy match with stats
    if do_fuzzy_match and atp_file and wta_file:
        stats_df = load_player_stats(atp_file, wta_file)
        valid_names = stats_df["Player"].unique()

        raw_df["FuzzyPlayer"] = raw_df["Name"].apply(
            lambda nm: fuzzy_match_names(nm, valid_names, threshold, potential_warn)
        )
        raw_df["FuzzyOpponent"] = raw_df["Opponent"].apply(
            lambda opp: fuzzy_match_names(opp, valid_names, threshold, potential_warn)
        )

        # Example: pull Elo for player
        stats_df_small_p = stats_df[["Player", "Elo"]].rename(columns={"Player": "FuzzyPlayer"})
        raw_df = pd.merge(raw_df, stats_df_small_p, how="left", on="FuzzyPlayer")

        # And for opponent
        stats_df_small_o = stats_df[["Player", "Elo"]].rename(columns={"Player": "FuzzyOpponent", "Elo": "OpponentElo"})
        raw_df = pd.merge(raw_df, stats_df_small_o, how="left", on="FuzzyOpponent")

    return raw_df


if __name__ == "__main__":
    """
    Example usage:
      1) Load the raw CSV
      2) Optionally fuzzy match with stats
      3) Deduplicate the matches
      4) Print or save the final DataFrame
    """
    # Suppose you have a sample CSV in "csvs/pool_sample.csv"
    raw_csv_path = "csvs/pool_sample.csv"

    # If you want to fuzzy match with "csvs/atp.csv" and "csvs/wta.csv":
    df = load_and_clean_data(
        raw_csv_path,
        atp_file="csvs/atp.csv",
        wta_file="csvs/wta.csv",
        do_fuzzy_match=True,
        threshold=90,
        potential_warn=75
    )

    # Now deduplicate
    df = deduplicate_matches(df)

    print("Data prep complete. Here's a sample:")
    print(df.head(10))
