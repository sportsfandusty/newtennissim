# streamlit_app.py

import streamlit as st
import pandas as pd
import csvs.tennis_sim.data_preparation as data_preparation
import csvs.tennis_sim.simulation as simulation

st.title("Tennis Simulation Web App")

# Keep some placeholders for global data
if "cleaned_df" not in st.session_state:
    st.session_state["cleaned_df"] = None

if "sim_results" not in st.session_state:
    st.session_state["sim_results"] = None

st.header("Data Preparation")
raw_file_path = st.text_input("Raw DFS CSV path", value="csvs/pool_sample.csv")
atp_path = st.text_input("ATP Stats path", value="csvs/atp.csv")
wta_path = st.text_input("WTA Stats path", value="csvs/wta.csv")

do_fuzzy = st.checkbox("Fuzzy Match with Stats?", value=True)

if st.button("Run Data Prep"):
    st.write("Running data prep...")
    df = data_preparation.load_and_clean_data(
        raw_csv_path=raw_file_path,
        atp_file=atp_path,
        wta_file=wta_path,
        do_fuzzy_match=do_fuzzy,
        threshold=90,
        potential_warn=75
    )

    # Deduplicate matches
    df = data_preparation.deduplicate_matches(df)

    st.session_state["cleaned_df"] = df
    st.write("Data prep complete. Here's a preview:")
    st.dataframe(df.head(10))

st.header("Simulation")
if st.button("Run Simulation"):
    if st.session_state["cleaned_df"] is not None:
        st.write("Simulating matches...")
        sim_df = simulation.simulate_all_matches(st.session_state["cleaned_df"])
        st.session_state["sim_results"] = sim_df
        st.write("Simulation complete! Here's a preview:")
        st.dataframe(sim_df.head(10))
    else:
        st.warning("No cleaned data found. Please run data prep first.")

st.header("Results")
if st.session_state["sim_results"] is not None:
    st.write("Final simulation results:")
    st.dataframe(st.session_state["sim_results"])
