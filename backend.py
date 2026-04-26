import os
import re
import json
import math
import numpy as np
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
from pathlib import Path

# Optional: placeholder API key. Replace with your own key for real OpenAI/Gemini integration.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-key-here")

try:
    from langchain.embeddings import OpenAIEmbeddings
    from langchain.llms import OpenAI
except ImportError:
    OpenAIEmbeddings = None
    OpenAI = None

try:
    import faiss
except ImportError:
    faiss = None

try:
    import docx
except ImportError:
    docx = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

app = FastAPI(title="Talent Scouting & Engagement Agent")

COMMON_SKILLS = [
    "python", "java", "javascript", "react", "node.js", "node", "sql", "aws", "azure",
    "docker", "kubernetes", "ml", "machine learning", "nlp", "data analysis", "pandas",
    "tensorflow", "pytorch", "leadership", "communication", "project management",
    "sales", "marketing", "design", "product management", "cloud", "devops"
]


def _load_text_from_pdf(file_path: Path) -> str:
    if not pdfplumber:
        return ""
    text = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text.append(page_text)
    return "\n".join(text)


def _load_text_from_docx(file_path: Path) -> str:
    if not docx:
        return ""
    document = docx.Document(str(file_path))
    return "\n".join([p.text for p in document.paragraphs])


def load_resume_text(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return _load_text_from_pdf(file_path)
    if suffix == ".docx":
        return _load_text_from_docx(file_path)
    try:
        return file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def normalize_skill(skill: str) -> str:
    mapping = {
        "python": "python",
        "python3": "python",
        "python2": "python",
        "ml": "machine learning",
        "machine learning": "machine learning",
        "nlp": "nlp",
        "ai": "ai",
        "fastapi": "fastapi",
        "flask": "flask",
        "pandas": "pandas",
        "cloud": "cloud",
        "aws": "aws",
        "azure": "azure",
        "docker": "docker",
        "kubernetes": "kubernetes",
    }
    return mapping.get(skill.lower(), skill.lower())


def extract_skills(text: str) -> List[str]:
    if not text:
        return []

    role_words = r"developer|engineer|programmer|specialist|consultant|lead"
    skill_patterns = {
        "python": [
            r"\bpython(?:\s*[23])?\b",
            rf"\bpython[\s-]+(?:{role_words})\b",
        ],
        "machine learning": [
            r"\bmachine[\s-]+learning\b",
            r"\bml\b",
            rf"\bml[\s-]+(?:{role_words})\b",
        ],
        "nlp": [r"\bnlp\b", r"\bnatural[\s-]+language[\s-]+processing\b"],
        "fastapi": [r"\bfastapi\b", r"\bfast[\s-]*api\b"],
        "flask": [r"\bflask\b"],
        "pandas": [r"\bpandas\b"],
        "cloud": [r"\bcloud\b", r"\bcloud[\s-]+(?:{role_words})\b"],
        "aws": [r"\baws\b", r"\bamazon[\s-]+web[\s-]+services\b"],
        "azure": [r"\bazure\b", r"\bmicrosoft[\s-]+azure\b"],
        "docker": [r"\bdocker\b"],
        "kubernetes": [r"\bkubernetes\b", r"\bk8s\b"],
    }
    normalized_text = normalize_text(text)
    found = set()

    for skill, patterns in skill_patterns.items():
        if any(re.search(pattern, normalized_text, flags=re.IGNORECASE) for pattern in patterns):
            found.add(normalize_skill(skill))

    if re.search(r"\bpython(?:\s*[23])?\b", normalized_text, flags=re.IGNORECASE):
        found.add("python")

    return sorted(found)


def extract_keywords(text: str, skill_list: List[str]) -> List[str]:
    normalized = normalize_text(text)
    found = set()
    for skill in skill_list:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, normalized):
            found.add(skill)
    return sorted(found)


def parse_experience_level(text: str) -> str:
    normalized = text.lower()
    if "senior" in normalized or "lead" in normalized or "principal" in normalized:
        return "Senior"
    if "mid" in normalized or "intermediate" in normalized:
        return "Mid"
    if "junior" in normalized or "entry" in normalized or "associate" in normalized:
        return "Junior"
    return "Not specified"


def parse_jd(jd_text: str) -> Dict[str, Any]:
    """Parse the job description text into structured JSON output."""
    if not jd_text:
        return {"required_skills": [], "experience_level": "Not specified", "responsibilities": []}

    normalized = normalize_text(jd_text)

    skills = extract_skills(jd_text)
    experience = parse_experience_level(jd_text)

    responsibilities = []
    lines = [line.strip() for line in jd_text.splitlines() if line.strip()]
    for line in lines:
        if any(keyword in line.lower() for keyword in ["responsible", "responsibilities", "responsibility", "you will", "you are", "tasks"]):
            responsibilities.append(line)
    if not responsibilities:
        sentences = re.split(r"[\.\n]", jd_text)
        for sentence in sentences:
            if len(sentence.split()) > 6 and any(word in sentence.lower() for word in ["build", "design", "lead", "manage", "develop", "support"]):
                responsibilities.append(sentence.strip())
    responsibilities = responsibilities[:6]

    return {
        "required_skills": skills,
        "experience_level": experience,
        "responsibilities": responsibilities,
        "raw_text": jd_text,
    }


def extract_resume_data(resume_file: Path) -> Dict[str, Any]:
    """Extract candidate data from a resume file."""
    text = load_resume_text(resume_file)
    if not text:
        text = resume_file.name

    candidate_name = resume_file.stem
    skills = extract_skills(text)
    experience_level = parse_experience_level(text)

    projects = []
    for section in re.split(r"\n{2,}", text):
        lower = section.lower()
        if "project" in lower or "accomplishment" in lower:
            projects.append(section.strip())
    if not projects:
        projects = [s.strip() for s in text.splitlines()[:3] if len(s.split()) > 3]

    summary = " ".join(skills + [experience_level])
    return {
        "name": candidate_name,
        "skills": skills,
        "experience_level": experience_level,
        "projects": projects[:5],
        "resume_text": text,
        "summary": summary,
    }


def extract_resume_data_from_text(candidate_name: str, resume_text: str) -> Dict[str, Any]:
    """Extract candidate data from raw resume text without file I/O."""
    text = resume_text or ""
    skills = extract_skills(text)
    experience_level = parse_experience_level(text)

    projects = []
    for section in re.split(r"\n{2,}", text):
        lower = section.lower()
        if "project" in lower or "accomplishment" in lower:
            projects.append(section.strip())
    if not projects:
        projects = [s.strip() for s in text.splitlines()[:3] if len(s.split()) > 3]

    summary = " ".join(skills + [experience_level])
    return {
        "name": candidate_name,
        "skills": skills,
        "experience_level": experience_level,
        "projects": projects[:5],
        "resume_text": text,
        "summary": summary,
    }


def build_embeddings(texts: List[str]) -> np.ndarray:
    """Generate embeddings for a list of texts. Uses OpenAI via LangChain if available."""
    if OpenAIEmbeddings and OPENAI_API_KEY != "your-key-here":
        embeddings_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        return np.array(embeddings_model.embed_documents(texts), dtype=float)
    # Fallback dummy embeddings: simple bag-of-letters vectorization
    return np.array([[float(sum(ord(c) for c in t) % 1000) for _ in range(1536)] for t in texts], dtype=float)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def compute_match_score(jd_data: Dict[str, Any], candidate_data: Dict[str, Any]) -> tuple[float, List[str]]:
    """Compute candidate match from required JD skills and resume skills."""
    jd_skills = {
        normalize_skill(skill)
        for skill in jd_data.get("required_skills", [])
        if skill
    }
    if not jd_skills:
        jd_skills = set(extract_skills(jd_data.get("raw_text", "")))

    resume_skills = {
        normalize_skill(skill)
        for skill in candidate_data.get("skills", [])
        if skill
    }
    if not resume_skills:
        resume_skills = set(extract_skills(candidate_data.get("resume_text", "")))

    matched_skills = sorted(jd_skills & resume_skills)
    total_jd_skills = len(jd_skills)
    match_ratio = len(matched_skills) / total_jd_skills if total_jd_skills else 0

    score = match_ratio * 100
    score += len(matched_skills) * 5
    if "python" in jd_skills and "python" not in resume_skills:
        score -= 10
    if {"machine learning", "nlp"}.issubset(set(matched_skills)):
        score += 5

    score = max(0, min(100, score))
    return round(score, 1), matched_skills


def run_chat_assessment(candidate_data: Dict[str, Any], jd_data: Dict[str, Any]) -> Dict[str, Any]:
    """Simulate recruiter-to-candidate chat and return a chat transcript."""
    candidate_skills = candidate_data.get("skills", [])
    jd_skills = jd_data.get("required_skills", [])
    missing = [skill for skill in jd_skills if skill not in candidate_skills]

    follow_up = []
    if missing:
        follow_up.append(f"Can you describe your hands-on experience with {', '.join(missing[:2])}?")
    else:
        follow_up.append("Tell me about your most recent project that is directly related to this role.")

    follow_up.append("How do you prioritize time between technical delivery and stakeholder communication?")

    candidate_response = (
        "I have consistently worked on similar responsibilities and I enjoy bridging technical details with business goals. "
        "My recent project involved delivering a cross-functional product while working in an agile team."
    )

    return {
        "questions": follow_up,
        "response": candidate_response,
        "transcript": [
            {"role": "recruiter", "text": follow_up[0]},
            {"role": "candidate", "text": candidate_response},
        ],
    }


def calculate_interest_score(chat_response: Dict[str, Any]) -> float:
    """Score candidate interest based on answer quality and alignment."""
    response = chat_response.get("response", "").lower()
    score = 50
    if any(word in response for word in ["excited", "passionate", "looking forward", "interested"]):
        score += 20
    if any(word in response for word in ["deliver", "product", "stakeholder", "collaborate", "agile"]):
        score += 15
    if "no" in response or "not" in response and "experience" in response:
        score -= 10
    return float(max(0, min(100, score)))


def rank_candidates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Rank candidates by combined score."""
    for candidate in candidates:
        candidate["combined_score"] = round(
            0.7 * candidate.get("match_score", 0) + 0.3 * candidate.get("interest_score", 0), 1
        )
    return sorted(candidates, key=lambda x: x["combined_score"], reverse=True)


class JDRequest(BaseModel):
    jd_text: str


@app.post("/parse_jd")
def api_parse_jd(request: JDRequest):
    return parse_jd(request.jd_text)


@app.post("/match_candidate")
def api_match_candidate(jd_text: str = Form(...), resume_file: UploadFile = File(...)):
    jd_data = parse_jd(jd_text)
    temp_path = Path("tmp_resume")
    temp_path.mkdir(exist_ok=True)
    dest = temp_path / resume_file.filename
    with dest.open("wb") as f:
        f.write(resume_file.file.read())
    candidate_data = extract_resume_data(dest)
    match_score, matched_skills = compute_match_score(jd_data, candidate_data)
    candidate_metrics = {"score": match_score, "matched_skills": matched_skills}
    chat_data = run_chat_assessment(candidate_data, jd_data)
    interest = calculate_interest_score(chat_data)
    return {
        "candidate": candidate_data,
        "match": candidate_metrics,
        "chat": chat_data,
        "interest_score": interest,
    }
