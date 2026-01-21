import streamlit as st
import requests
import pandas as pd

# ---- CHATBOT DUMMY FUNCTION ----
def chatbot_response(user_msg):
    return f"Chatbot Response: You said → {user_msg}"

# ---- CONTENT GENERATION FUNCTION ----
def generate_content(product, audience):
    return f"""
    Marketing Content:
    Product: {product}
    Target Audience: {audience}

    Sample Output:
    Introducing {product}! Perfect for {audience}, designed to meet needs with quality and value.
    """

# ---- DATA COMPARISON & ANALYSIS FUNCTION ----
def analyze_data_from_url(url):
    try:
        df = pd.read_csv(url)
        analysis = {
            "Rows": df.shape[0],
            "Columns": df.shape[1],
            "Missing Values": df.isnull().sum().to_dict(),
            "Column Types": df.dtypes.astype(str).to_dict()
        }
        return analysis, df
    except Exception as e:
        return {"error": str(e)}, None

# ---- STREAMLIT UI ----

st.set_page_config(page_title="Multi Tool App", page_icon="🚀", layout="centered")

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "welcome"

# --- PAGE: WELCOME ---
if st.session_state.page == "welcome":
    st.title("👋 Welcome!")
    st.write("Click below to start using the app")
    if st.button("Continue"):
        st.session_state.page = "menu"

# --- PAGE: MENU ---
elif st.session_state.page == "menu":
    st.title("Select a Tool")
    st.write("Choose one of the following options:")
    if st.button("🤖 Chatbot"):
        st.session_state.page = "chatbot"
    if st.button("📝 Content Generator"):
        st.session_state.page = "content"
    if st.button("📊 Compare & Analyze Data"):
        st.session_state.page = "compare"
    if st.button("⬅ Back"):
        st.session_state.page = "welcome"

# --- PAGE: CHATBOT ---
elif st.session_state.page == "chatbot":
    st.title("🤖 Chatbot")
    user_input = st.text_input("Enter your message:")
    if user_input:
        response = chatbot_response(user_input)
        st.success(response)
    if st.button("⬅ Back"):
        st.session_state.page = "menu"

# --- PAGE: CONTENT GENERATOR ---
elif st.session_state.page == "content":
    st.title("📝 Content Generator")
    product = st.text_input("Enter Product Name:")
    audience = st.text_input("Enter Target Audience:")
    if st.button("Generate"):
        if product and audience:
            output = generate_content(product, audience)
            st.success(output)
        else:
            st.warning("Please fill both fields!")
    if st.button("⬅ Back"):
        st.session_state.page = "menu"

# --- PAGE: DATA COMPARISON & ANALYSIS ---
elif st.session_state.page == "compare":
    st.title("📊 Compare & Analyze Data from URL")
    url = st.text_input("Enter CSV URL:")
    if st.button("Analyze"):
        if url:
            result, dataframe = analyze_data_from_url(url)
            if dataframe is not None:
                st.subheader("Basic Analysis")
                st.json(result)
                st.subheader("Preview Data")
                st.dataframe(dataframe.head())
            else:
                st.error(result.get("error"))
        else:
            st.warning("URL cannot be empty!")
    if st.button("⬅ Back"):
        st.session_state.page = "menu"
