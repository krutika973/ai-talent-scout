# 🤖 AI-Powered Talent Scouting & Engagement Agent

## 🚀 Overview

Recruiters often spend significant time manually screening candidates and assessing their interest.
This project automates the entire process using AI by:

* Parsing Job Descriptions (JD)
* Matching resumes with required skills
* Engaging candidates using AI (Gemini)
* Evaluating candidate interest through conversation
* Generating **Match Score** and **Interest Score**
* Producing a **ranked shortlist** for quick decision-making

---

## 🛠 Tech Stack

* **Python**
* **Streamlit** (Frontend UI)
* **Gemini API** (AI interaction)
* **NLP** (Skill extraction & matching)
* **Pandas** (Data handling)

---

## ⚙️ How to Run the Project

### 1️⃣ Clone the repository

```bash
git clone https://github.com/krutika973/ai-talent-scout.git
cd ai-talent-scout
```

### 2️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Run the application

```bash
streamlit run app.py
```

---

## 📊 Features

* 📄 Job Description parsing
* 📑 Resume analysis (PDF/TXT/DOCX)
* 🧠 Skill extraction using NLP
* 🤖 AI-powered candidate interaction (Gemini)
* 📈 Match Score calculation
* 💬 Interest Score evaluation via conversation
* 🏆 Ranked shortlist of candidates
* 📥 Download results as CSV
* 📊 Skill gap analysis (Matched / Missing / Additional skills)

---

## ⚙️ Scoring Logic

* **Match Score**
  Based on how well candidate skills match the Job Description

* **Interest Score**
  Based on AI conversation:

  * relevance
  * clarity
  * technical depth

* **Final Score Calculation**

```
Final Score = (0.7 × Match Score) + (0.3 × Interest Score)
```

---

## 🏗 System Architecture

1. Input Job Description
2. Upload / Enter Candidate Resumes
3. Extract skills using NLP
4. Perform skill matching
5. Initiate AI conversation (Gemini)
6. Evaluate responses → Interest Score
7. Combine scores → Final Score
8. Generate ranked shortlist

---

## 📸 Sample Output

* Ranked candidates with scores
* Skill gap analysis
* AI recruiter evaluation
* Downloadable report (CSV)

---

## 🎥 Demo Video

(https://drive.google.com/file/d/1id2Hpv1IlliGMjKhoTUk2kkfqVopoPm6/view?usp=sharing)

---

## 📂 Repository

👉 https://github.com/krutika973/ai-talent-scout

---

## 👩‍💻 Author

**Krutika Kanade**
GitHub: https://github.com/krutika973

---

## 📌 Notes

* Ensure Gemini API key is configured before running
* Designed for hackathon submission and real-world recruiter use
