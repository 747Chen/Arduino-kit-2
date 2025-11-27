# python
import streamlit as st
import pandas as pd

# Simple DataFrame
df = pd.DataFrame({
    "Category": ["A", "B", "C", "D"],
    "Value1": [10, 25, 15, 30],
    "Value2": [5, 12, 8, 20]
})

# App UI
st.title("Simple Streamlit Dashboard Tutorial")
st.write("This demo shows a DataFrame and basic Streamlit widgets.")

#Understanding widgets: name
name = st.text_input("Enter your name", "Guest")
if name:
    st.write(f"Hello, {name}!")

# Show raw data
if st.checkbox("Show raw data"):
    st.dataframe(df)

# Select column to inspect
col = st.selectbox("Select column to view", options=["Value1", "Value2"])
st.write(f"Showing column: {col}")

# Slider to filter rows by selected column
min_val, max_val = int(df[col].min()), int(df[col].max())
low, high = st.slider("Filter by value range", min_val, max_val, (min_val, max_val))
filtered = df[df[col].between(low, high)]
st.write(f"Filtered rows: {len(filtered)}")
st.dataframe(filtered)

# Button to show a chart
if st.button("Show line chart"):
    st.line_chart(filtered.set_index("Category")[[col]])

# Simple summary
st.write("Summary statistics:")
st.write(df.describe())
