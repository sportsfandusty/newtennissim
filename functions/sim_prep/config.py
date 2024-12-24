# functions/sim_prep/config.py
import logging

# Toggle debug logs
DEBUG = True

# Hard-coded file paths
NAMES_FILE = "csvs/names.csv"
ATP_FILE = "csvs/atp.csv"
WTA_FILE = "csvs/wta.csv"
CONTEXT_FILE = "data/match_context.csv"
OUTPUT_FILE = "data/sim_ready.csv"
PENDING_FILE = "data/pending_approvals.csv"

# Fuzzy thresholds
FUZZY_THRESHOLD = 90
MIN_SCORE = 70

# Logging setup
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(levelname)s: %(message)s"
)
