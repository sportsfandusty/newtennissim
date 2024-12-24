# functions/sim_prep/pending_approvals.py

import os
import logging
import pandas as pd
from .config import PENDING_FILE

def save_pending_approval(raw_name, candidates):
    """
    Store borderline matches in 'data/pending_approvals.csv'.
    We'll keep up to 3 (name, score) pairs.
    """
    if not candidates:
        return
    row_data = [raw_name]
    for i in range(3):
        if i < len(candidates):
            row_data.append(candidates[i][0])  # candidate name
            row_data.append(candidates[i][1])  # score
        else:
            row_data.append("")
            row_data.append("")

    columns = ["raw_name","cand1","score1","cand2","score2","cand3","score3"]

    if not os.path.exists(PENDING_FILE):
        pd.DataFrame([row_data], columns=columns).to_csv(PENDING_FILE, index=False)
        logging.debug(f"Created new {PENDING_FILE} with pending row for {raw_name}.")
    else:
        df_pend = pd.read_csv(PENDING_FILE)
        df_new = pd.DataFrame([row_data], columns=columns)
        df_pend = pd.concat([df_pend, df_new], ignore_index=True)
        df_pend.drop_duplicates(subset=["raw_name"], inplace=True)
        df_pend.to_csv(PENDING_FILE, index=False)
        logging.debug(f"Appended pending approval for {raw_name} in {PENDING_FILE}.")
