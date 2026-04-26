import streamlit as st
import pandas as pd
import re
import json
import time
from io import BytesIO
from pathlib import Path
from docx import Document
import pdfplumber

# Existing backend imports
try:
    from backend import (
        compute_match_score,
        extract_resume_data_from_text,
        parse_jd,
    )
except ImportError:
    st.warning("Backend module not found. Using the new built-in AI Talent Scouting Engine instead.")

# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="AI Talent Scout Pro",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded", 
)

# ==========================================
# ===== SECURE API UI ADDED =====
# ==========================================
with st.sidebar:
    st.markdown("### 🔐 LLM Configuration")
    st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 10px 0;'>", unsafe_allow_html=True)
    
    enable_ai = st.checkbox("Enable AI (LLM Processing)", value=False)
    provider = st.selectbox("Select Provider", ["gemini", "openai"])
    
    # Fallback support
    fallback_key = ""
    try:
        if provider == "gemini":
            fallback_key = st.secrets.get("GEMINI_API_KEY", "")
        elif provider == "openai":
            fallback_key = st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        pass # Secrets file might not exist

    api_key = st.text_input("Enter API Key", type="password", value=fallback_key)

    if enable_ai and api_key:
        st.session_state["api_key"] = api_key
        st.session_state["llm_provider"] = provider
        st.session_state["enable_ai"] = True
        
        try:
            if provider == "gemini":
                import google.generativeai as genai
                genai.configure(api_key=api_key)
            elif provider == "openai":
                import openai
                openai.api_key = api_key
            st.success(f"{provider.capitalize()} API Key configured securely!")
        except ImportError:
            st.warning(f"Library for {provider} not installed. Install to use live LLM.")
    else:
        st.session_state["enable_ai"] = False
        st.info("Enable AI and provide API key to unlock full LLM features.")
# ==========================================

# ==========================================
# ===== 3D UI ENHANCEMENT & VISIBILITY FIXES =====
# ==========================================
css_code = """
<style>
    /* GLOBAL THEME & NEON 3D BACKGROUND */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;800&display=swap');
    
    .stApp {
        background: radial-gradient(circle at 50% 50%, rgba(59, 130, 246, 0.15) 0%, transparent 50%),
                    linear-gradient(135deg, #0f172a, #1e3a8a, #4c1d95) !important;
        background-attachment: fixed;
        color: #ffffff !important;
        font-family: 'Inter', sans-serif;
    }

    /* SIDEBAR BACKGROUND */
    [data-testid="stSidebar"] {
        background: linear-gradient(135deg, #0f172a, #1e293b) !important;
        border-right: 1px solid rgba(59, 130, 246, 0.3) !important;
    }
    
    /* FIX TEXT */
    label, .stTextInput label, .stSelectbox label, .stCheckbox label {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    /* SIDEBAR HEADINGS */
    [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
        text-shadow: 0 0 10px rgba(59, 130, 246, 0.8) !important;
    }

    /* INPUT BOX */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #0f172a !important;
        color: #ffffff !important;
        border: 1px solid #3b82f6 !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }
    
    /* DROPDOWN SELECTED TEXT */
    .stSelectbox div[data-baseweb="select"] span {
        color: #ffffff !important;
        font-weight: 600 !important;
    }

    /* PLACEHOLDER */
    input::placeholder, textarea::placeholder {
        color: #94a3b8 !important;
        opacity: 1 !important;
    }
    
    /* FOCUS EFFECT */
    input:focus, .stTextInput input:focus, .stSelectbox div[data-baseweb="select"] > div:focus-within {
        box-shadow: 0 0 10px #3b82f6 !important;
        border-color: #60a5fa !important;
        outline: none !important;
    }
    
    /* DROPDOWN POPUP MENU */
    div[role="listbox"] {
        background-color: #0f172a !important;
        border: 1px solid #3b82f6 !important;
    }
    div[role="option"] {
        color: #ffffff !important;
    }
    div[role="option"]:hover, div[aria-selected="true"] {
        background-color: rgba(59, 130, 246, 0.3) !important;
    }
    
    /* EXPANDER UI VISIBILITY FIX */
    div[data-testid="stExpander"] details summary {
        background-color: #0f172a !important;
        color: #ffffff !important;
        border: 1px solid #3b82f6 !important;
        border-radius: 12px !important;
        padding: 10px 15px !important;
        transition: all 0.3s ease !important;
    }
    div[data-testid="stExpander"] details summary:hover {
        background-color: #1e293b !important;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.5) !important;
    }
    div[data-testid="stExpander"] details summary p {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    div[data-testid="stExpander"] {
        border: none !important;
        background: transparent !important;
        margin-bottom: 15px !important;
    }

    /* FADE-IN ANIMATION */
    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .block-container {
        animation: fadeUp 0.8s ease-out;
    }

    /* TEXT VISIBILITY, HIERARCHY & NEON GLOW */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 800 !important;
        opacity: 1 !important;
        letter-spacing: 0.5px;
        text-shadow: 0 0 10px rgba(59,130,246,0.6), 0 0 20px rgba(59,130,246,0.4) !important;
    }
    
    p, span, .stMarkdown {
        color: #ffffff !important;
        font-weight: 600 !important;
    }

    /* HEADER GLOW */
    .header-text {
        text-align: center;
        color: #ffffff !important;
        text-shadow: 0 0 15px #3b82f6, 0 0 30px #3b82f6 !important;
        font-size: 3.5rem !important;
        margin-bottom: 0.5rem !important;
    }

    /* REMOVED EMPTY TOP BOXES & APPLIED CSS TO STREAMLIT COLUMNS VIA HOOK */
    div[data-testid="column"]:has(.glass-card-hook) {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(15px) !important;
        -webkit-backdrop-filter: blur(15px) !important;
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        padding: 30px !important;
        box-shadow: 0 10px 40px rgba(0,0,0,0.6) !important;
        transition: all 0.4s ease-in-out !important;
    }
    
    .glass-card-hook {
        display: none !important;
    }

    /* UPLOAD BOX DESIGN WITH GLOW */
    section[data-testid="stFileUploader"] {
        border: 2px dashed #3b82f6 !important;
        border-radius: 20px !important;
        background-color: rgba(255,255,255,0.03) !important;
        padding: 20px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.2) !important;
    }
    
    section[data-testid="stFileUploader"]:hover {
        border-color: #60a5fa !important;
        box-shadow: 0 0 25px rgba(59, 130, 246, 0.6) !important;
        background-color: rgba(255,255,255,0.06) !important;
    }
    
    section[data-testid="stFileUploader"] > div {
        background: transparent !important;
    }

    section[data-testid="stFileUploader"] div, 
    section[data-testid="stFileUploader"] span, 
    section[data-testid="stFileUploader"] label {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    section[data-testid="stFileUploader"] small {
        color: #ffffff !important;
        font-weight: 600 !important;
        opacity: 1 !important;
        margin-left: 15px !important;
        font-size: 0.95rem !important;
    }

    /* WHITE INPUT UI FIX APPLIED (Textareas) */
    textarea {
        background-color: #ffffff !important;
        color: #000000 !important;
        font-weight: 500 !important;
        border: 2px solid #3b82f6 !important;
        border-radius: 12px !important;
        padding: 10px !important;
        transition: all 0.3s ease !important;
    }
    
    textarea:focus {
        outline: none !important;
        border-color: #2563eb !important;
        box-shadow: 0 0 10px rgba(37, 99, 235, 0.5) !important;
    }

    /* BUTTON STYLING (NEON GLOW) */
    button[kind="primary"], button[kind="secondary"] {
        background: linear-gradient(90deg, #3b82f6, #2563eb) !important;
        color: #ffffff !important;
        border-radius: 50px !important;
        border: none !important;
        font-weight: 800 !important;
        font-size: 1.2rem !important;
        padding: 1rem 2rem !important;
        box-shadow: 0 0 15px rgba(59,130,246,0.8) !important;
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    }
    
    button[kind="primary"]:hover, button[kind="secondary"]:hover {
        transform: scale(1.05) !important;
        box-shadow: 0 0 25px rgba(59,130,246,1) !important;
    }

    /* 3D RESULT CARDS */
    .result-card, .glass-skill-card {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(15px) !important;
        -webkit-backdrop-filter: blur(15px) !important;
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        padding: 25px !important;
        box-shadow: 0 10px 40px rgba(0,0,0,0.6) !important;
        transform-style: preserve-3d;
        transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 0.4s ease !important;
        margin-bottom: 20px;
        height: 100%;
    }

    .result-card:hover, .glass-skill-card:hover {
        transform: perspective(1000px) rotateX(5deg) rotateY(-5deg) scale(1.03) !important;
        box-shadow: 0 20px 60px rgba(0,0,0,0.8), 0 0 20px rgba(59,130,246,0.3) !important;
        border-color: rgba(59, 130, 246, 0.5) !important;
    }

    /* 3D SKILL TAGS (PILLS) */
    .skill-pill {
        padding: 8px 14px;
        border-radius: 999px;
        font-size: 14px;
        margin: 5px;
        display: inline-block;
        font-weight: 700;
        color: #ffffff;
    }
    .pill-matched {
        background: rgba(34,197,94,0.2);
        border: 1px solid #22c55e;
        box-shadow: 0 0 12px #22c55e;
        text-shadow: 0 0 5px #22c55e;
    }
    .pill-partial {
        background: rgba(245,158,11,0.2);
        border: 1px solid #f59e0b;
        box-shadow: 0 0 12px #f59e0b;
        text-shadow: 0 0 5px #f59e0b;
    }
    .pill-missing {
        background: rgba(239,68,68,0.2);
        border: 1px solid #ef4444;
        box-shadow: 0 0 12px #ef4444;
        text-shadow: 0 0 5px #ef4444;
    }
    .pill-additional {
        background: rgba(147,51,234,0.2);
        border: 1px solid #9333ea;
        box-shadow: 0 0 12px #9333ea;
        text-shadow: 0 0 5px #9333ea;
    }
</style>
"""
# Apply regex to crush all whitespace/newlines, ensuring Streamlit parses it safely
st.markdown(re.sub(r'\s+', ' ', css_code), unsafe_allow_html=True)


# ==========================================
# ===== AI TALENT SCOUTING AGENT CORE =====
# ==========================================

TECH_SKILLS_DB = [
    "python", "java", "c++", "javascript", "react", "node.js", "aws", "azure", "gcp",
    "machine learning", "ml", "nlp", "deep learning", "sql", "nosql", "docker", "kubernetes",
    "fastapi", "django", "flask", "pandas", "numpy", "scikit-learn", "html", "css", "git",
    "linux", "agile", "scrum", "ci/cd", "devops", "terraform", "pytorch", "tensorflow", "golang"
]

def parse_jd_agent(jd_text):
    jd_lower = jd_text.lower()
    extracted_skills = [skill for skill in TECH_SKILLS_DB if skill in jd_lower]
    exp_matches = re.findall(r'(\d+)\+?\s*years?', jd_lower)
    exp_years = max([int(e) for e in exp_matches]) if exp_matches else 0
    return {
        "skills": extracted_skills,
        "experience_required": exp_years
    }

def parse_resume_agent(resume_text):
    resume_lower = resume_text.lower()
    extracted_skills = [skill for skill in TECH_SKILLS_DB if skill in resume_lower]
    return {"skills": extracted_skills}

# =========================================================================
# ===== HEURISTIC SCORING FALLBACK (USED BEFORE CHAT BEGINS) =====
# =========================================================================
def compute_match_score_agent(jd_data, resume_data):
    req_skills = set(jd_data.get("skills", []))
    res_skills = set(resume_data.get("skills", []))
    additional_skills = list(res_skills.difference(req_skills))

    if not req_skills:
        return 0.0, [], [], additional_skills

    matched_skills = list(req_skills.intersection(res_skills))
    missing_skills = list(req_skills.difference(res_skills))

    total_required_skills = len(req_skills)
    score = (len(matched_skills) / total_required_skills) * 100
    
    return round(score, 2), matched_skills, missing_skills, additional_skills

def calculate_dynamic_interest(chat_history):
    if not chat_history: return 0
    ans_text = " ".join([m["text"] for m in chat_history if m["sender"] == "Candidate"]).lower()
    if not ans_text.strip(): return 0
        
    jd_skills = st.session_state.get("jd_data", {}).get("skills", [])
    relevance = 0
    if jd_skills:
        matched_jd = sum(1 for skill in jd_skills if skill.lower() in ans_text)
        relevance = min(100, (matched_jd / max(1, len(jd_skills))) * 100 * 1.5) 
    else:
        relevance = 50 

    advanced_keywords = ['accuracy', 'metrics', 'deployment', 'architecture', 'pipeline', 'infrastructure', 'ci/cd', 'docker', 'kubernetes', 'aws', 'gcp', 'azure', 'transformer', 'production', 'scalable']
    mid_keywords = ['api', 'database', 'frontend', 'backend', 'server', 'framework', 'library', 'regression', 'classification', 'sklearn', 'tensorflow', 'pytorch', 'fastapi', 'flask', 'django', 'model']
    
    adv_matches = sum(1 for word in advanced_keywords if word in ans_text)
    mid_matches = sum(1 for word in mid_keywords if word in ans_text)
    technical_depth = min(100, (mid_matches * 15) + (adv_matches * 30))

    specificity_keywords = ['built', 'developed', 'project', 'implemented', 'designed', 'created', 'led', 'managed', 'deployed', 'optimized', 'achieved', 'integrated', 'example']
    matched_spec = sum(1 for word in specificity_keywords if word in ans_text)
    specificity = min(100, matched_spec * 20) 

    clarity = 70 
    if any(w in ans_text for w in ["maybe", "i guess", "not sure", "don't know", "probably", "i think"]):
        clarity -= 30
    if "." in ans_text or "," in ans_text:
        clarity += 15 
        
    structure_markers = ["first", "second", "however", "therefore", "for example", "specifically", "because", "additionally", "moreover", "\n"]
    if any(marker in ans_text for marker in structure_markers):
        clarity += 10
        
    clarity = min(100, max(0, clarity))

    generic_phrases = ["i explored", "i am interested", "i have basic knowledge", "i am learning", "i have heard of", "basic idea"]
    generic_penalty = sum(10 for phrase in generic_phrases if phrase in ans_text)

    interest_score = (0.45 * relevance) + (0.25 * technical_depth) + (0.15 * specificity) + (0.15 * clarity)
    interest_score = max(0, interest_score - generic_penalty)
    
    has_real_project = any(w in ans_text for w in ['project', 'built', 'implemented', 'deployed', 'developed', 'example'])
    if has_real_project and clarity >= 85:
        interest_score += 5
    
    if technical_depth < 70:
        interest_score = min(interest_score, 80)
        
    if adv_matches == 0 and mid_matches == 0:
        interest_score = min(interest_score, 60)
    elif adv_matches == 0 and mid_matches <= 2:
        interest_score = min(interest_score, 75)
    elif adv_matches == 0 and mid_matches > 2:
        interest_score = min(interest_score, 90)

    return int(interest_score)

def simulate_conversation_agent(resume_data):
    skills = resume_data.get("skills", [])
    
    if len(skills) >= 5:
        r1 = "Yes, I am highly interested and actively looking for this kind of role! I have been following the company's recent projects and feel my background aligns perfectly."
        r2 = f"Absolutely, my core expertise lies heavily in {', '.join(skills[:3])} and related technologies. I have built several production-level applications using these."
    elif len(skills) >= 2:
        r1 = "I am very interested in learning more about the opportunity and the team."
        r2 = f"I have strong foundational experience with {', '.join(skills[:2])} and I am eager to apply it here in a real-world setting."
    else:
        r1 = "I might be interested depending on the project scope."
        r2 = "I have basic exposure to the tech stack and I'm currently upskilling."

    transcript = [
        {"sender": "AI Recruiter", "text": "Are you interested in this role?"},
        {"sender": "Candidate", "text": r1},
        {"sender": "AI Recruiter", "text": "Do you have hands-on experience in our required tech stack?"},
        {"sender": "Candidate", "text": r2}
    ]
    
    interest_score = calculate_dynamic_interest(transcript)
    return interest_score, transcript

def compute_final_score_agent(match_score, interest_score):
    final_score = (0.7 * match_score) + (0.3 * interest_score)
    return round(final_score, 2)
# =========================================================================

# =========================================================================
# ===== INTELLIGENT LLM EVALUATION AGENT =====
# =========================================================================
def evaluate_candidate_with_llm(jd_skills, resume_skills, chat_history, api_key):
    import google.generativeai as genai
    import json
    import time
    
    if not api_key or not chat_history:
        return None
        
    genai.configure(api_key=api_key)
    ans_text = " ".join([m["text"] for m in chat_history if m["sender"] == "Candidate"])
    
    if not ans_text.strip(): return None

    prompt = f"""
    You are an AI recruiter scoring candidate suitability.

    TASK:
    Given:
    1. Job Description skills: {', '.join(jd_skills)}
    2. Candidate resume skills: {', '.join(resume_skills)}
    3. Candidate answer: {ans_text}

    Perform intelligent evaluation WITHOUT strict keyword matching.

    RULES:
    - Normalize similar skills (e.g., ML = Machine Learning, NLP = Natural Language Processing)
    - Identify:
      • Matched Skills
      • Partial Matches (related/mentioned but not strong)
      • Missing Skills
    - Do NOT duplicate skills (ML & Machine Learning should be one)

    SCORING:
    1. Match Score (0–100):
    - Full match = 1 point
    - Partial match = 0.5 point
    - Match Score = (matched + 0.5 × partial) / total JD skills × 100 (If total is 0, output 0)

    2. Interest Score (0–100):
    - Based on:
      • Relevance to job description
      • Mention of ML/NLP/API/Deployment concepts
      • Technical clarity
    - DO NOT use word count

    3. Final Score:
    Final = (0.70 × Match) + (0.30 × Interest)

    4. Confidence:
    - High (>70)
    - Medium (40–70)
    - Low (<40)

    5. Decision:
    - Strong Hire → match >60 AND interest >60
    - Consider → match >40
    - Reject → otherwise

    OUTPUT FORMAT (STRICT JSON):
    {{
      "matched_skills": [],
      "partial_matches": [],
      "missing_skills": [],
      "match_score": 0.0,
      "interest_score": 0.0,
      "final_score": 0.0,
      "confidence": "Low",
      "decision": "Reject",
      "reason": "Short explanation"
    }}
    """
    
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target_model = available_models[0] if available_models else "models/gemini-1.5-flash"
        for pref in ["models/gemini-pro", "models/gemini-1.5-flash", "models/gemini-1.5-pro", "models/gemini-1.0-pro"]:
            if pref in available_models:
                target_model = pref
                break
                
        model = genai.GenerativeModel(target_model)
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = model.generate_content(prompt)
                if response.text:
                    out = response.text.replace('```json', '').replace('```', '').strip()
                    return json.loads(out)
            except Exception as e:
                if '429' in str(e) or 'quota' in str(e).lower():
                    if attempt < max_retries - 1:
                        time.sleep(8)
                        continue
                break 
    except Exception:
        pass
            
    return None

def generate_ai_conversation(jd_text, resume_text, api_key, history=[], topics_covered=[], conf_score=0.0):
    import google.generativeai as genai
    import time
    genai.configure(api_key=api_key)

    hist_text = "\n".join([f"{m['sender']}: {m['text']}" for m in history])
    topics_str = ", ".join(topics_covered) if topics_covered else "None"
    
    prompt = f"""
    You are a professional AI recruiter conducting a realistic interview.

    JOB DESCRIPTION:
    {jd_text}

    CANDIDATE RESUME:
    {resume_text}

    PAST CONVERSATION:
    {hist_text}
    
    INTERVIEW STATUS:
    Topics successfully covered so far: {topics_str}
    Current candidate average confidence score: {conf_score}/100

    TASK:
    - Generate ONLY the NEXT single question from the AI Recruiter.
    - Do NOT simulate or guess the Candidate's answer. Stop immediately after asking the question.
    - Make the question realistic, human-like, and tailored to the resume and previous answers.
    - If the current confidence score is weak (< 70) and history exists, ask a probing follow-up question.
    - If the score is strong, move to a new critical topic missing from the 'Topics covered' list.
    
    FORMAT STRICTLY:
    <your question here without any prefix>
    """
    
    try:
        try:
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        except Exception as e:
            raise Exception(f"Auth Error: Could not fetch models. Verify your API key. ({e})")

        if not available_models:
            raise Exception("Your API key does not have access to any text generation models.")

        best_model_name = available_models[0] 
        for pref in ["models/gemini-pro", "models/gemini-1.5-flash", "models/gemini-1.5-pro", "models/gemini-1.0-pro"]:
            if pref in available_models:
                best_model_name = pref
                break

        model = genai.GenerativeModel(best_model_name)
        
        max_retries = 3
        last_error = None
        for attempt in range(max_retries):
            try:
                response = model.generate_content(prompt)
                out = response.text
                if out.startswith("AI Recruiter:"): 
                    out = out.replace("AI Recruiter:", "").strip()
                return out.strip()
            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                if '429' in err_str or 'quota' in err_str:
                    if attempt < max_retries - 1:
                        time.sleep(8) 
                        continue
                raise Exception(f"API Error ({best_model_name}): {str(e)}")
                
        raise Exception(f"API Quota exceeded. Max retries hit ({best_model_name}): {str(last_error)}")
        
    except Exception as e:
        raise Exception(str(e))
# =========================================================================


# ==========================================
# 3. EXISTING HELPER FUNCTIONS (Preserved)
# ==========================================
def extract_text(file):
    if file.name.endswith(".pdf"):
        with pdfplumber.open(file) as pdf:
            return "\n".join([page.extract_text() or "" for page in pdf.pages])
    elif file.name.endswith(".docx"):
        doc = Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    elif file.name.endswith(".txt"):
        return file.read().decode("utf-8")
    return ""

def extract_name_from_resume(text):
    lines = text.strip().split("\n")
    for line in lines:
        line = line.strip()
        if line.lower().startswith("name"):
            return line.split(":")[-1].strip().title()
        if len(line.split()) >= 2 and len(line) < 40:
            return line.title()
    return "Candidate"


# =====================================================================
# ===== NEW ENHANCED FUNCTIONS (ADDED WITHOUT REMOVING EXISTING) ======
# =====================================================================

def normalize_skills_helper(raw_skills):
    """1. SKILL NORMALIZATION FUNCTION"""
    mapping = {
        "ml": "Machine Learning",
        "nlp": "Natural Language Processing",
        "js": "JavaScript",
        "react.js": "React",
        "node": "Node.js",
        "aws": "AWS",
        "gcp": "GCP"
    }
    normalized = set()
    for skill in raw_skills:
        s_low = skill.lower().strip()
        normalized.add(mapping.get(s_low, skill.title()))
    return list(normalized)

def detect_partial_matches(jd_skills, candidate_skills):
    """2. PARTIAL MATCH DETECTION FUNCTION"""
    matched = []
    partial = []
    missing = []
    
    cand_lower = [s.lower() for s in candidate_skills]
    jd_lower = [s.lower() for s in jd_skills]
    
    for jd_skill in jd_lower:
        if jd_skill in cand_lower:
            matched.append(jd_skill.title())
        else:
            # Check for substrings to assign partial match
            is_partial = False
            for c_skill in cand_lower:
                if jd_skill in c_skill or c_skill in jd_skill:
                    partial.append(jd_skill.title())
                    is_partial = True
                    break
            if not is_partial:
                missing.append(jd_skill.title())
                
    return matched, partial, missing

def enhanced_match_score(matched_count, partial_count, total_count):
    """3. NEW MATCH SCORE FUNCTION (ENHANCED)"""
    if total_count == 0:
        return 0.0
    return round(((matched_count + (0.5 * partial_count)) / total_count) * 100, 2)

def advanced_interest_score(ans_text, jd_skills):
    """4. ADVANCED INTEREST SCORING FUNCTION"""
    if not ans_text.strip():
        return None
        
    ans_lower = ans_text.lower()
    
    # Relevance to JD
    relevance = 0
    if jd_skills:
        matched_jd = sum(1 for skill in jd_skills if skill.lower() in ans_lower)
        relevance = min(100, (matched_jd / max(1, len(jd_skills))) * 100 * 2.0) 
    else:
        relevance = 50 
        
    # Technical Keywords
    tech_keys = ['ml', 'api', 'deployment', 'nlp', 'cloud', 'architecture', 'database']
    tech_count = sum(1 for k in tech_keys if k in ans_lower)
    tech_score = min(100, tech_count * 25)
    
    # Technical Clarity
    clarity = 70
    if any(w in ans_lower for w in ["maybe", "not sure", "i guess"]): clarity -= 30
    if "." in ans_lower or "," in ans_lower: clarity += 15
    clarity = min(100, max(0, clarity))
    
    interest = (0.5 * relevance) + (0.3 * tech_score) + (0.2 * clarity)
    return round(interest, 2)

def semantic_skill_boost(ans_text):
    """5. SEMANTIC SKILL BOOST FUNCTION"""
    ans_lower = ans_text.lower()
    boosted_skills = []
    
    if "api" in ans_lower:
        boosted_skills.extend(["Flask", "FastAPI"])
    if "chatbot" in ans_lower or "conversation" in ans_lower:
        boosted_skills.append("Natural Language Processing")
    if "cloud" in ans_lower:
        boosted_skills.extend(["AWS", "Azure"])
        
    return boosted_skills

def get_decision(match, interest):
    """6. DECISION FUNCTION"""
    if interest is None:
        return "Pending Evaluation"
        
    if match > 60 and interest > 60:
        return "Strong Hire"
    elif match > 30 and interest > 70:
        return "Consider (High Potential)"
    elif match > 40:
        return "Consider"
    else:
        return "Reject"

def get_confidence(final_score, interest_score):
    """7. CONFIDENCE FUNCTION"""
    if interest_score is None:
        return "N/A"
        
    if final_score > 70:
        return "High"
    elif final_score >= 40:
        return "Medium"
    else:
        return "Low"

def get_potential(interest_score):
    """8. POTENTIAL FUNCTION"""
    if interest_score is None:
        return "N/A"
        
    if interest_score > 80:
        return "High"
    elif interest_score > 60:
        return "Medium"
    else:
        return "Low"

def generate_recruiter_insight(match_score, interest_score, missing_skills):
    """9. RECRUITER INSIGHT FUNCTION"""
    if interest_score is None:
        return "Candidate has not responded yet. Start AI interview to evaluate interest."
        
    if match_score > 60 and interest_score > 60:
        insight = "Candidate demonstrates strong technical alignment and high engagement."
    elif match_score > 40:
        insight = "Candidate shows acceptable technical overlap but requires deeper probing."
    else:
        insight = "Candidate lacks core requirements for this specific role."
        
    if missing_skills:
        insight += f" Note: They are currently missing explicit experience with {', '.join(missing_skills[:2])}."
        
    return insight

def get_enhanced_evaluation(jd_skills, resume_skills, chat_history):
    """10. CREATE NEW FINAL RESULT OBJECT"""
    ans_text = " ".join([m["text"] for m in chat_history if m["sender"] == "Candidate"])
    
    norm_jd = normalize_skills_helper(jd_skills)
    norm_res = normalize_skills_helper(resume_skills)
    
    semantic_additions = semantic_skill_boost(ans_text)
    total_candidate_skills = list(set(norm_res + semantic_additions))
    
    matched, partial, missing = detect_partial_matches(norm_jd, total_candidate_skills)
    
    enh_match = enhanced_match_score(len(matched), len(partial), len(norm_jd))
    enh_interest = advanced_interest_score(ans_text, norm_jd)
    
    if enh_interest is None:
        enh_final = enh_match
    else:
        enh_final = round((0.7 * enh_match) + (0.3 * enh_interest), 2)
    
    decision = get_decision(enh_match, enh_interest)
    confidence = get_confidence(enh_final, enh_interest)
    potential = get_potential(enh_interest)
    insight = generate_recruiter_insight(enh_match, enh_interest, missing)
    
    return {
        "enhanced_match_score": enh_match,
        "enhanced_interest_score": enh_interest,
        "final_score": enh_final,
        "decision": decision,
        "confidence": confidence,
        "potential": potential,
        "insight": insight,
        "matched_skills": matched,
        "partial_matches": partial,
        "missing_skills": missing
    }

# =====================================================================


# 4. STATE INITIALIZATION
if "chat_history" not in st.session_state: st.session_state.chat_history = {}
if "interest_scores" not in st.session_state: st.session_state.interest_scores = {}

# 5. TITLE SECTION
title_html = """
<div style="text-align: center; padding: 2rem 0; margin-bottom: 2rem;">
    <h1 class="header-text">🤖 AI Talent Scouting Agent</h1>
    <p style="color: #cbd5f5 !important; font-size: 1.3rem; opacity: 0.9;">High-End Resume Matching & Conversational Engagement.</p>
</div>
"""
st.markdown(re.sub(r'\s+', ' ', title_html), unsafe_allow_html=True)

# 6. INPUT CARDS (TWO COLUMNS)
col_jd, col_res = st.columns(2, gap="large")

with col_jd:
    st.markdown(re.sub(r'\s+', ' ', """<div class="glass-card-hook"></div>"""), unsafe_allow_html=True)
    st.subheader("📝 Job Description")
    jd_file = st.file_uploader(
        "Upload JD (PDF/TXT/DOCX)",
        type=["pdf", "txt", "docx"],
        key="jd_uploader"
    )
    jd_input = st.text_area("Or Paste JD Requirements", height=150, placeholder="Define the role, tech stack, and responsibilities...")

with col_res:
    st.markdown(re.sub(r'\s+', ' ', """<div class="glass-card-hook"></div>"""), unsafe_allow_html=True)
    st.subheader("📄 Candidate Resumes")
    resume_files = st.file_uploader(
        "Upload Resumes (PDF/TXT/DOCX)",
        type=["pdf", "txt", "docx"],
        accept_multiple_files=True,
        key="resume_uploader"
    )

    if resume_files:
        st.markdown(re.sub(r'\s+', ' ', f"""<p style="color: #38bdf8; font-weight: 600; margin-top: 10px;">Number of uploaded resumes: {len(resume_files)}</p>"""), unsafe_allow_html=True)
        for i, file in enumerate(resume_files):
            st.markdown(re.sub(r'\s+', ' ', f"""<p style="color: #cbd5f5; font-size: 0.9rem; margin-top: -10px; margin-bottom: 5px;">Resume {i+1}: {file.name}</p>"""), unsafe_allow_html=True)
    else:
        st.info("Please upload at least one resume")

    st.markdown(re.sub(r'\s+', ' ', """<hr style="border-color: rgba(255,255,255,0.1); margin: 20px 0;">"""), unsafe_allow_html=True)
    st.markdown("#### Or Enter Resumes Manually")
    num_resumes = st.number_input("Number of resumes to add manually", min_value=0, max_value=10, value=1, step=1)
    
    if num_resumes > 0:
        st.markdown(re.sub(r'\s+', ' ', f"""<p style="color: #38bdf8; font-size: 0.9rem; margin-bottom: 10px;">You are adding {num_resumes} manual resumes.</p>"""), unsafe_allow_html=True)
        
    pasted_resumes_list = []
    for i in range(num_resumes):
        p_text = st.text_area(f"Resume {i+1}", height=120, key=f"dynamic_res_{i}", placeholder="Paste candidate resume here...")
        pasted_resumes_list.append(p_text)

# 7. CENTERED BUTTON ROWS
st.markdown(re.sub(r'\s+', ' ', """<br>"""), unsafe_allow_html=True)

c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    run_clicked = st.button("🚀 RUN MATCHING", type="primary", use_container_width=True)

st.markdown(re.sub(r'\s+', ' ', """<br>"""), unsafe_allow_html=True)

c4, c5, c6 = st.columns([1, 2, 1])
with c5:
    reset_clicked = st.button("🔄 RESET WORKSPACE", type="secondary", use_container_width=True)

# 8. ACTIONS LOGIC 
if run_clicked:
    resumes_dict = {}
    final_jd = jd_input.strip() or (extract_text(jd_file) if jd_file else "")
    st.session_state["jd_raw"] = final_jd

    if resume_files:
        for f in resume_files:
            txt = extract_text(f)
            if txt.strip(): resumes_dict[extract_name_from_resume(txt)] = txt
            
    for p_text in pasted_resumes_list:
        if p_text.strip():
            name = extract_name_from_resume(p_text)
            if name == "Candidate":
                name = f"Manual Candidate {len(resumes_dict) + 1}"
            resumes_dict[name] = p_text

    if not final_jd:
        st.error("Missing Job Description! Please upload or paste a JD.")
    elif not resumes_dict:
        st.error("No Resumes provided! Please upload or paste at least one resume.")
    else:
        with st.spinner("Initializing 3D Match AI..."):
            jd_data = parse_jd_agent(final_jd)
            st.session_state["jd_data"] = jd_data
            
            results = []
            for name, r_txt in resumes_dict.items():
                resume_data = parse_resume_agent(r_txt)
                
                # Check if real AI is enabled for chat
                if st.session_state.get("enable_ai", False) and st.session_state.get("llm_provider", "") == "gemini":
                    transcript = [] 
                else:
                    _, transcript = simulate_conversation_agent(resume_data)
                
                # We use the new Enhanced Evaluation completely here so initial sorting is perfectly accurate.
                eval_data = get_enhanced_evaluation(jd_data["skills"], resume_data.get("skills", []), transcript)
                st.session_state.chat_history[name] = transcript
                
                eval_data["name"] = name
                eval_data["raw_resume"] = r_txt
                eval_data["raw_res_skills"] = resume_data.get("skills", [])
                results.append(eval_data)
            
            st.session_state["ranked_candidates"] = sorted(results, key=lambda x: x["final_score"], reverse=True)

if reset_clicked:
    st.session_state.clear()
    st.rerun()

# 9. RESULTS SECTION 
if st.session_state.get("ranked_candidates"):
    st.divider()
    st.markdown(re.sub(r'\s+', ' ', """<h2 style="text-align: center; margin-bottom: 2rem;">🏆 Ranked Final Shortlist</h2>"""), unsafe_allow_html=True)
    
    for idx, c in enumerate(st.session_state["ranked_candidates"]):
        cid = c["name"]
        
        # --- RE-COMPUTE ENHANCED METRICS DYNAMICALLY ---
        active_chat = st.session_state.get(f"ai_hist_{cid}", st.session_state.chat_history.get(cid, []))
        jd_raw_s = st.session_state.get("jd_data", {}).get("skills", [])
        res_raw_s = c.get("raw_res_skills", [])
        
        enh_eval = get_enhanced_evaluation(jd_raw_s, res_raw_s, active_chat)
        
        # Override the old values to ensure no mismatch
        match_s = enh_eval["enhanced_match_score"]
        int_s = enh_eval["enhanced_interest_score"]
        final_s = enh_eval["final_score"]
        
        c["match_score"] = match_s
        c["interest_score"] = int_s
        c["final_score"] = final_s
        
        # Format variables for display gracefully handling None states
        int_display = f"{int_s}%" if int_s is not None else "Not Evaluated"
        int_bar_width = int_s if int_s is not None else 0
        
        # Colors for Decision/Confidence/Potential
        conf_color = "#22c55e" if enh_eval['confidence'] == "High" else "#f59e0b" if enh_eval['confidence'] == "Medium" else "#ef4444" if enh_eval['confidence'] == "Low" else "#94a3b8"
        pot_color = "#22c55e" if enh_eval['potential'] == "High" else "#f59e0b" if enh_eval['potential'] == "Medium" else "#ef4444" if enh_eval['potential'] == "Low" else "#94a3b8"
        
        if enh_eval['decision'] == "Strong Hire": dec_color = "#22c55e"
        elif "Consider" in enh_eval['decision']: dec_color = "#f59e0b"
        elif enh_eval['decision'] == "Pending Evaluation": dec_color = "#94a3b8"
        else: dec_color = "#ef4444"

        is_top = (idx == 0)
        top_badge = """<span style="font-size: 0.8rem; background: linear-gradient(90deg, #f59e0b, #fbbf24); color: #000; padding: 4px 10px; border-radius: 20px; margin-left: 10px; vertical-align: middle; font-weight: 800; box-shadow: 0 0 10px rgba(245, 158, 11, 0.6);">🏆 TOP CANDIDATE</span>""" if is_top else ""
        top_style = "border: 2px solid #f59e0b; box-shadow: 0 10px 40px rgba(245, 158, 11, 0.2), inset 0 0 20px rgba(245, 158, 11, 0.05);" if is_top else ""
        
        with st.container():
            card_html = f"""
            <div class="result-card" style="{top_style}">
                <h3 style="margin: 0; color: #ffffff; display: flex; align-items: center;">
                    {idx+1}. {cid} {top_badge}
                </h3>
                <div style="display: flex; justify-content: space-between; margin-top: 15px;">
                    <div style="flex: 1; padding-right: 15px;">
                        <p style="margin: 0; font-size: 0.9rem; color: #cbd5f5;">Match Score</p>
                        <h4 style="margin: 0; color: #ffffff; text-shadow: 0 0 10px #3b82f6;">{match_s}%</h4>
                        <div style="background: rgba(0,0,0,0.5); border-radius: 5px; height: 10px; margin-top: 5px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.8);">
                            <div style="background: linear-gradient(90deg, #3b82f6, #60a5fa); border-radius: 5px; height: 10px; width: {match_s}%; box-shadow: 0 0 15px #3b82f6;"></div>
                        </div>
                    </div>
                    <div style="flex: 1; padding-right: 15px;">
                        <p style="margin: 0; font-size: 0.9rem; color: #cbd5f5;">Interest Score</p>
                        <h4 style="margin: 0; color: #ffffff; text-shadow: 0 0 10px #8b5cf6;">{int_display}</h4>
                        <div style="background: rgba(0,0,0,0.5); border-radius: 5px; height: 10px; margin-top: 5px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.8);">
                            <div style="background: linear-gradient(90deg, #8b5cf6, #c084fc); border-radius: 5px; height: 10px; width: {int_bar_width}%; box-shadow: 0 0 15px #8b5cf6;"></div>
                        </div>
                    </div>
                    <div style="flex: 1;">
                        <p style="margin: 0; font-size: 1rem; color: #ffffff; font-weight: bold;">Final Score</p>
                        <h3 style="margin: 0; color: #ffffff; text-shadow: 0 0 20px #22c55e;">{final_s}%</h3>
                        <div style="background: rgba(0,0,0,0.5); border-radius: 5px; height: 12px; margin-top: 5px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.8);">
                            <div style="background: linear-gradient(90deg, #22c55e, #10b981); border-radius: 5px; height: 12px; width: {final_s}%; box-shadow: 0 0 15px #22c55e;"></div>
                        </div>
                    </div>
                </div>
            </div>
            """
            st.markdown(re.sub(r'\s+', ' ', card_html), unsafe_allow_html=True)
            
            # ========================================================
            # 11. STREAMLIT INTEGRATION - AI Recruiter Enhanced Evaluation
            # ========================================================
            enhanced_eval_html = f"""
            <div class="glass-skill-card" style="margin-top: -5px; margin-bottom: 20px; border-left: 4px solid #8b5cf6;">
                <h5 style="margin-bottom: 15px; color: #ffffff; text-shadow: 0 0 10px #8b5cf6;">🌟 AI Recruiter Enhanced Evaluation</h5>
                <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
                    <div style="flex: 1;">
                        <span style="color: #cbd5f5; font-size: 0.95rem;">Decision: </span>
                        <strong style="color: {dec_color}; font-size: 1.05rem; text-shadow: 0 0 8px {dec_color};">{enh_eval['decision'].upper()}</strong>
                    </div>
                    <div style="flex: 1;">
                        <span style="color: #cbd5f5; font-size: 0.95rem;">Confidence: </span>
                        <strong style="color: {conf_color}; font-size: 1.05rem;">{enh_eval['confidence']}</strong>
                    </div>
                    <div style="flex: 1;">
                        <span style="color: #cbd5f5; font-size: 0.95rem;">Potential: </span>
                        <strong style="color: {pot_color}; font-size: 1.05rem;">{enh_eval['potential']}</strong>
                    </div>
                </div>
                <div style="background: rgba(0,0,0,0.2); padding: 12px; border-radius: 8px; border-left: 2px solid #8b5cf6;">
                    <p style="margin: 0; color: #e2e8f0; font-size: 0.95rem; font-style: italic;">"{enh_eval['insight']}"</p>
                </div>
            </div>
            """
            st.markdown(re.sub(r'\s+', ' ', enhanced_eval_html), unsafe_allow_html=True)
            # ========================================================
            
            st.markdown(re.sub(r'\s+', ' ', """<hr style="border-color: rgba(255,255,255,0.1); margin: 25px 0;">"""), unsafe_allow_html=True)
            st.markdown(re.sub(r'\s+', ' ', """<h4 style="margin-bottom: 15px;">💡 3D Skill Gap Analysis</h4>"""), unsafe_allow_html=True)
            
            g_col1, g_col2, g_col3 = st.columns(3)
            
            with g_col1:
                matched_html = "".join([f"""<span class="skill-pill pill-matched">{s.title()}</span>""" for s in enh_eval['matched_skills']]) if enh_eval['matched_skills'] else """<span style="color:#94a3b8;">None</span>"""
                card_matched = f"""<div class="glass-skill-card"><h5 style="margin-bottom:15px;">✅ Matched Skills</h5>{matched_html}</div>"""
                st.markdown(re.sub(r'\s+', ' ', card_matched), unsafe_allow_html=True)
                
            with g_col2:
                partial_html = "".join([f"""<span class="skill-pill pill-partial">{s.title()}</span>""" for s in enh_eval['partial_matches']]) if enh_eval['partial_matches'] else """<span style="color:#94a3b8;">None</span>"""
                card_partial = f"""<div class="glass-skill-card"><h5 style="margin-bottom:15px;">⚠️ Partial Match</h5>{partial_html}</div>"""
                st.markdown(re.sub(r'\s+', ' ', card_partial), unsafe_allow_html=True)
                
            with g_col3:
                missing_html = "".join([f"""<span class="skill-pill pill-missing">{s.title()}</span>""" for s in enh_eval['missing_skills']]) if enh_eval['missing_skills'] else """<span style="color:#94a3b8;">None</span>"""
                card_missing = f"""<div class="glass-skill-card"><h5 style="margin-bottom:15px;">❌ Missing Skills</h5>{missing_html}</div>"""
                st.markdown(re.sub(r'\s+', ' ', card_missing), unsafe_allow_html=True)

            st.markdown(re.sub(r'\s+', ' ', """<br>"""), unsafe_allow_html=True)

            # ========================================================
            # ===== MANUAL USER INPUT CHAT SYSTEM APPLIED =====
            # ========================================================
            enable_llm = st.session_state.get("enable_ai", False)
            api_key = st.session_state.get("api_key", "")
            provider = st.session_state.get("llm_provider", "")

            exp_title = f"💬 Engage {cid} (Live AI Conversation)" if (enable_llm and provider == "gemini") else f"💬 Engage {cid} (Simulated AI Conversation)"
            
            with st.expander(exp_title):
                if enable_llm and api_key and provider == "gemini":
                    
                    st.info("🤖 Using Live Gemini AI")
                    cid_hist_key = f"ai_hist_{cid}"
                    cid_step_key = f"ai_step_{cid}"
                    cid_done_key = f"ai_done_{cid}"

                    if cid_hist_key not in st.session_state:
                        st.session_state[cid_hist_key] = []
                        st.session_state[cid_step_key] = 0
                        st.session_state[cid_done_key] = False
                    
                    if not st.session_state[cid_hist_key]:
                        if st.button("🚀 Start Live Interview", key=f"start_{cid}"):
                            with st.spinner("AI is generating the first question..."):
                                try:
                                    q = generate_ai_conversation(
                                        st.session_state.get("jd_raw", ""), 
                                        c.get("raw_resume", ""), 
                                        api_key, 
                                        []
                                    )
                                    st.session_state[cid_hist_key].append({"sender": "AI Recruiter", "text": q})
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"API Error: {e}")
                    
                    for msg in st.session_state[cid_hist_key]:
                        bg, col = ("rgba(0,0,0,0.4)", "#38bdf8") if msg["sender"] in ["AI Recruiter", "System"] else ("rgba(59,130,246,0.1)", "#22c55e")
                        chat_bubble = f"""
                        <div style="background:{bg};padding:15px;border-radius:12px;margin-bottom:10px;border-left:4px solid {col}; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
                            <b style="color:{col}">{msg['sender']}:</b> <span style="color: #ffffff;">{msg['text']}</span>
                        </div>
                        """
                        st.markdown(re.sub(r'\s+', ' ', chat_bubble), unsafe_allow_html=True)

                    if st.session_state[cid_hist_key] and not st.session_state[cid_done_key]:
                        if st.session_state[cid_hist_key][-1]["sender"] == "AI Recruiter":
                            with st.form(key=f"form_{cid}_{st.session_state[cid_step_key]}"):
                                user_input = st.text_input("Your Answer:", key=f"input_{cid}_{st.session_state[cid_step_key]}")
                                submit_btn = st.form_submit_button("Submit Answer")
                                
                                if submit_btn:
                                    if user_input.strip():
                                        st.session_state[cid_hist_key].append({"sender": "Candidate", "text": user_input.strip()})
                                        st.session_state[cid_step_key] += 1
                                        
                                        MAX_QUESTIONS = 7
                                        current_step = st.session_state[cid_step_key]
                                        
                                        if current_step >= MAX_QUESTIONS:
                                            st.session_state[cid_done_key] = True
                                            st.session_state[cid_hist_key].append({
                                                "sender": "System", 
                                                "text": f"Interview complete! Results have been updated."
                                            })
                                            st.rerun()
                                        else:
                                            with st.spinner("Adapting next question..."):
                                                try:
                                                    next_q = generate_ai_conversation(
                                                        st.session_state.get("jd_raw", ""), 
                                                        c.get("raw_resume", ""), 
                                                        api_key, 
                                                        st.session_state[cid_hist_key]
                                                    )
                                                    st.session_state[cid_hist_key].append({"sender": "AI Recruiter", "text": next_q})
                                                except Exception as e:
                                                    st.session_state[cid_hist_key].append({"sender": "System", "text": f"API Error: {e}"})
                                            st.rerun()
                                    else:
                                        st.warning("Please type an answer before submitting.")

                else:
                    st.info("🤖 Using Simulation")
                    st.markdown("### 💬 Simulated AI Conversation")
                    chat_html = ""
                    for msg in st.session_state.chat_history[cid]:
                        bg, col = ("rgba(0,0,0,0.4)", "#38bdf8") if msg["sender"] in ["AI Recruiter", "System"] else ("rgba(59,130,246,0.1)", "#22c55e")
                        chat_html += f"""
                        <div style="background:{bg};padding:15px;border-radius:12px;margin-bottom:10px;border-left:4px solid {col}; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
                            <b style="color:{col}">{msg['sender']}:</b> <span style="color: #ffffff;">{msg['text']}</span>
                        </div>
                        """
                    st.markdown(re.sub(r'\s+', ' ', chat_html), unsafe_allow_html=True)
            # ========================================================

    # DOWNLOAD FEATURE
    st.markdown(re.sub(r'\s+', ' ', """<br>"""), unsafe_allow_html=True)
    c7, c8, c9 = st.columns([1, 2, 1])
    with c8:
        download_data = []
        for cand in st.session_state["ranked_candidates"]:
            download_data.append({
                "Name": cand["name"],
                "Match Score": cand["match_score"],
                "Interest Score": cand.get("interest_score", "Not Evaluated"),
                "Final Score": cand["final_score"]
            })
            
        csv = pd.DataFrame(download_data).to_csv(index=False).encode('utf-8')
        st.download_button("📥 DOWNLOAD RESULTS (CSV)", data=csv, file_name="talent_scout_report.csv", mime="text/csv", type="secondary", use_container_width=True)