import streamlit as st
from groq import Groq
import requests
from bs4 import BeautifulSoup
import io

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload


# ===================== UI THEME =====================
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
            pointer-events: none;
            z-index: -1;
        }
        .feature-card {
            border-radius: 18px;
            padding: 28px;
            text-align: center;
            font-weight: 600;
            font-size: 1.2rem;
            color: white;
            border: 2px solid rgba(255,255,255,0.3);
            cursor: pointer;
            transition: .35s;
            box-shadow: 0 0 12px rgba(255,255,255,0.25);
        }
        .feature-card:hover {
            transform: scale(1.05) translateY(-6px);
            box-shadow: 0 0 25px rgba(255,255,255,0.6);
        }
        .chatbot-box { background: linear-gradient(135deg,#6A11CB,#2575FC); }
        .content-box { background: linear-gradient(135deg,#00B4DB,#0083B0); }
        .web-box { background: linear-gradient(135deg,#FF8008,#FFC837); color:#222; }

        .stButton>button {
            background: linear-gradient(135deg,#5118C4,#A020F0);
            color:white; padding:12px 26px;
            border-radius:10px; border:none;
            font-size:16px; transition:.3s;
        }
        .stButton>button:hover { transform:scale(1.05); }

        textarea, .stTextInput>div>div>input {
            background:rgba(255,255,255,0.15)!important;
            border-radius:10px!important;
            color:#E6E6FA!important;
            border:1px solid rgba(255,255,255,0.3)!important;
        }
        </style>
    """, unsafe_allow_html=True)


# ===================== GOOGLE DRIVE =====================
def get_drive_service():
    creds_info = st.secrets["gcp_service_account"]
    creds = service_account.Credentials.from_service_account_info(
        creds_info, scopes=["https://www.googleapis.com/auth/drive.file"]
    )
    return build('drive','v3',credentials=creds)

def upload_to_drive(filename, text):
    service = get_drive_service()
    fh = io.BytesIO(text.encode('utf-8'))
    media = MediaIoBaseUpload(fh, mimetype='text/plain', resumable=True)
    file = service.files().create(
        body={'name': filename, 'mimeType':'text/plain'},
        media_body=media,
        fields='id,name').execute()
    return file.get('id'), file.get('name')


# ===================== WEBSITE ANALYZER =====================
def extract_visible_text(html):
    soup = BeautifulSoup(html,"html.parser")
    for t in soup(["script","style","meta","header","nav","footer","noscript"]):
        t.decompose()
    return " ".join(soup.stripped_strings)

def analyze_website(url, client):
    try:
        response = requests.get(url, timeout=10)
        text = extract_visible_text(response.text)[:6000]

        prompt = f"""
Analyze this website content.

If placement/career info exists:
- Extract the stats & summarize

Else:
- Summarize purpose
- Explain key sections
- Explain offerings

Rules:
- No justification
- No mentioning absence
- Only bullet points

Content:
\"\"\"{text}\"\"\"
"""
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":prompt}]
        )
        return r.choices[0].message.content

    except Exception as e:
        return f"❌ Error: {e}"


# ===================== STREAMLIT =====================
st.set_page_config(page_title="Honnagiri Multi Tool", page_icon="🚀", layout="wide")
inject_css()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "page" not in st.session_state: st.session_state.page="welcome"
if "chat_history" not in st.session_state: st.session_state.chat_history=[]
if "generated_text" not in st.session_state: st.session_state.generated_text=""


# ===================== PAGES =====================
if st.session_state.page=="welcome":
    st.title("🌌 Welcome to Honnagiri Universe Tools")
    if st.button("🚀 Start"):
        st.session_state.page="menu"

elif st.session_state.page=="menu":
    st.title("🪐 Choose Your Tool")
    c1,c2,c3 = st.columns(3)

    with c1:
        st.markdown("<div class='feature-card chatbot-box'>🤖<br>Chatbot</div>", unsafe_allow_html=True)
        if st.button("Chat"):
            st.session_state.page="chatbot"

    with c2:
        st.markdown("<div class='feature-card content-box'>📝<br>Content Generator</div>", unsafe_allow_html=True)
        if st.button("Generate Content"):
            st.session_state.page="content"

    with c3:
        st.markdown("<div class='feature-card web-box'>🌍<br>Website Analyzer</div>", unsafe_allow_html=True)
        if st.button("Analyze"):
            st.session_state.page="analyzer"

    if st.button("🔙 Exit"):
        st.session_state.page="welcome"


elif st.session_state.page=="chatbot":
    st.title("🤖 Honnagiri Chatbot")
    msg = st.text_input("💬 Say something:")
    if msg:
        st.session_state.chat_history.append({"role":"user","content":msg})
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=st.session_state.chat_history)
        st.session_state.chat_history.append({"role":"assistant","content":r.choices[0].message.content})

    for chat in st.session_state.chat_history:
        st.write(f"**{'🧑' if chat['role']=='user' else '🤖'}:** {chat['content']}")

    if st.button("🔙 Back"):
        st.session_state.page="menu"


elif st.session_state.page=="content":
    st.title("📝 Honnagiri Content Generator")

    topic = st.text_input("🧾 What content do you need?")
    audience = st.text_input("🎯 Who is the audience?")

    if st.button("✨ Generate"):
        prompt = f"Write engaging marketing content about '{topic}' for the target audience '{audience}'."
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":prompt}]
        )
        st.session_state.generated_text = r.choices[0].message.content

    if st.session_state.generated_text:
        st.write(st.session_state.generated_text)
        filename = st.text_input("File name:", value="content.txt")
        if st.button("📤 Upload to Drive"):
            upload_to_drive(filename, st.session_state.generated_text)
            st.success("Uploaded!")

    if st.button("🔙 Back"):
        st.session_state.page="menu"


elif st.session_state.page=="analyzer":
    st.title("🌍 Universal Website Analyzer")
    url = st.text_input("🔗 Paste website URL:")
    if st.button("📡 Analyze"):
        if url:
            with st.spinner("Reading site..."):
                st.write(analyze_website(url, client))
        else:
            st.warning("Enter a valid URL.")
    if st.button("🔙 Back"):
        st.session_state.page="menu"
