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


# ===================== THEME CSS =====================
def inject_css():
    st.markdown("""
    <style>

    /* ================================================================== */
    /*                           GLOBAL BACKGROUND                        */
    /* ================================================================== */
    body {
        background: radial-gradient(circle at top, #1a074b, #080315 70%);
        color: #E4E4F1 !important;
        font-family: 'Poppins', sans-serif;
        overflow-x: hidden;
    }

    /* Floating particles */
    body::before {
        content: "";
        position: fixed;
        top:0; left:0;
        width:100%; height:100%;
        background-image:
            radial-gradient(2px 2px at 20% 30%, #ffffff55, transparent),
            radial-gradient(1px 1px at 60% 70%, #ffffff33, transparent),
            radial-gradient(2px 2px at 80% 20%, #ffffff44, transparent);
        background-repeat: no-repeat;
        animation: particleMove 18s infinite linear;
        pointer-events:none;
        z-index:-1;
    }
    @keyframes particleMove {
        0% { transform: translateY(0px); }
        100% { transform: translateY(-1500px); }
    }

    /* ================================================================== */
    /*                             LOGO (HG)                              */
    /* ================================================================== */
    .logo-container {
        width: 260px;
        height: 260px;
        margin: auto;
        position: relative;
        display:flex;
        align-items:center;
        justify-content:center;
        animation: floatLogo 4s ease-in-out infinite alternate;
    }

    /* Floating animation */
    @keyframes floatLogo {
        0%   { transform: translateY(0px) rotate(0deg); }
        100% { transform: translateY(-16px) rotate(3deg); }
    }

    .logo {
        width: 100%;
        height: 100%;
        border-radius: 30px;
        display:flex;
        align-items:center;
        justify-content:center;
        font-family: 'Montserrat', monospace;
        font-weight: bold;
        font-size: 85px;
        letter-spacing: 10px;
        color: #ffffff;
        text-shadow:0 0 18px #b087ff;
        background: rgba(255,255,255,0.07);
        border: 2px solid rgba(255,255,255,0.25);
        box-shadow: 0 0 40px rgba(131, 70, 255, 0.7);
        backdrop-filter: blur(14px);
        animation: logoGlowPulse 3s infinite alternate;
    }

    @keyframes logoGlowPulse {
        0%   { box-shadow: 0 0 22px #764bff; }
        100% { box-shadow: 0 0 48px #9e71ff; }
    }

    .welcome-title {
        text-align:center;
        margin-top: 18px;
        font-size: 28px;
        color:#d0c8ff;
        text-shadow:0 0 9px #9f6bff;
        animation: fadeInUp 1.2s ease;
    }

    .welcome-tagline {
        text-align:center;
        margin-top: 6px;
        color:#a789ff;
        font-size:17px;
        opacity:0.85;
        animation: fadeInUp 1.8s ease;
    }

    @keyframes fadeInUp {
        from {opacity:0; transform:translateY(20px);}
        to   {opacity:1; transform:translateY(0);}
    }

    /* ================================================================== */
    /*                              CARDS                                 */
    /* ================================================================== */
    .feature-card {
        backdrop-filter: blur(12px);
        border-radius: 20px;
        padding: 28px;
        text-align: center;
        color: #E6E6FA;
        font-weight: 600;
        font-size: 1.1rem;
        border: 2px solid rgba(255,255,255,0.18);
        background: rgba(255,255,255,0.08);
        box-shadow: 0 0 25px rgba(111, 70, 255, 0.4);
        transition: 0.4s;
        cursor: pointer;
    }
    .feature-card:hover {
        transform: scale(1.06) translateY(-6px);
        box-shadow: 0 0 35px rgba(157, 98, 255, 0.8);
    }

    /* ================================================================== */
    /*                             BUTTONS                                */
    /* ================================================================== */
    .stButton>button {
        background: linear-gradient(135deg,#6D28D9,#4C1D95);
        color:white;
        padding:12px 26px;
        border-radius:12px;
        border:none;
        font-size:16px;
        font-weight:600;
        box-shadow:0 0 15px rgba(139,92,246,0.8);
        transition:0.3s;
    }
    .stButton>button:hover {
        transform:translateY(-3px) scale(1.03);
        box-shadow:0 0 22px rgba(167,139,250,1);
    }

    /* ================================================================== */
    /*                            INPUT FIELDS                            */
    /* ================================================================== */
    textarea, .stTextInput>div>div>input {
        background:rgba(255,255,255,0.12)!important;
        border-radius:10px!important;
        color:#E6E6FA!important;
        border:1px solid rgba(255,255,255,0.3)!important;
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
    skills_db = ["python","java","c","c++","javascript","sql","html","css",
                 "machine learning","deep learning","communication","teamwork",
                 "ai","ml","docker","react","node","linux","cloud","devops","flask"]
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


# ===================== APP START =====================
st.set_page_config(page_title="Honnagiri Multi Tool", page_icon="🚀", layout="wide")
inject_css()
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "page" not in st.session_state:
    st.session_state.page="welcome"
if "chat_history" not in st.session_state:
    st.session_state.chat_history=[]


# ===================== WELCOME PAGE =====================
if st.session_state.page=="welcome":
    st.markdown("<div class='logo-container'><div class='logo'>HG</div></div>", unsafe_allow_html=True)
    st.markdown("<div class='welcome-title'>Honnagiri Galaxy Tools</div>", unsafe_allow_html=True)
    st.markdown("<div class='welcome-tagline'>Explore. Create. Analyze. Convert — all in one universe.</div>", unsafe_allow_html=True)

    st.write("")
    if st.button("🚀 Enter the Galaxy"):
        st.session_state.page="menu"


# ===================== MENU =====================
elif st.session_state.page=="menu":
    st.title("🪐 Choose Your Tool")

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

    c7,c8 = st.columns(2)
    with c7:
        st.markdown("<div class='feature-card'>🔁<br>File Converter</div>", unsafe_allow_html=True)
        if st.button("Converter"): st.session_state.page="converter"
    with c8:
        st.markdown("<div class='feature-card'>📑<br>Resume Analyzer</div>", unsafe_allow_html=True)
        if st.button("Analyze Resume"): st.session_state.page="resume"

    if st.button("🔙 Exit"): st.session_state.page="welcome"


# ===================== CHATBOT =====================
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


# ===================== CONTENT GENERATOR =====================
elif st.session_state.page=="content":
    st.title("📝 Content Generator")
    topic = st.text_input("Topic:")
    audience = st.text_input("Audience:")
    if st.button("Generate"):
        prompt = f"Write marketing content about '{topic}' for '{audience}'."
        r = client.chat.completions.create(model="llama-3.3-70b-versatile",messages=[{"role":"user","content":prompt}])
        st.write(r.choices[0].message.content)
    if st.button("Back"): st.session_state.page="menu"


# ===================== WEBSITE ANALYZER =====================
elif st.session_state.page=="analyzer":
    st.title("🌍 Website Analyzer")
    url = st.text_input("Website URL:")
    if st.button("Analyze"):
        st.write(analyze_website(url, client))
    if st.button("Back"): st.session_state.page="menu"


# ===================== TEXT → IMAGE =====================
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


# ===================== WEBSITE COMPARATOR =====================
elif st.session_state.page=="compare2":
    st.title("📊 Website Comparator")
    u1 = st.text_input("Website 1:")
    u2 = st.text_input("Website 2:")
    if st.button("Compare"):
        st.write(compare_websites(u1, u2, client))
    if st.button("Back"): st.session_state.page="menu"


# ===================== PDF/TEXT SUMMARIZER =====================
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
            r = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role":"user","content":prompt}]
            )
            st.write(r.choices[0].message.content)
        else:
            st.warning("No text found")
    if st.button("Back"): st.session_state.page="menu"


# ===================== FILE CONVERTER =====================
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


# ===================== RESUME ANALYZER =====================
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
