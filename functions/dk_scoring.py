# draftkings_scoring.py

def calculate_draftkings_points(events, best_of_3=True):
    """
    Calculate DraftKings fantasy points based on a dictionary of match events.
    Adjust these rules as needed for your scoring system.
    """
    match_played_points = 30
    game_won_points = 2.5 if best_of_3 else 2
    game_lost_points = -2 if best_of_3 else -1.6
    set_won_points = 6 if best_of_3 else 5
    set_lost_points = -3 if best_of_3 else -2.5
    match_won_points = 6 if best_of_3 else 5
    ace_points = 0.4 if best_of_3 else 0.25
    double_fault_points = -1
    break_points = 0.75 if best_of_3 else 0.5
    clean_set_bonus = 4 if best_of_3 else 2.5
    straight_sets_bonus = 6 if best_of_3 else 5
    no_double_fault_bonus = 2.5 if best_of_3 else 5

    points = match_played_points
    points += events['games_won'] * game_won_points
    points += events['games_lost'] * game_lost_points
    points += events['sets_won'] * set_won_points
    points += events['sets_lost'] * set_lost_points
    points += events['match_won'] * match_won_points
    points += events['aces'] * ace_points
    points += events['double_faults'] * double_fault_points
    points += events['breaks'] * break_points

    if events['clean_sets'] > 0:
        points += clean_set_bonus * events['clean_sets']
    if events['straight_sets']:
        points += straight_sets_bonus
    if events['double_faults'] == 0:
        points += no_double_fault_bonus

    return points
