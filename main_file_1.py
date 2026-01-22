import streamlit as st
from groq import Groq
import requests
from bs4 import BeautifulSoup
import json
import io
import re

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

import PyPDF2
import docx2txt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

import nltk
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from fuzzywuzzy import fuzz

# ===================== NLP MODELS LOADING =====================
nltk.download('punkt')
nlp = spacy.load("en_core_web_sm")

# ===================== FUTURISTIC UI THEME =====================
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
        body::before {
            content: "";
            position: fixed;
            top:0;left:0;
            width:100%;height:100%;
            background-image: radial-gradient(#ffffff 1px, transparent 1px);
            background-size: 3px 3px;
            opacity:0.15;
            animation: floatStars 200s linear infinite;
            pointer-events:none;
            z-index:-1;
        }
        @keyframes floatStars {
            from {transform: translateY(0px);}
            to {transform: translateY(-2000px);}
        }
        .feature-card {
            backdrop-filter: blur(12px);
            border-radius: 20px;
            padding: 32px;
            text-align: center;
            color: #E6E6FA;
            font-weight: 600;
            font-size: 1.15rem;
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
        .feature-icon {
            font-size: 2.4rem;
            display: block;
            margin-bottom: 10px;
            filter: drop-shadow(0px 0px 6px #fff);
        }
        .chatbot-box { color:#7dd3fc !important; }
        .content-box { color:#a5b4fc !important; }
        .web-box { color:#fcd34d !important; }
        .image-box { color:#bbf7d0 !important; }
        .compare-box { color:#ff9b9b !important; }
        .pdf-box { color:#c5f0ff !important; }
        .convert-box { color:#d1ffc5 !important; }
        .plag-box { color:#ffd1d1 !important; }
        .resume-box { color:#ffe7ab !important; }

        textarea, .stTextInput>div>div>input {
            background:rgba(255,255,255,0.15)!important;
            border-radius:10px!important;
            color:#E6E6FA!important;
            border:1px solid rgba(255,255,255,0.3)!important;
            box-shadow: inset 0 0 12px rgba(0,0,0,0.45);
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
        h1, h2, h3 {
            color: #F3EFFA !important;
            text-shadow:0 0 10px rgba(166,130,255,0.7);
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
        fields='id,name'
    ).execute()
    return file.get('id'), file.get('name')


# ===================== HELPERS =====================
def extract_visible_text(html):
    soup = BeautifulSoup(html,"html.parser")
    for t in soup(["script","style","meta","header","nav","footer","noscript"]):
        t.decompose()
    return " ".join(soup.stripped_strings)


# ===================== TOOL: WEBSITE ANALYZER =====================
def analyze_website(url, client):
    response = requests.get(url, timeout=10)
    text = extract_visible_text(response.text)[:6000]

    prompt = f"""
Analyze this website content and summarize purpose, key sections, offerings, and audience using bullet points.

Content:
\"\"\"{text}\"\"\"
"""
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"user","content":prompt}]
    )
    return r.choices[0].message.content


# ===================== TOOL: WEBSITE COMPARATOR =====================
def compare_websites(url1, url2, client):
    A = extract_visible_text(requests.get(url1).text)[:5000]
    B = extract_visible_text(requests.get(url2).text)[:5000]

    prompt = f"""
Compare these two websites and give:
- Purpose comparison
- Offering comparison
- Audience comparison
- Differences
- Similarities
- Unique traits
- Summary conclusion

=== WEBSITE A ===
{A}

=== WEBSITE B ===
{B}
"""
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"user","content":prompt}]
    )
    return r.choices[0].message.content


# ===================== TOOL: PDF/TEXT SUMMARIZER =====================
def pdf_to_text(file):
    pdf = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf.pages:
        text += page.extract_text() or ""
    return text

def summarize_text(text, client):
    prompt = f"""
Summarize the following content using:

- Key Bullet Points
- 5-10 Line Summary
Text:
\"\"\"{text}\"\"\"
"""
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"user","content":prompt}]
    )
    return r.choices[0].message.content


# ===================== TOOL: FILE FORMAT CONVERTER =====================
def convert_docx_to_text(file):
    return docx2txt.process(file)

def convert_text_to_pdf(text):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 50
    for line in text.split("\n"):
        c.drawString(50, y, line[:120])
        y -= 15
    c.save()
    buffer.seek(0)
    return buffer


# ===================== TOOL: ONLINE PLAGIARISM CHECKER =====================
def online_plagiarism_check(text, serp_key, client):
    queries = nltk.sent_tokenize(text)[:3]  # Limit first 3 sentences for efficiency
    matches = []

    for q in queries:
        params = {
            "engine": "google",
            "q": q,
            "api_key": serp_key
        }
        r = requests.get("https://serpapi.com/search", params=params)
        data = r.json()

        if "organic_results" in data:
            for result in data["organic_results"]:
                snippet = result.get("snippet", "")
                score = fuzz.ratio(q.lower(), snippet.lower())
                if score > 40:
                    matches.append({"query": q, "snippet": snippet, "score": score})

    prompt = f"""
Analyze plagiarism results and produce:
- Estimated plagiarism %
- List of matched sentences
- Unique content
- Final assessment

Text:
{text}

Matches:
{json.dumps(matches, indent=2)}
"""
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"user","content":prompt}]
    )
    return r.choices[0].message.content


# ===================== TOOL: RESUME ANALYZER =====================
def extract_skills(text):
    skills_db = ["Python", "Java", "C", "C++", "JavaScript", "HTML", "CSS", "SQL", "AI", "ML", "Communication", "Teamwork"]
    detected = [s for s in skills_db if s.lower() in text.lower()]
    return detected

def analyze_resume(text, client):
    skills = extract_skills(text)
    prompt = f"""
Evaluate this resume and provide:
- ATS Score (0-100)
- Strengths
- Weaknesses
- Suggested Improvements
- Suitable Job Roles
- Detected Skills: {skills}

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
SERP_KEY = st.secrets["SERPAPI_KEY"]

if "page" not in st.session_state: st.session_state.page="welcome"
if "chat_history" not in st.session_state: st.session_state.chat_history=[]
if "generated_text" not in st.session_state: st.session_state.generated_text=""

# ===================== PAGES =====================
if st.session_state.page=="welcome":
    st.title("🌌 Welcome to Honnagiri Universe Tools")
    if st.button("🚀 Enter"):
        st.session_state.page="menu"


elif st.session_state.page=="menu":
    st.title("🪐 Choose Your Tool")

    # ROW 1
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div class='feature-card chatbot-box'><span class='feature-icon'>🤖</span>Chatbot</div>", unsafe_allow_html=True)
        if st.button("Chat"):
            st.session_state.page="chatbot"

    with c2:
        st.markdown("<div class='feature-card content-box'><span class='feature-icon'>📝</span>Content Generator</div>", unsafe_allow_html=True)
        if st.button("Content Gen"):
            st.session_state.page="content"

    with c3:
        st.markdown("<div class='feature-card web-box'><span class='feature-icon'>🌍</span>Website Analyzer</div>", unsafe_allow_html=True)
        if st.button("Analyze Site"):
            st.session_state.page="analyzer"

    # ROW 2
    c4, c5, c6 = st.columns(3)
    with c4:
        st.markdown("<div class='feature-card image-box'><span class='feature-icon'>🖼</span>Text → Image</div>", unsafe_allow_html=True)
        if st.button("Image Gen"):
            st.session_state.page="image"

    with c5:
        st.markdown("<div class='feature-card compare-box'><span class='feature-icon'>📊</span>Website Comparator</div>", unsafe_allow_html=True)
        if st.button("Compare"):
            st.session_state.page="compare2"

    with c6:
        st.markdown("<div class='feature-card pdf-box'><span class='feature-icon'>📄</span>PDF/Text Summarizer</div>", unsafe_allow_html=True)
        if st.button("Summarizer"):
            st.session_state.page="summarizer"

    # ROW 3
    c7, c8, c9 = st.columns(3)
    with c7:
        st.markdown("<div class='feature-card convert-box'><span class='feature-icon'>🔁</span>File Converter</div>", unsafe_allow_html=True)
        if st.button("Converter"):
            st.session_state.page="converter"

    with c8:
        st.markdown("<div class='feature-card plag-box'><span class='feature-icon'>🕵️</span>Plagiarism Checker</div>", unsafe_allow_html=True)
        if st.button("Plag Check"):
            st.session_state.page="plag"

    with c9:
        st.markdown("<div class='feature-card resume-box'><span class='feature-icon'>📑</span>Resume Analyzer</div>", unsafe_allow_html=True)
        if st.button("Resume"):
            st.session_state.page="resume"

    if st.button("🔙 Exit"):
        st.session_state.page="welcome"


elif st.session_state.page=="chatbot":
    st.title("🤖 Honnagiri Chatbot")
    msg = st.text_input("💬 Say something:")
    if msg:
        st.session_state.chat_history.append({"role":"user","content":msg})
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=st.session_state.chat_history
        )
        st.session_state.chat_history.append({"role":"assistant","content":r.choices[0].message.content})
    for chat in st.session_state.chat_history:
        st.write(f"**{'🧑' if chat['role']=='user' else '🤖'}:** {chat['content']}")
    if st.button("🔙 Back"):
        st.session_state.page="menu"


elif st.session_state.page=="content":
    st.title("📝 Content Generator")
    topic = st.text_input("🧾 Topic?")
    audience = st.text_input("🎯 Audience?")
    if st.button("Generate"):
        prompt = f"Write marketing content about '{topic}' for '{audience}'."
        r = client.chat.completions.create(model="llama-3.3-70b-versatile",messages=[{"role":"user","content":prompt}])
        st.write(r.choices[0].message.content)
    if st.button("🔙 Back"):
        st.session_state.page="menu"


elif st.session_state.page=="analyzer":
    st.title("🌍 Website Analyzer")
    url = st.text_input("URL:")
    if st.button("Analyze"):
        st.write(analyze_website(url, client))
    if st.button("🔙 Back"):
        st.session_state.page="menu"


elif st.session_state.page=="image":
    st.title("🖼 Text → Image Generator")
    prompt = st.text_input("Describe the image:")
    if st.button("Generate"):
        formatted = prompt.replace(" ", "+")
        url = f"https://image.pollinations.ai/prompt/{formatted}"
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"})
        if r.status_code==200:
            st.image(r.content)
        else:
            st.error("Failed to generate image")
    if st.button("🔙 Back"):
        st.session_state.page="menu"


elif st.session_state.page=="compare2":
    st.title("📊 Website Comparator")
    u1 = st.text_input("Website 1 URL:")
    u2 = st.text_input("Website 2 URL:")
    if st.button("Compare Now"):
        st.write(compare_websites(u1, u2, client))
    if st.button("🔙 Back"):
        st.session_state.page="menu"


elif st.session_state.page=="summarizer":
    st.title("📄 PDF/Text Summarizer")
    uploaded = st.file_uploader("Upload PDF or DOCX or TXT", type=["pdf","docx","txt"])
    txt = st.text_area("Or paste text here:")
    if st.button("Summarize"):
        if uploaded:
            ext = uploaded.name.split(".")[-1]
            if ext=="pdf":
                txt = pdf_to_text(uploaded)
            elif ext=="docx":
                txt = docx2txt.process(uploaded)
            elif ext=="txt":
                txt = uploaded.read().decode()
        if txt.strip():
            st.write(summarize_text(txt, client))
        else:
            st.warning("No content found")
    if st.button("🔙 Back"):
        st.session_state.page="menu"


elif st.session_state.page=="converter":
    st.title("🔁 File Format Converter")
    file = st.file_uploader("Upload File", type=["pdf","docx","txt"])
    mode = st.selectbox("Convert to:", ["TXT","PDF","DOCX"])
    if st.button("Convert"):
        if not file:
            st.warning("Upload a file first")
        else:
            ext = file.name.split(".")[-1]
            text=""
            if ext=="pdf":
                text = pdf_to_text(file)
            elif ext=="docx":
                text = docx2txt.process(file)
            else:
                text = file.read().decode()

            if mode=="TXT":
                st.download_button("Download TXT", text, file_name="output.txt")
            elif mode=="PDF":
                pdf = convert_text_to_pdf(text)
                st.download_button("Download PDF", pdf, file_name="output.pdf")
            elif mode=="DOCX":
                from docx import Document
                doc = Document()
                doc.add_paragraph(text)
                buffer = io.BytesIO()
                doc.save(buffer)
                st.download_button("Download DOCX", buffer.getvalue(), file_name="output.docx")
    if st.button("🔙 Back"):
        st.session_state.page="menu"


elif st.session_state.page=="plag":
    st.title("🕵️ Online Plagiarism Checker")
    content = st.text_area("Paste your text:")
    if st.button("Check Plagiarism"):
        if content.strip():
            st.write(online_plagiarism_check(content, SERP_KEY, client))
        else:
            st.warning("Enter content first")
    if st.button("🔙 Back"):
        st.session_state.page="menu"


elif st.session_state.page=="resume":
    st.title("📑 Resume Analyzer")
    uploaded = st.file_uploader("Upload Resume (PDF/DOCX)", type=["pdf","docx"])
    if st.button("Analyze Resume"):
        if uploaded:
            ext = uploaded.name.split(".")[-1]
            if ext=="pdf":
                text = pdf_to_text(uploaded)
            else:
                text = docx2txt.process(uploaded)
            st.write(analyze_resume(text, client))
        else:
            st.warning("Upload resume first")
    if st.button("🔙 Back"):
        st.session_state.page="menu"
