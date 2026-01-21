import streamlit as st
from groq import Groq
import pandas as pd
import io

# Google Drive Upload Imports
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload


# ===================== FANTASY UI THEME CSS =====================
def inject_css():
    st.markdown("""
        <style>
        /* ===== GLOBAL BACKGROUND ===== */
        body {
            background: radial-gradient(circle at 20% 20%, #382B73, #0F0E24 60%, #000000);
            background-attachment: fixed;
            color: #E4E4F1 !important;
            font-family: 'Trebuchet MS', sans-serif;
        }

        /* ===== STARFIELD ANIMATION ===== */
        body::before {
            content: "";
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background-image: url('https://i.imgur.com/7bFQq3d.png');
            background-size: cover;
            background-position: center;
            opacity: 0.15;
            animation: floatStars 60s linear infinite;
            pointer-events: none;
            z-index: -1;
        }
        @keyframes floatStars {
            0% {background-position: 0 0;}
            100% {background-position: -3000px 3000px;}
        }

        /* ===== GLASS CONTAINER ===== */
        .main .block-container {
            backdrop-filter: blur(14px);
            background: rgba(255,255,255,0.07);
            border-radius: 18px;
            padding: 2.5rem;
            box-shadow: 0px 10px 40px rgba(0,0,0,0.5);
            margin-top: 2rem;
        }

        /* ===== MENU CARDS ===== */
        .menu-card {
            border-radius: 18px;
            padding: 25px;
            text-align: center;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.25);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            color: #E6E6FA;
            font-size: 1.1rem;
        }
        .menu-card:hover {
            transform: translateY(-6px) scale(1.03);
            box-shadow: 0px 10px 35px rgba(0,0,0,0.7);
            border: 1px solid rgba(255,255,255,0.6);
        }

        /* ===== NEON BUTTONS ===== */
        .stButton>button {
            background: linear-gradient(135deg, #5118C4, #A020F0);
            color: white;
            padding: 12px 26px;
            border-radius: 12px;
            font-size: 17px;
            border: none;
            letter-spacing: 0.4px;
            cursor: pointer;
            transition: 0.3s ease;
            box-shadow: 0px 0px 10px rgba(150, 55, 200, 0.8);
        }
        .stButton>button:hover {
            background: linear-gradient(135deg, #6B2CF5, #C334FF);
            box-shadow: 0px 0px 20px rgba(200, 120, 255, 1);
            transform: scale(1.05);
        }

        /* ===== TEXT INPUT ===== */
        .stTextInput>div>div>input {
            background: rgba(255,255,255,0.15) !important;
            border-radius: 10px;
            color: #E6E6FA !important;
            border: 1px solid rgba(255,255,255,0.3) !important;
        }

        textarea {
            background: rgba(255,255,255,0.12) !important;
            color: #E6E6FA !important;
            border: 1px solid rgba(255,255,255,0.3) !important;
            border-radius: 12px !important;
        }

        .stSelectbox>div>div {
            background: rgba(255,255,255,0.15) !important;
            color: #E6E6FA !important;
            border-radius: 10px !important;
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
        creds_info,
        scopes=["https://www.googleapis.com/auth/drive.file"]
    )
    return build('drive', 'v3', credentials=creds)


def upload_to_drive(filename, text_content):
    service = get_drive_service()

    metadata = {'name': filename, 'mimeType': 'text/plain'}
    fh = io.BytesIO(text_content.encode('utf-8'))
    media = MediaIoBaseUpload(fh, mimetype='text/plain', resumable=True)
    file = service.files().create(body=metadata, media_body=media, fields='id,name').execute()

    return file.get('id'), file.get('name')


# ===================== CSV ANALYSIS =====================
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


# ===================== APP START =====================
st.set_page_config(page_title="Honnagiri Multi Tool", page_icon="🚀", layout="wide")
inject_css()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "page" not in st.session_state:
    st.session_state.page = "welcome"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "generated_text" not in st.session_state:
    st.session_state.generated_text = ""


# ===================== WELCOME PAGE =====================
if st.session_state.page == "welcome":
    st.title("🌌 Welcome to Honnagiri Universe Tools")
    st.write("A multi-dimensional AI suite across galaxies ✨")
    if st.button("🚀 Enter the Portal"):
        st.session_state.page = "menu"


# ===================== MENU PAGE =====================
elif st.session_state.page == "menu":
    st.title("🪐 Choose Your Cosmic Tool")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="menu-card">🤖<br><b>Chatbot</b><br>Talk to AI</div>', unsafe_allow_html=True)
        if st.button("Open Chatbot"):
            st.session_state.page = "chatbot"

    with col2:
        st.markdown('<div class="menu-card">📝<br><b>Content Generator</b><br>Export to Drive</div>', unsafe_allow_html=True)
        if st.button("Open Generator"):
            st.session_state.page = "content"

    with col3:
        st.markdown('<div class="menu-card">📊<br><b>Data Analyzer</b><br>CSV Insights</div>', unsafe_allow_html=True)
        if st.button("Analyze Data"):
            st.session_state.page = "compare"

    if st.button("🔙 Back to Welcome"):
        st.session_state.page = "welcome"


# ===================== CHATBOT =====================
elif st.session_state.page == "chatbot":
    st.title("🤖 Honnagiri Chatbot (Groq Powered)")

    user_msg = st.text_input("💬 Speak to the AI:")

    if user_msg:
        st.session_state.chat_history.append({"role": "user", "content": user_msg})

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=st.session_state.chat_history,
        )

        st.session_state.chat_history.append(
            {"role": "assistant", "content": response.choices[0].message.content}
        )

    for chat in st.session_state.chat_history:
        prefix = "🧑 You:" if chat["role"] == "user" else "🤖 Bot:"
        st.markdown(f"**{prefix}** {chat['content']}")

    if st.button("🔙 Back"):
        st.session_state.page = "menu"


# ===================== CONTENT GENERATOR =====================
elif st.session_state.page == "content":
    st.title("📝 Honnagiri Content Generator → Google Drive")
    st.info("Generated files are stored inside the service account's Google Drive.")

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

        with st.spinner("🧠 Generating …"):
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}]
            )
            st.session_state.generated_text = response.choices[0].message.content

    if st.session_state.generated_text:
        st.subheader("✨ Output")
        st.text_area("Preview", st.session_state.generated_text, height=250)

        file_name = st.text_input("Filename (ex: marketing.txt)", value="honnagiri_marketing.txt")

        if st.button("📤 Upload to Google Drive"):
            try:
                with st.spinner("Uploading..."):
                    file_id, name = upload_to_drive(file_name, st.session_state.generated_text)
                    st.success(f"✅ Uploaded as {name}")
                    st.write(f"📎 File ID: `{file_id}`")
            except Exception as e:
                st.error(f"Error: {e}")

    if st.button("🔙 Back"):
        st.session_state.page = "menu"


# ===================== COMPARISON PAGE =====================
elif st.session_state.page == "compare":
    st.title("📊 CSV Data Analyzer")
    url = st.text_input("🔗 CSV URL:")

    if st.button("📂 Analyze"):
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
            st.warning("⚠ Enter a valid URL")

    if st.button("🔙 Back"):
        st.session_state.page = "menu"
