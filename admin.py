# admin.py

import streamlit as st
import pandas as pd
import os

# Import the pipeline function
from functions.sim_prep import run_sim_prep
from functions.sim_prep.config import OUTPUT_FILE, PENDING_FILE
from functions.sim_prep.name_mapping import append_name_mapping


def load_pending_approvals():
    if not os.path.exists(PENDING_FILE) or os.path.getsize(PENDING_FILE) == 0:
        return pd.DataFrame(columns=["raw_name", "cand1", "score1", "cand2", "score2", "cand3", "score3"])
    return pd.read_csv(PENDING_FILE)


def remove_pending(raw_name):
    if not os.path.exists(PENDING_FILE):
        return
    df = pd.read_csv(PENDING_FILE)
    df = df[df["raw_name"] != raw_name]
    df.to_csv(PENDING_FILE, index=False)


def main():
    st.title("Admin Panel")

    # 1) Button to run sim prep
    if st.button("Run Sim Prep"):
        try:
            df = run_sim_prep()  # Writes data/sim_ready.csv
            st.success("Sim prep complete! Wrote data/sim_ready.csv.")

            # Display match count confirmation
            context_matches = len(df) // 2
            prepped_matches = len(pd.read_csv(OUTPUT_FILE)) // 2
            if context_matches == prepped_matches:
                st.success(f"Match count validation passed. Matches: {context_matches}")
            else:
                st.error(f"Match count mismatch! Context: {context_matches}, Prepped: {prepped_matches}")

            # Show full table
            st.subheader("Full Player Pool")
            st.dataframe(df)

            # Show subset with only "Estimated"
            df_estimated = df[df["StatsSource"] == "Estimated"]
            st.subheader("Players with Estimated Stats")
            if df_estimated.empty:
                st.write("No players needed estimation.")
            else:
                st.dataframe(df_estimated)

        except ValueError as e:
            st.error(f"Error during sim prep: {e}")
        except Exception as e:
            st.error(f"Unexpected error: {e}")

    st.header("Pending Fuzzy Matches")
    df_pending = load_pending_approvals()
    if df_pending.empty:
        st.write("No pending approvals.")
    else:
        for i, row in df_pending.iterrows():
            raw_name = row["raw_name"]
            st.subheader(f"Raw Name: {raw_name}")

            candidates = []
            for c_i in range(1, 4):
                cand_col = f"cand{c_i}"
                score_col = f"score{c_i}"
                if pd.notna(row[cand_col]) and row[cand_col] != "":
                    candidates.append((row[cand_col], row[score_col]))

            pick_options = ["No Match/Ignore"]
            for (cand_name, cand_score) in candidates:
                pick_options.append(f"{cand_name} (score={cand_score})")

            choice = st.selectbox(f"Choose best match for '{raw_name}'",
                                  pick_options, key=f"choice_{raw_name}")

            if st.button(f"Approve {raw_name}", key=f"approve_{raw_name}"):
                if choice == "No Match/Ignore":
                    st.write("No match chosen. Stats remain estimated.")
                else:
                    chosen_name = choice.split(" (score=")[0]
                    append_name_mapping(raw_name, chosen_name)
                    st.success(f"Saved mapping: {raw_name} -> {chosen_name}")

                remove_pending(raw_name)
                st.experimental_rerun()


if __name__ == "__main__":
    main()
