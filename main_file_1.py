import streamlit as st
from groq import Groq
import requests
from bs4 import BeautifulSoup
import json
import io

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

import PyPDF2
import docx2txt
from docx import Document
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from fuzzywuzzy import fuzz


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
Summarize this website with:
- Purpose
- Key Sections
- Main Offerings
- Target Audience

Content:
\"\"\"{text}\"\"\"
"""
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"user","content":prompt}]
    )
    return r.choices[0].message.content



# ===================== WEBSITE COMPARATOR =====================
def compare_websites(url1, url2, client):
    A = extract_visible_text(requests.get(url1).text)[:5000]
    B = extract_visible_text(requests.get(url2).text)[:5000]

    prompt = f"""
Compare these two websites:
Criteria:
- Purpose
- Audience
- Offerings
- Similarities
- Differences
- Summary

SITE A:
{A}

SITE B:
{B}
"""
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"user","content":prompt}]
    )
    return r.choices[0].message.content



# ===================== PDF/TEXT SUMMARIZER =====================
def pdf_to_text(file):
    pdf = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text



# ===================== FILE CONVERTER =====================
def read_pdf(file):
    pdf = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text

def read_docx(file):
    return docx2txt.process(file)

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
    story = []
    for line in text.split("\n"):
        story.append(Paragraph(line, styles['Normal']))
        story.append(Spacer(1, 4))
    pdf = SimpleDocTemplate(buf)
    pdf.build(story)
    buf.seek(0)
    return buf



# ===================== CUSTOM SENTENCE SPLITTER =====================
import re
def simple_sentence_split(text):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 0]



# ===================== IMPROVED PLAGIARISM CHECKER =====================
def free_web_plagiarism_check(text):
    sentences = simple_sentence_split(text)
    queries = sentences[:5]  # take first 5 sentences max

    results = []
    total = len(queries)
    copied = 0

    for q in queries:
        url = f"https://duckduckgo.com/html/?q={requests.utils.quote(q)}"
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")

        snippets = soup.select(".result__snippet")
        best_score = 0
        best_snippet = ""

        for s in snippets[:3]:
            snippet = s.get_text()
            score = fuzz.ratio(q.lower(), snippet.lower())
            if score > best_score:
                best_score = score
                best_snippet = snippet

        results.append({
            "sentence": q,
            "best_match": best_snippet,
            "score": best_score
        })

        if best_score > 50:
            copied += 1

    plagiarism_percentage = round((copied / total) * 100, 2) if total > 0 else 0

    return {
        "percent": plagiarism_percentage,
        "copied": copied,
        "total": total,
        "details": results
    }



# ===================== RESUME ANALYZER =====================
def extract_skills(text):
    skills_db = [
        "python","java","c","c++","javascript","sql","html","css",
        "machine learning","deep learning","communication","teamwork",
        "ai","ml","docker","react","node","linux","cloud","devops","flask"
    ]
    return [s for s in skills_db if s.lower() in text.lower()]

def analyze_resume(text, client):
    skills = extract_skills(text)
    prompt = f"""
Analyze this resume. Provide:
- ATS Score (0-100)
- Strengths
- Weaknesses
- Improvements
- Suitable job roles
- Detected Skills: {skills}

Resume:
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


# ===================== PAGE ROUTER =====================
if st.session_state.page=="welcome":
    st.title("🌌 Welcome to Honnagiri Universe Tools")
    if st.button("🚀 Enter"):
        st.session_state.page="menu"


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
        if st.button("Summarizer"): st.session_state.page="summarizer"

    c7,c8,c9 = st.columns(3)
    with c7:
        st.markdown("<div class='feature-card'>🔁<br>File Converter</div>", unsafe_allow_html=True)
        if st.button("Converter"): st.session_state.page="converter"

    with c8:
        st.markdown("<div class='feature-card'>🕵️<br>Plagiarism Checker</div>", unsafe_allow_html=True)
        if st.button("Check Plagiarism"): st.session_state.page="plag"

    with c9:
        st.markdown("<div class='feature-card'>📑<br>Resume Analyzer</div>", unsafe_allow_html=True)
        if st.button("Analyze Resume"): st.session_state.page="resume"

    if st.button("🔙 Exit"): st.session_state.page="welcome"



elif st.session_state.page=="chatbot":
    st.title("🤖 Chatbot")
    msg = st.text_input("Your message:")
    if msg:
        st.session_state.chat_history.append({"role":"user","content":msg})
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=st.session_state.chat_history
        )
        st.session_state.chat_history.append({"role":"assistant","content":r.choices[0].message.content})
    for chat in st.session_state.chat_history:
        st.write(f"**{'You' if chat['role']=='user' else 'Bot'}:** {chat['content']}")
    if st.button("Back"): st.session_state.page="menu"



elif st.session_state.page=="content":
    st.title("📝 Content Generator")
    topic = st.text_input("Topic:")
    audience = st.text_input("Audience:")
    if st.button("Generate"):
        prompt = f"Write marketing content about '{topic}' for '{audience}'."
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":prompt}]
        )
        st.write(r.choices[0].message.content)
    if st.button("Back"): st.session_state.page="menu"



elif st.session_state.page=="analyzer":
    st.title("🌍 Website Analyzer")
    url = st.text_input("Website URL:")
    if st.button("Analyze"):
        st.write(analyze_website(url, client))
    if st.button("Back"): st.session_state.page="menu"



elif st.session_state.page=="image":
    st.title("🖼 Text → Image Generator")
    prompt = st.text_input("Describe image:")
    if st.button("Generate"):
        formatted = prompt.replace(" ", "+")
        img_url = f"https://image.pollinations.ai/prompt/{formatted}"
        r = requests.get(img_url, headers={"User-Agent":"Mozilla/5.0"})
        if r.status_code==200:
            st.image(r.content)
        else:
            st.error("Failed to generate image")
    if st.button("Back"): st.session_state.page="menu"



elif st.session_state.page=="compare2":
    st.title("📊 Website Comparator")
    u1 = st.text_input("Website 1 URL:")
    u2 = st.text_input("Website 2 URL:")
    if st.button("Compare Now"):
        st.write(compare_websites(u1, u2, client))
    if st.button("Back"): st.session_state.page="menu"



elif st.session_state.page=="summarizer":
    st.title("📄 PDF/Text Summarizer")
    file = st.file_uploader("Upload PDF/DOCX/TXT:", type=["pdf","docx","txt"])
    txt = st.text_area("Or paste text:")
    if st.button("Summarize"):
        if file:
            ext = file.name.split(".")[-1].lower()
            if ext=="pdf": txt = pdf_to_text(file)
            elif ext=="docx": txt = docx2txt.process(file)
            elif ext=="txt": txt = file.read().decode()
        if txt.strip():
            prompt = f"Summarize this:\n{txt}"
            r = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role":"user","content":prompt}]
            )
            st.write(r.choices[0].message.content)
        else:
            st.warning("No content found")
    if st.button("Back"): st.session_state.page="menu"



elif st.session_state.page=="converter":
    st.title("🔁 Universal File Converter")
    file = st.file_uploader("Upload file:", type=["pdf","docx","txt"])
    output = st.selectbox("Convert to:", ["TXT","PDF","DOCX"])
    if st.button("Convert"):
        if file:
            ext = file.name.split(".")[-1].lower()

            if ext=="pdf": text = read_pdf(file)
            elif ext=="docx": text = read_docx(file)
            else: text = file.read().decode()

            if output=="TXT":
                st.download_button("Download TXT", text, file_name=file.name.replace(ext,"txt"))
            elif output=="DOCX":
                buf = convert_txt_to_docx(text)
                st.download_button("Download DOCX", buf, file_name=file.name.replace(ext,"docx"))
            elif output=="PDF":
                buf = convert_txt_to_pdf(text)
                st.download_button("Download PDF", buf, file_name=file.name.replace(ext,"pdf"))
        else:
            st.warning("Upload a file first")
    if st.button("Back"): st.session_state.page="menu"



elif st.session_state.page=="plag":
    st.title("🕵️ Improved Plagiarism Checker")
    content = st.text_area("Paste text:")
    if st.button("Scan Now"):
        if content.strip():
            with st.spinner("Scanning the web..."):
                result = free_web_plagiarism_check(content)
                st.subheader(f"Plagiarism Score: {result['percent']}%")
                st.write(f"Matched Sentences: {result['copied']} / {result['total']}")
                st.write("---")
                st.subheader("Detailed Comparison:")
                for row in result["details"]:
                    st.write(f"📌 Sentence: **{row['sentence']}**")
                    st.write(f"🔍 Match Score: **{row['score']}**")
                    st.write(f"📝 Match Found: {row['best_match']}")
                    st.write("---")
        else:
            st.warning("Enter text first")
    if st.button("Back"): st.session_state.page="menu"



elif st.session_state.page=="resume":
    st.title("📑 Resume Analyzer")
    file = st.file_uploader("Upload Resume (PDF/DOCX):", type=["pdf","docx"])
    if st.button("Analyze Resume"):
        if file:
            ext = file.name.split(".")[-1].lower()
            if ext=="pdf":
                txt = pdf_to_text(file)
            else:
                txt = docx2txt.process(file)
            st.write(analyze_resume(txt, client))
        else:
            st.warning("Upload resume first")
    if st.button("Back"): st.session_state.page="menu"
