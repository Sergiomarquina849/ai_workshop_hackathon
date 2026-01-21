import streamlit as st
import requests
import pandas as pd

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
        .back-btn>button {
            background: #e74c3c !important;
        }
        </style>
    """, unsafe_allow_html=True)


# ===== FUNCTIONS =====
def chatbot_response(user_msg):
    return f"🤖 Chatbot: You said → {user_msg}"

def generate_content(product, audience):
    return f"""
📝 **Generated Marketing Content**

🌟 **Product:** {product}  
🎯 **Audience:** {audience}  

✨ Introducing **{product}**, perfectly crafted for **{audience}**.  
Designed to meet expectations with quality, elegance, and performance!
"""

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

if "page" not in st.session_state:
    st.session_state.page = "welcome"

# ===== WELCOME PAGE =====
if st.session_state.page == "welcome":
    st.title("👋 Welcome to Multi Tool App")
    st.markdown("### Your all-in-one creative, AI-powered tool!")
    st.write("")
    if st.button("🚀 Start"):
        st.session_state.page = "menu"

# ===== MENU PAGE =====
elif st.session_state.page == "menu":
    st.title("📍 Choose What You Want to Use")
    st.write("Select one of the features below:")
    st.write("")

    col1, col2, col3 = st.columns(3)

    with col1:
        with st.container():
            st.markdown('<div class="menu-card">🤖<br><b>Chatbot</b><br>Talk to AI!</div>', unsafe_allow_html=True)
            if st.button("Open Chatbot"):
                st.session_state.page = "chatbot"

    with col2:
        with st.container():
            st.markdown('<div class="menu-card">📝<br><b>Content Generator</b><br>Create text fast!</div>', unsafe_allow_html=True)
            if st.button("Open Generator"):
                st.session_state.page = "content"

    with col3:
        with st.container():
            st.markdown('<div class="menu-card">📊<br><b>Compare & Analyze Data</b><br>From URL link</div>', unsafe_allow_html=True)
            if st.button("Analyze Data"):
                st.session_state.page = "compare"

    st.write("")
    if st.button("🔙 Back to Welcome"):
        st.session_state.page = "welcome"

# ===== CHATBOT PAGE =====
elif st.session_state.page == "chatbot":
    st.title("🤖 Chatbot")
    user_input = st.text_input("💬 Enter your message:")
    if user_input:
        st.success(chatbot_response(user_input))
    if st.button("🔙 Back", key="b1"):
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
    if st.button("🔙 Back", key="b2"):
        st.session_state.page = "menu"

# ===== COMPARE & ANALYZE PAGE =====
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
    if st.button("🔙 Back", key="b3"):
        st.session_state.page = "menu"
