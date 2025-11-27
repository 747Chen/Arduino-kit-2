import streamlit as st
import pandas as pd
import numpy as np

# Sample data (we'll create proper function below)
df = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=30),
    'temperature': np.random.randint(15, 30, 30),
    'humidity': np.random.randint(40, 80, 30)
})

# Line chart - best for trends over time
st.line_chart(df.set_index('date')['temperature'])

# Bar chart - best for comparisons
st.bar_chart(df.set_index('date')['humidity'])

# Area chart - best for cumulative/magnitude
st.area_chart(df.set_index('date')[['temperature', 'humidity']])