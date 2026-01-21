import streamlit as st
from groq import Groq
import pandas as pd
import io
import requests
from bs4 import BeautifulSoup

# Google Drive Upload Imports
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload


# ===================== FANTASY UI THEME CSS =====================
def inject_css():
    st.markdown("""
        <style>
        body {
            background: radial-gradient(circle at 20% 20%, #382B73, #0F0E24 60%, #000000);
            background-attachment: fixed;
            color: #E4E4F1 !important;
            font-family: 'Trebuchet MS', sans-serif;
        }
        body::before {
            content: "";
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background-image: url('https://i.imgur.com/7bFQq3d.png');
            background-size: cover;
            opacity: 0.15;
            animation: floatStars 60s linear infinite;
            pointer-events: none;
            z-index: -1;
        }
        @keyframes floatStars {
            0% {background-position: 0 0;}
            100% {background-position: -3000px 3000px;}
        }
        .main .block-container {
            backdrop-filter: blur(14px);
            background: rgba(255,255,255,0.07);
            border-radius: 18px;
            padding: 2.5rem;
            box-shadow: 0px 10px 40px rgba(0,0,0,0.5);
            margin-top: 2rem;
        }
        .menu-card {
            border-radius: 18px;
            padding: 25px;
            text-align: center;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.25);
            transition: 0.3s ease;
            color: #E6E6FA;
            font-size: 1.1rem;
        }
        .menu-card:hover {
            transform: translateY(-6px) scale(1.03);
            box-shadow: 0px 10px 35px rgba(0,0,0,0.7);
            border: 1px solid rgba(255,255,255,0.6);
        }
        .stButton>button {
            background: linear-gradient(135deg, #5118C4, #A020F0);
            color: white;
            padding: 12px 26px;
            border-radius: 12px;
            font-size: 17px;
            cursor: pointer;
            transition: 0.3s;
        }
        .stButton>button:hover {
            background: linear-gradient(135deg, #6B2CF5, #C334FF);
            transform: scale(1.05);
        }
        .stTextInput>div>div>input, textarea {
            background: rgba(255,255,255,0.15)!important;
            border-radius: 10px!important;
            color: #E6E6FA!important;
            border: 1px solid rgba(255,255,255,0.3)!important;
        }
        h1, h2, h3 {
            color: #E6E6FA !important;
            text-shadow: 0px 0px 8px rgba(130, 80, 255, 0.9);
        }
        </style>
    """, unsafe_allow_html=True)


# ===================== GOOGLE DRIVE SERVICE =====================
def get_drive_service():
    creds_info = st.secrets["gcp_service_account"]
    creds = service_account.Credentials.from_service_account_info(
        creds_info, scopes=["https://www.googleapis.com/auth/drive.file"]
    )
    return build('drive', 'v3', credentials=creds)

def upload_to_drive(filename, text_content):
    service = get_drive_service()
    metadata = {'name': filename, 'mimeType': 'text/plain'}
    fh = io.BytesIO(text_content.encode('utf-8'))
    media = MediaIoBaseUpload(fh, mimetype='text/plain', resumable=True)
    file = service.files().create(body=metadata, media_body=media, fields='id,name').execute()
    return file.get('id'), file.get('name')


# ===================== UNIVERSAL WEBSITE ANALYZER =====================
def extract_visible_text(html):
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "meta", "noscript", "header", "footer", "nav"]):
        tag.decompose()

    text = " ".join(soup.stripped_strings)
    return text


def analyze_website(url, client):
    try:
        head = requests.head(url, allow_redirects=True, timeout=10)
        content_type = head.headers.get("Content-Type", "")

        if "pdf" in content_type.lower():
            return "**PDF detected. PDF parsing not implemented yet.**"

        response = requests.get(url, timeout=10)
        html = response.text
        text = extract_visible_text(html)
        cleaned = text[:7000]

        prompt = f"""
You are an AI that analyzes any kind of website content.

Task:
1. If the website contains placement or career info, extract these fields:
   - University/Organization Name
   - Placement/Recruitment stats
   - Avg Package
   - Highest Package
   - Top Recruiters
   - Number of Students Placed
   - Summary

2. If the website does NOT contain placement/career info:
   - Identify purpose of the website
   - Provide a short structured summary
   - Highlight key topics and findings

Content to analyze:
\"\"\" 
{cleaned} 
\"\"\"

Return output in clean bullet points.
"""

        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return res.choices[0].message.content

    except Exception as e:
        return f"❌ Error: {e}"


# ===================== STREAMLIT =====================
st.set_page_config(page_title="Honnagiri Multi Tool", page_icon="🚀", layout="wide")
inject_css()
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "page" not in st.session_state:
    st.session_state.page = "welcome"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "generated_text" not in st.session_state:
    st.session_state.generated_text = ""


# ===================== PAGES =====================
if st.session_state.page == "welcome":
    st.title("🌌 Welcome to Honnagiri Universe Tools")
    st.write("A multi-dimensional AI suite across galaxies ✨")
    if st.button("🚀 Enter the Portal"):
        st.session_state.page = "menu"

elif st.session_state.page == "menu":
    st.title("🪐 Choose Your Cosmic Tool")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="menu-card">🤖<br><b>Chatbot</b></div>', unsafe_allow_html=True)
        if st.button("Open Chatbot"):
            st.session_state.page = "chatbot"

    with col2:
        st.markdown('<div class="menu-card">📝<br><b>Content Generator</b></div>', unsafe_allow_html=True)
        if st.button("Open Generator"):
            st.session_state.page = "content"

    with col3:
        st.markdown('<div class="menu-card">🌍<br><b>Website Analyzer</b></div>', unsafe_allow_html=True)
        if st.button("Analyze Data"):
            st.session_state.page = "compare"

    if st.button("🔙 Back to Welcome"):
        st.session_state.page = "welcome"


elif st.session_state.page == "chatbot":
    st.title("🤖 Honnagiri Chatbot (Groq Powered)")
    msg = st.text_input("💬 Speak to the AI:")
    if msg:
        st.session_state.chat_history.append({"role": "user", "content": msg})
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=st.session_state.chat_history
        )
        st.session_state.chat_history.append({"role": "assistant", "content": r.choices[0].message.content})

    for chat in st.session_state.chat_history:
        prefix = "🧑 You" if chat["role"] == "user" else "🤖 Bot"
        st.markdown(f"**{prefix}:** {chat['content']}")

    if st.button("🔙 Back"):
        st.session_state.page = "menu"


elif st.session_state.page == "content":
    st.title("📝 Honnagiri Content Generator → Google Drive")
    product = st.text_input("Product / Service Name")
    audience = st.text_input("Target Audience")
    tone = st.selectbox("Tone", ["Professional", "Casual", "Exciting"])

    if st.button("✨ Generate Content"):
        prompt = f"""
Create marketing content for:
Product: {product}
Audience: {audience}
Tone: {tone}
Generate:
1. Ad copy
2. Email subject
3. LinkedIn post
"""
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        st.session_state.generated_text = r.choices[0].message.content

    if st.session_state.generated_text:
        st.text_area("Generated Content", st.session_state.generated_text, height=240)
        file_name = st.text_input("Filename:", value="honnagiri_marketing.txt")
        if st.button("📤 Upload to Drive"):
            with st.spinner("Uploading…"):
                file_id, name = upload_to_drive(file_name, st.session_state.generated_text)
                st.success(f"Uploaded as {name}")
                st.write(f"File ID: {file_id}")

    if st.button("🔙 Back"):
        st.session_state.page = "menu"


elif st.session_state.page == "compare":
    st.title("🌍 Universal Website Analyzer")
    url = st.text_input("🔗 Enter any website URL:")

    if st.button("📡 Analyze Site"):
        if url:
            with st.spinner("Fetching & Analyzing…"):
                result = analyze_website(url, client)
                st.subheader("📌 Analysis Result")
                st.write(result)
        else:
            st.warning("Enter a valid URL")

    if st.button("🔙 Back"):
        st.session_state.page = "menu"
