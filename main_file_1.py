import streamlit as st
import requests
import pandas as pd
from groq import Groq

# ===== CUSTOM CSS FOR COLORFUL UI =====
def inject_css():
    st.markdown("""
        <style>
        body {
            background: linear-gradient(135deg, #9b59b6, #3498db);
            color: white !important;
        }
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .menu-card {
            background-color: white;
            color: #2c3e50;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0px 4px 12px rgba(0,0,0,0.2);
            text-align: center;
            transition: 0.3s;
        }
        .menu-card:hover {
            transform: scale(1.03);
            box-shadow: 0px 6px 15px rgba(0,0,0,0.3);
        }
        .stButton>button {
            background: #2ecc71;
            color: white;
            font-size: 17px;
            padding: 10px 22px;
            border-radius: 10px;
            border: None;
            margin-top: 10px;
            width: 100%;
        }
        .stButton>button:hover {
            background: #27ae60;
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)

# ===== CONTENT GENERATOR FUNCTION =====
def generate_content(product, audience):
    return f"""
📝 **Generated Marketing Content**

🌟 **Product:** {product}  
🎯 **Audience:** {audience}  

✨ Introducing **{product}**, perfectly crafted for **{audience}**.  
Designed to meet expectations with quality, elegance, and performance!
"""

# ===== DATA ANALYSIS FUNCTION =====
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

# ===== STREAMLIT UI START =====
st.set_page_config(page_title="Multi Tool App", page_icon="🚀", layout="wide")
inject_css()

# Groq Client Init
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# Session state init
if "page" not in st.session_state:
    st.session_state.page = "welcome"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ===== WELCOME PAGE =====
if st.session_state.page == "welcome":
    st.title("👋 Welcome to Multi Tool App")
    st.markdown("### Your all-in-one creative, AI-powered tool!")
    if st.button("🚀 Start"):
        st.session_state.page = "menu"

# ===== MENU PAGE =====
elif st.session_state.page == "menu":
    st.title("📍 Choose What You Want to Use")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="menu-card">🤖<br><b>Chatbot</b><br>Talk to AI!</div>', unsafe_allow_html=True)
        if st.button("Open Chatbot"):
            st.session_state.page = "chatbot"

    with col2:
        st.markdown('<div class="menu-card">📝<br><b>Content Generator</b><br>Create text fast!</div>', unsafe_allow_html=True)
        if st.button("Open Generator"):
            st.session_state.page = "content"

    with col3:
        st.markdown('<div class="menu-card">📊<br><b>Compare & Analyze Data</b><br>From URL link</div>', unsafe_allow_html=True)
        if st.button("Analyze Data"):
            st.session_state.page = "compare"

    if st.button("🔙 Back to Welcome"):
        st.session_state.page = "welcome"

# ===== CHATBOT PAGE (UPDATED WITH GROQ) =====
elif st.session_state.page == "chatbot":
    st.title("🤖 AI Chatbot (Powered by Groq)")

    user_msg = st.text_input("💬 Type your message:")

    if user_msg:
        st.session_state.chat_history.append({"role": "user", "content": user_msg})

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=st.session_state.chat_history
        )

        bot_reply = response.choices[0].message.content
        st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})

    # Display chat history
    for chat in st.session_state.chat_history:
        if chat["role"] == "user":
            st.markdown(f"**🧑 You:** {chat['content']}")
        else:
            st.markdown(f"**🤖 Bot:** {chat['content']}")

    if st.button("🔙 Back"):
        st.session_state.page = "menu"

# ===== CONTENT GENERATOR PAGE =====
elif st.session_state.page == "content":
    st.title("📝 Content Generator")
    product = st.text_input("📦 Enter Product Name:")
    audience = st.text_input("🎯 Enter Target Audience:")
    if st.button("✨ Generate Content"):
        if product and audience:
            st.success(generate_content(product, audience))
        else:
            st.warning("⚠ Please fill both fields!")
    if st.button("🔙 Back"):
        st.session_state.page = "menu"

# ===== DATA ANALYSIS PAGE =====
elif st.session_state.page == "compare":
    st.title("📊 Compare & Analyze Data")
    url = st.text_input("🔗 Enter CSV URL:")
    if st.button("📂 Analyze Data"):
        if url:
            result, dataframe = analyze_data_from_url(url)
            if dataframe is not None:
                st.subheader("📌 Summary")
                st.json(result)
                st.subheader("📄 Preview")
                st.dataframe(dataframe.head())
            else:
                st.error(result.get("error"))
        else:
            st.warning("⚠ URL cannot be empty!")
    if st.button("🔙 Back"):
        st.session_state.page = "menu"
