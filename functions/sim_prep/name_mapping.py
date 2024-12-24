# functions/sim_prep/name_mapping.py

import os
import logging
import pandas as pd
from .config import NAMES_FILE

def load_name_mapping():
    """
    Loads 'names.csv' [raw_name, approved_name].
    Returns a dict {raw_name -> approved_name}.
    """
    mapping = {}
    if not os.path.exists(NAMES_FILE):
        logging.debug(f"{NAMES_FILE} not found; returning empty mapping.")
        return mapping

    if os.path.getsize(NAMES_FILE) == 0:
        logging.debug(f"{NAMES_FILE} is empty; returning empty mapping.")
        return mapping

    try:
        df = pd.read_csv(NAMES_FILE)
        if "raw_name" not in df.columns or "approved_name" not in df.columns:
            logging.warning(f"{NAMES_FILE} missing expected columns. Using empty mapping.")
            return mapping

        for _, row in df.iterrows():
            mapping[row["raw_name"]] = row["approved_name"]
    except pd.errors.EmptyDataError:
        logging.warning(f"No columns to parse in {NAMES_FILE}. Using empty mapping.")
    except Exception as e:
        logging.error(f"Error reading {NAMES_FILE}: {e}")

    logging.debug(f"Loaded name mapping: {mapping}")
    return mapping


def append_name_mapping(raw_name, approved_name):
    """
    Writes row [raw_name, approved_name] to 'names.csv'.
    Creates file if doesn't exist or empty.
    """
    if not os.path.exists(NAMES_FILE) or os.path.getsize(NAMES_FILE) == 0:
        logging.debug(f"Creating new {NAMES_FILE} with headers.")
        df_new = pd.DataFrame([[raw_name, approved_name]],
                              columns=["raw_name","approved_name"])
        df_new.to_csv(NAMES_FILE, index=False)
    else:
        df_map = pd.read_csv(NAMES_FILE)
        new_row = pd.DataFrame([[raw_name, approved_name]],
                               columns=["raw_name","approved_name"])
        df_map = pd.concat([df_map, new_row], ignore_index=True)
        df_map.drop_duplicates(["raw_name"], inplace=True)
        df_map.to_csv(NAMES_FILE, index=False)
    logging.debug(f"Appended {raw_name}->{approved_name} in {NAMES_FILE}.")
