import streamlit as st
import pandas as pd

import plotly

# ============================================================================
# SIDEBAR
# ============================================================================
with st.sidebar:
    st.header("Sidebar")
    name = st.text_input("Your name:", "Student")
    age = st.slider("Your age:", 18, 65, 25)

st.write(f"Hello, {name}! You are {age} years old.")


df = pd.read_csv("Wind_2025_1.csv")
df1 = pd.read_csv("../2025-26-Data-driven/Gen_data/Wind_2022.csv")

st.title("Wind Power Data")
st.write("This is a simple dashboard to show the wind power data for 2025.")

# widgets:name
name = st.text_input("Enter your name", "Guest")
if name:
    st.write(f"Hello, {name}!")

# show raw data
if st.checkbox("Show raw data"):
    st.dataframe(df)

# select column to inspect
time_columns = [col for col in df.columns[:5] if 'time' in col.lower()]
if time_columns:
    time_column = time_columns[0]  # Use the first column that contains 'time'
else:
    time_column = "hourly__time"  # fallback to default

# Filter out non-numeric columns
numeric_columns = [col for col in df.columns if col != time_column and pd.api.types.is_numeric_dtype(df[col])]
col = st.selectbox("Select column to view", options=numeric_columns)
st.write(f"Showing column: {col}")

# Slider to filter rows by selected column
min_val, max_val = float(df[col].min()), float(df[col].max())
low, high = st.slider("Filter by value range", min_val, max_val, (min_val, max_val), step=0.1)
filtered = df[df[col].between(low, high)]
st.write(f"Filtered rows: {len(filtered)}")
st.dataframe(filtered)

# button to show line chart
if st.button("Show line chart"):
    st.line_chart(df.set_index("hourly__time")[[col]])

# write summary
st.write("Summary statistics:")
st.write(df.describe())
