import streamlit as st

st.title("Layout Tutorial")

# ============================================================================
# SIDEBAR
# ============================================================================
with st.sidebar:
    st.header("Sidebar")
    name = st.text_input("Your name:", "Student")
    age = st.slider("Your age:", 18, 65, 25)

st.write(f"Hello, {name}! You are {age} years old.")

# ============================================================================
# COLUMNS
# ============================================================================
st.header("Columns")
col1, col2, col3 = st.columns(3)

with col1:
    st.write("**Column 1**")
    st.button("Button 1")

with col2:
    st.write("**Column 2**")
    st.button("Button 2")

with col3:
    st.write("**Column 3**")
    st.button("Button 3")

# ============================================================================
# TABS
# ============================================================================
st.header("Tabs")
tab1, tab2 = st.tabs(["Tab A", "Tab B"])

with tab1:
    st.write("This is Tab A")
    st.write("Content in first tab")

with tab2:
    st.write("This is Tab B")
    st.write("Content in second tab")

# ============================================================================
# EXPANDER
# ============================================================================
st.header("Expander")

with st.expander("Click to expand"):
    st.write("This was hidden!")
    st.write("Expanders save space.")

# ============================================================================
# CONTAINER
# ============================================================================
st.header("Container")

with st.container(border=True):
    st.write("This is inside a container")
    st.write("Everything here is grouped together")