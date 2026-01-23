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

#------model 4----------
import streamlit as st
from groq import Groq
import requests
from bs4 import BeautifulSoup
import json
import io
import re

import PyPDF2
import docx2txt
from docx import Document
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

from PIL import Image


# ===================== THEME =====================
def inject_css():
    st.markdown("""
    <style>
    body {
        background: linear-gradient(135deg, #0a0f26, #120a35, #1a0f50);
        background-size: 300% 300%;
        animation: bgShift 12s ease infinite;
        color: #E4E4F1 !important;
        font-family: 'Poppins', sans-serif;
    }
    @keyframes bgShift {
        0% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }
    .feature-card {
        backdrop-filter: blur(12px);
        border-radius: 20px;
        padding: 32px;
        text-align: center;
        color: #E6E6FA;
        font-weight: 600;
        font-size: 1.2rem;
        border: 2px solid rgba(255,255,255,0.18);
        background: rgba(255,255,255,0.08);
        box-shadow: 0 0 25px rgba(99, 70, 255, 0.4);
        transition: 0.4s;
        cursor: pointer;
    }
    .feature-card:hover {
        transform: scale(1.06) translateY(-6px);
        box-shadow: 0 0 35px rgba(137, 98, 255, 0.8);
    }
    textarea, .stTextInput>div>div>input {
        background:rgba(255,255,255,0.15)!important;
        border-radius:10px!important;
        color:#E6E6FA!important;
        border:1px solid rgba(255,255,255,0.3)!important;
    }
    .stButton>button {
        background: linear-gradient(135deg,#6D28D9,#4C1D95);
        color:white;
        padding:10px 22px;
        border-radius:10px;
        border:none;
        font-size:14px;
        font-weight:600;
        box-shadow:0 0 12px rgba(139,92,246,0.8);
        transition:0.3s;
    }
    .stButton>button:hover {
        transform:translateY(-3px) scale(1.03);
        box-shadow:0 0 18px rgba(167,139,250,1);
    }
    </style>
    """, unsafe_allow_html=True)


# ===================== WEBSITE UTILITIES =====================
def extract_visible_text(html):
    soup = BeautifulSoup(html,"html.parser")
    for t in soup(["script","style","meta","header","nav","footer","noscript"]):
        t.decompose()
    return " ".join(soup.stripped_strings)


# ===================== WEBSITE ANALYZER =====================
def analyze_website(url, client):
    response = requests.get(url, timeout=10)
    text = extract_visible_text(response.text)[:6000]
    prompt = f"""
Summarize this website:
- Purpose
- Key Sections
- Offerings
- Target Audience

Content:
\"\"\"{text}\"\"\"
"""
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return r.choices[0].message.content


# ===================== WEBSITE COMPARATOR =====================
def compare_websites(url1, url2, client):
    A = extract_visible_text(requests.get(url1).text)[:5000]
    B = extract_visible_text(requests.get(url2).text)[:5000]
    prompt = f"""
Compare these two websites:
- Purpose
- Audience
- Offerings
- Similarities
- Differences

SITE A:
{A}

SITE B:
{B}
"""
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return r.choices[0].message.content


# ===================== PDF TO TEXT =====================
def pdf_to_text(file):
    pdf = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf.pages:
        extracted = page.extract_text()
        if extracted: text += extracted + "\n"
    return text


# ===================== FILE CONVERTER =====================
def convert_txt_to_docx(text):
    doc = Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

def convert_txt_to_pdf(text):
    buf = io.BytesIO()
    styles = getSampleStyleSheet()
    story = [Paragraph(line, styles['Normal']) for line in text.split("\n")]
    pdf = SimpleDocTemplate(buf)
    pdf.build(story)
    buf.seek(0)
    return buf


# ===================== RESUME ANALYZER =====================
def extract_skills(text):
    skills_db = ["python","java","c","c++","javascript","sql","html","css","machine learning","deep learning","communication","teamwork","ai","ml","docker","react","node","linux","cloud","devops","flask"]
    return [s for s in skills_db if s.lower() in text.lower()]


def analyze_resume(text, client):
    skills = extract_skills(text)
    prompt = f"""
Analyze this resume and return structured sections:

ATS SCORE (0-100)
SKILLS FOUND: {skills}
STRENGTHS:
WEAKNESSES:
SUITABLE ROLES:

Resume Content:
\"\"\"{text}\"\"\"
"""
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"user","content":prompt}]
    )
    return r.choices[0].message.content


# ===================== STREAMLIT APP =====================
st.set_page_config(page_title="Honnagiri Multi Tool", page_icon="🚀", layout="wide")
inject_css()
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "page" not in st.session_state: st.session_state.page="welcome"
if "chat_history" not in st.session_state: st.session_state.chat_history=[]


# ===================== ROUTING =====================

# WELCOME
if st.session_state.page=="welcome":
    st.title("🌌 Welcome to Honnagiri Universe Tools")
    if st.button("🚀 Enter"): st.session_state.page="menu"


# MENU
elif st.session_state.page=="menu":
    st.title("🪐 Choose Your Tool")

    # Row 1
    c1,c2,c3 = st.columns(3)
    with c1:
        st.markdown("<div class='feature-card'>🤖<br>Chatbot</div>", unsafe_allow_html=True)
        if st.button("Chat"): st.session_state.page="chatbot"
    with c2:
        st.markdown("<div class='feature-card'>📝<br>Content Generator</div>", unsafe_allow_html=True)
        if st.button("Content Gen"): st.session_state.page="content"
    with c3:
        st.markdown("<div class='feature-card'>🌍<br>Website Analyzer</div>", unsafe_allow_html=True)
        if st.button("Analyze Site"): st.session_state.page="analyzer"

    # Row 2
    c4,c5,c6 = st.columns(3)
    with c4:
        st.markdown("<div class='feature-card'>🖼<br>Text → Image</div>", unsafe_allow_html=True)
        if st.button("Image Gen"): st.session_state.page="image"
    with c5:
        st.markdown("<div class='feature-card'>📊<br>Website Comparator</div>", unsafe_allow_html=True)
        if st.button("Compare Sites"): st.session_state.page="compare2"
    with c6:
        st.markdown("<div class='feature-card'>📄<br>PDF/Text Summarizer</div>", unsafe_allow_html=True)
        if st.button("Summarize PDF/TXT"): st.session_state.page="pdf_summary"

    # Row 3
    c7,c8 = st.columns(2)
    with c7:
        st.markdown("<div class='feature-card'>🔁<br>File Converter</div>", unsafe_allow_html=True)
        if st.button("Converter"): st.session_state.page="converter"
    with c8:
        st.markdown("<div class='feature-card'>📑<br>Resume Analyzer</div>", unsafe_allow_html=True)
        if st.button("Analyze Resume"): st.session_state.page="resume"

    if st.button("🔙 Exit"): st.session_state.page="welcome"


# CHATBOT
elif st.session_state.page=="chatbot":
    st.title("🤖 Chatbot")
    msg = st.text_input("Your message:")
    if msg:
        st.session_state.chat_history.append({"role":"user","content":msg})
        r = client.chat.completions.create(model="llama-3.3-70b-versatile",messages=st.session_state.chat_history)
        st.session_state.chat_history.append({"role":"assistant","content":r.choices[0].message.content})
    for chat in st.session_state.chat_history:
        st.write(f"**{'You' if chat['role']=='user' else 'Bot'}:** {chat['content']}")
    if st.button("Back"): st.session_state.page="menu"


# CONTENT GENERATOR
elif st.session_state.page=="content":
    st.title("📝 Content Generator")
    topic = st.text_input("Topic:")
    audience = st.text_input("Audience:")
    if st.button("Generate"):
        prompt = f"Write marketing content about '{topic}' for '{audience}'."
        r = client.chat.completions.create(model="llama-3.3-70b-versatile",messages=[{"role":"user","content":prompt}])
        st.write(r.choices[0].message.content)
    if st.button("Back"): st.session_state.page="menu"


# WEBSITE ANALYZER
elif st.session_state.page=="analyzer":
    st.title("🌍 Website Analyzer")
    url = st.text_input("Website URL:")
    if st.button("Analyze"):
        st.write(analyze_website(url, client))
    if st.button("Back"): st.session_state.page="menu"


# TEXT → IMAGE
elif st.session_state.page=="image":
    st.title("🖼 Text → Image Generator")
    prompt = st.text_input("Describe image:")
    if st.button("Generate"):
        formatted = prompt.replace(" ", "+")
        url = f"https://image.pollinations.ai/prompt/{formatted}"
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"})
        if r.status_code==200:
            st.image(r.content)
        else:
            st.error("Failed to generate image")
    if st.button("Back"): st.session_state.page="menu"


# WEBSITE COMPARATOR
elif st.session_state.page=="compare2":
    st.title("📊 Website Comparator")
    u1 = st.text_input("Website 1:")
    u2 = st.text_input("Website 2:")
    if st.button("Compare"):
        st.write(compare_websites(u1, u2, client))
    if st.button("Back"): st.session_state.page="menu"


# PDF/TEXT SUMMARIZER
elif st.session_state.page=="pdf_summary":
    st.title("📄 PDF / Text Summarizer")
    file = st.file_uploader("Upload PDF or TXT:", type=["pdf","txt"])
    text_input = st.text_area("Or paste text:")
    if st.button("Summarize"):
        extracted = ""
        if file:
            ext = file.name.split(".")[-1].lower()
            if ext=="pdf": extracted = pdf_to_text(file)
            elif ext=="txt": extracted = file.read().decode()
        elif text_input.strip():
            extracted = text_input
        if extracted.strip():
            prompt = f"Summarize this:\n{extracted}"
            r = client.chat.completions.create(model="llama-3.3-70b-versatile",messages=[{"role":"user","content":prompt}])
            st.write(r.choices[0].message.content)
        else:
            st.warning("No text found")
    if st.button("Back"): st.session_state.page="menu"


# FILE CONVERTER
elif st.session_state.page=="converter":
    st.title("🔁 Universal File Converter")
    file = st.file_uploader("Upload file:", type=["pdf","docx","txt"])
    output = st.selectbox("Convert to:", ["TXT","PDF","DOCX"])
    if st.button("Convert"):
        if file:
            ext = file.name.split(".")[-1].lower()
            text = pdf_to_text(file) if ext=="pdf" else docx2txt.process(file) if ext=="docx" else file.read().decode()
            if output=="TXT":
                st.download_button("Download TXT", text, file_name=file.name.replace(ext,"txt"))
            elif output=="DOCX":
                st.download_button("Download DOCX", convert_txt_to_docx(text), file_name=file.name.replace(ext,"docx"))
            elif output=="PDF":
                st.download_button("Download PDF", convert_txt_to_pdf(text), file_name=file.name.replace(ext,"pdf"))
        else:
            st.warning("Upload a file first")
    if st.button("Back"): st.session_state.page="menu"


# RESUME ANALYZER
elif st.session_state.page=="resume":
    st.title("📑 Resume Analyzer")
    file = st.file_uploader("Upload Resume (PDF/DOCX):", type=["pdf","docx"])
    if st.button("Analyze Resume"):
        if file:
            ext = file.name.split(".")[-1].lower()
            text = pdf_to_text(file) if ext=="pdf" else docx2txt.process(file)
            result = analyze_resume(text, client)
            st.subheader("📝 Analysis Result")
            st.write(result)
        else:
            st.warning("Upload resume first")
    if st.button("Back"): st.session_state.page="menu"
