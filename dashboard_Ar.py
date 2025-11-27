import streamlit as st
import pandas as pd 
import os


st.title("welcom to my first dashboard")
st.write("this is my first dashboard using streamlit")


df = pd.read_csv('dataset/actual_PV_2025.csv')

name = st.text_input("Enter your name", "Guest")
if name:
    st.write(f"Hello, {name}!")

if st.checkbox("Show raw data"):
    st.dataframe(df)      

col = st.selectbox("Select column to view", options=["Area", "Production Type", "Generation (MWh)"])
st.write(df[["datetime", col]])