import streamlit as st
from groq import Groq
import pandas as pd
import requests
import io

# Google Drive Upload Imports
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

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


# ===== GOOGLE DRIVE SERVICE ACCOUNT LOGIC =====
def get_drive_service():
    creds_info = st.secrets["gcp_service_account"]
    creds = service_account.Credentials.from_service_account_info(
        creds_info,
        scopes=["https://www.googleapis.com/auth/drive.file"]
    )
    return build('drive', 'v3', credentials=creds)


def upload_to_drive(filename, text_content):
    service = get_drive_service()

    metadata = {
        'name': filename,
        'mimeType': 'text/plain'
    }

    fh = io.BytesIO(text_content.encode('utf-8'))
    media = MediaIoBaseUpload(fh, mimetype='text/plain', resumable=True)

    file = service.files().create(
        body=metadata,
        media_body=media,
        fields='id, name'
    ).execute()

    return file.get('id'), file.get('name')


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


# ===== STREAMLIT INITIAL CONFIG =====
st.set_page_config(page_title="Honnagiri Multi Tool App", page_icon="🚀", layout="wide")
inject_css()

# Init Groq Client
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# Session State
if "page" not in st.session_state:
    st.session_state.page = "welcome"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "generated_text" not in st.session_state:
    st.session_state.generated_text = ""


# ===== WELCOME PAGE =====
if st.session_state.page == "welcome":
    st.title("👋 Welcome to Honnagiri Multi Tool App")
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
        st.markdown('<div class="menu-card">📝<br><b>Content Generator</b><br>Export to Drive</div>', unsafe_allow_html=True)
        if st.button("Open Generator"):
            st.session_state.page = "content"

    with col3:
        st.markdown('<div class="menu-card">📊<br><b>Analyze Data</b><br>From CSV URL</div>', unsafe_allow_html=True)
        if st.button("Analyze Data"):
            st.session_state.page = "compare"

    if st.button("🔙 Back to Welcome"):
        st.session_state.page = "welcome"


# ===== CHATBOT PAGE =====
elif st.session_state.page == "chatbot":
    st.title("🤖 Honnagiri AI Chatbot (Powered by Groq)")
    user_msg = st.text_input("💬 Type your message:")

    if user_msg:
        st.session_state.chat_history.append({"role": "user", "content": user_msg})

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=st.session_state.chat_history
        )

        bot_reply = response.choices[0].message.content
        st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})

    for chat in st.session_state.chat_history:
        if chat["role"] == "user":
            st.markdown(f"**🧑 You:** {chat['content']}")
        else:
            st.markdown(f"**🤖 Bot:** {chat['content']}")

    if st.button("🔙 Back"):
        st.session_state.page = "menu"


# ===== CONTENT GENERATOR PAGE (RENAMED) =====
elif st.session_state.page == "content":
    st.title("📢 Honnagiri Marketing Content Generator (Google Drive Export)")
    st.info("Files will be uploaded to the service account's Google Drive.")

    product = st.text_input("Product / Service Name")
    audience = st.text_input("Target Audience")
    tone = st.selectbox("Tone", ["Professional", "Casual", "Exciting"])

    if st.button("Generate Content"):
        prompt = f"Create marketing content for:\nProduct: {product}\nAudience: {audience}\nTone: {tone}\n\nGenerate: 1. Ad copy 2. Email subject 3. LinkedIn post"

        with st.spinner("Generating..."):
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
            )
            st.session_state.generated_text = response.choices[0].message.content

    if st.session_state.generated_text:
        st.subheader("✨ Generated Content")
        st.text_area("Preview", st.session_state.generated_text, height=200)

        file_name = st.text_input("File name to upload (e.g. marketing.txt)", value="honnagiri_content.txt")

        if st.button("Upload to Google Drive"):
            try:
                with st.spinner("Uploading..."):
                    file_id, name = upload_to_drive(file_name, st.session_state.generated_text)
                    st.success(f"✅ File '{name}' uploaded successfully!")
                    st.write(f"🔗 File ID: `{file_id}`")
            except Exception as e:
                st.error(f"❌ Upload failed: {e}")

    if st.button("🔙 Back"):
        st.session_state.page = "menu"


# ===== DATA ANALYSIS PAGE =====
elif st.session_state.page == "compare":
    st.title("📊 Analyze CSV from URL")
    url = st.text_input("🔗 Enter CSV URL:")

    if st.button("📂 Analyze Data"):
        if url:
            result, df = analyze_data_from_url(url)
            if df is not None:
                st.subheader("📌 Summary")
                st.json(result)
                st.subheader("📄 Preview")
                st.dataframe(df.head())
            else:
                st.error(result.get("error"))
        else:
            st.warning("⚠ URL cannot be empty!")

    if st.button("🔙 Back"):
        st.session_state.page = "menu"
