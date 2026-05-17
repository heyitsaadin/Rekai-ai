"""
─────────────────────────────────────────────────────
  JARVIS QUIZ ROUTES — paste into app.py
  BEFORE the  init_db()  line at the bottom.

  Requirements:
      pip install pdfplumber
─────────────────────────────────────────────────────
"""

import json as _json
import pdfplumber
from datetime import datetime as _dt


# ──────────────────────────────────────────────
# QUIZ PAGE
# ──────────────────────────────────────────────

@app.route("/quiz")
def quiz():
    if "user" not in session:
        return redirect("/")
    heartbeat(session["user"])
    return render_template("quiz.html", username=session["user"])


# ──────────────────────────────────────────────
# SHARED: extract PDF text
# ──────────────────────────────────────────────

def _extract_pdf_text(pdf_file, max_pages=20, max_chars=7000):
    """Extract and return text from an uploaded PDF file object."""
    with pdfplumber.open(pdf_file) as pdf:
        pages_text = []
        for page in pdf.pages[:max_pages]:
            t = page.extract_text()
            if t:
                pages_text.append(t)
    raw = "\n".join(pages_text).strip()
    return raw[:max_chars]


# ──────────────────────────────────────────────
# GENERATE QUIZ FROM PDF
# ──────────────────────────────────────────────

@app.route("/generate_quiz", methods=["POST"])
def generate_quiz():
    """
    Accepts: PDF upload + optional form fields:
        count      (int, default 10)  — how many questions
        difficulty (str, default "mixed") — easy | mixed | hard

    Returns: { "questions": [ ... ] }  or  { "error": "..." }
    Each question: { question, options (4 strings), answer, explanation }
    """
    if "user" not in session:
        return _json.dumps({"error": "not_logged_in"}), 401, {"Content-Type": "application/json"}
    heartbeat(session["user"])

    # ── 1. Receive and validate PDF ──
    pdf_file = request.files.get("pdf")
    if not pdf_file or not pdf_file.filename.lower().endswith(".pdf"):
        return _json.dumps({"error": "Please upload a valid PDF file."}), 400, {"Content-Type": "application/json"}

    # ── 2. Read settings ──
    try:
        count = max(5, min(25, int(request.form.get("count", 10))))
    except (ValueError, TypeError):
        count = 10
    difficulty = request.form.get("difficulty", "mixed").strip().lower()
    if difficulty not in ("easy", "mixed", "hard"):
        difficulty = "mixed"

    # ── 3. Extract text ──
    try:
        study_material = _extract_pdf_text(pdf_file)
    except Exception as e:
        return _json.dumps({"error": f"Could not read PDF: {str(e)}"}), 400, {"Content-Type": "application/json"}

    if not study_material or len(study_material) < 100:
        return _json.dumps({"error": "PDF appears to be empty or image-only. Please use a text-based PDF."}), 400, {"Content-Type": "application/json"}

    # ── 4. Build difficulty instruction ──
    diff_instructions = {
        "easy":  "All questions should be straightforward recall questions that test basic understanding of facts and definitions. Keep language simple.",
        "mixed": "Mix difficulty: roughly one-third easy recall, one-third application/analysis, one-third deeper conceptual or evaluative questions.",
        "hard":  "All questions should be challenging: require analysis, comparison, inference, or critical evaluation. Avoid simple one-word fact recall."
    }
    diff_note = diff_instructions[difficulty]

    # ── 5. Prompt Groq ──
    API_KEY = os.environ["GROQ_API_KEY"]
    url     = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": "Bearer " + API_KEY, "Content-Type": "application/json"}

    system_prompt = f"""You are an expert academic exam question writer.
Your ONLY job is to read the study material provided and return exactly {count} multiple-choice questions as a raw JSON array.

DIFFICULTY SETTING: {diff_note}

CRITICAL RULES — follow every one:
1. Return ONLY a valid JSON array. No preamble, no markdown fences, no explanation.
2. Each element must have EXACTLY these keys:
     "question"    : the question string
     "options"     : an array of exactly 4 strings (the answer choices)
     "answer"      : the EXACT string from options that is correct
     "explanation" : a 2-3 sentence explanation covering WHY the answer is correct and what the concept means
3. Questions must be based strictly on the provided material.
4. QUESTION VARIETY IS MANDATORY — do NOT produce only single-word or single-name answer questions.
   Use a healthy mix of these question types:
     - "Explain why / how does X work…"
     - "What is the significance/impact/role of X?"
     - "Which of the following best describes…"
     - "Compare X and Y — what is the key difference?"
     - "What would happen if…"
     - "According to the material, what conclusion can be drawn about…"
     - "Which statement is most accurate regarding…"
5. Options must be plausible and specific — avoid vague distractors like "None of the above" or "All of the above".
6. Never repeat questions.
7. Return exactly {count} questions."""

    user_prompt = f"Study material:\n\n{study_material}\n\nGenerate {count} MCQ questions now."

    data = {
        "model":       "llama-3.1-8b-instant",
        "messages":    [
            {"role": "system",  "content": system_prompt},
            {"role": "user",    "content": user_prompt}
        ],
        "max_tokens":  3500,
        "temperature": 0.5,
    }

    try:
        res = requests.post(url, headers=headers, json=data, timeout=60)
        raw = res.json()["choices"][0]["message"]["content"].strip()

        # Strip any accidental markdown fences
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip().rstrip("`").strip()

        questions = _json.loads(raw)
        if not isinstance(questions, list) or len(questions) == 0:
            raise ValueError("Empty or invalid question list")

        return _json.dumps({"questions": questions}), 200, {"Content-Type": "application/json"}

    except _json.JSONDecodeError:
        return _json.dumps({"error": "AI returned an invalid response. Please try again."}), 500, {"Content-Type": "application/json"}
    except Exception as e:
        return _json.dumps({"error": f"Quiz generation failed: {str(e)}"}), 500, {"Content-Type": "application/json"}


# ──────────────────────────────────────────────
# GENERATE MODEL EXAM PAPER FROM PDF
# ──────────────────────────────────────────────

@app.route("/generate_exam", methods=["POST"])
def generate_exam():
    """
    Generates a formatted model exam paper (as plain text) from the uploaded PDF.
    Accepts: PDF upload + count + difficulty (same as generate_quiz).
    Returns: { "exam_paper": "..." }  or  { "error": "..." }

    The exam paper contains:
      - A cover header (subject inferred from content, date, instructions)
      - Numbered MCQ questions with A/B/C/D choices
      - An answer key at the end
    """
    if "user" not in session:
        return _json.dumps({"error": "not_logged_in"}), 401, {"Content-Type": "application/json"}
    heartbeat(session["user"])

    pdf_file = request.files.get("pdf")
    if not pdf_file or not pdf_file.filename.lower().endswith(".pdf"):
        return _json.dumps({"error": "Please upload a valid PDF file."}), 400, {"Content-Type": "application/json"}

    try:
        count = max(5, min(25, int(request.form.get("count", 10))))
    except (ValueError, TypeError):
        count = 10
    difficulty = request.form.get("difficulty", "mixed").strip().lower()
    if difficulty not in ("easy", "mixed", "hard"):
        difficulty = "mixed"

    try:
        study_material = _extract_pdf_text(pdf_file)
    except Exception as e:
        return _json.dumps({"error": f"Could not read PDF: {str(e)}"}), 400, {"Content-Type": "application/json"}

    if not study_material or len(study_material) < 100:
        return _json.dumps({"error": "PDF appears to be empty or image-only. Please use a text-based PDF."}), 400, {"Content-Type": "application/json"}

    diff_instructions = {
        "easy":  "All questions should test straightforward recall of facts and definitions.",
        "mixed": "Mix difficulty: a blend of recall, application, and conceptual/evaluative questions.",
        "hard":  "All questions should require analysis, comparison, inference, or critical evaluation."
    }
    diff_note = diff_instructions[difficulty]

    API_KEY = os.environ["GROQ_API_KEY"]
    url     = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": "Bearer " + API_KEY, "Content-Type": "application/json"}

    system_prompt = f"""You are a professional exam paper formatter.
Read the study material provided and produce a model exam paper in plain text.

DIFFICULTY: {diff_note}

FORMAT RULES — follow exactly:
1. Start with a header block:
     ═══════════════════════════════════════
     MODEL EXAMINATION PAPER
     Subject : [infer a short subject name from the material]
     Total Questions : {count}
     Difficulty : {difficulty.capitalize()}
     Date : {_dt.now().strftime('%B %d, %Y')}
     ═══════════════════════════════════════
     INSTRUCTIONS:
     • Answer ALL questions.
     • Each question carries equal marks.
     • Select the BEST answer for each question.
     ═══════════════════════════════════════

2. Then list the questions numbered 1 to {count}:
     1. [Full question text — not just a word answer — must be a proper exam question]
        A) [option]
        B) [option]
        C) [option]
        D) [option]

     [blank line between questions]

3. After ALL questions add:
     ═══════════════════════════════════════
     ANSWER KEY
     ═══════════════════════════════════════
     1. [correct letter]) [correct option text]
     2. ...
     (continue for all questions)

MANDATORY QUESTION QUALITY RULES:
- Use a variety of question types: conceptual, application, comparison, "why/how" style.
- Do NOT produce only one-word-answer style questions. At least half must require understanding, not just recall.
- All 4 options must be specific and plausible — no "None of the above" or "All of the above".
- Questions must be based strictly on the provided material.
- Produce EXACTLY {count} questions.

Return ONLY the formatted exam paper text. No preamble, no markdown, no extra commentary."""

    user_prompt = f"Study material:\n\n{study_material}\n\nGenerate the model exam paper now."

    data = {
        "model":       "llama-3.1-8b-instant",
        "messages":    [
            {"role": "system",  "content": system_prompt},
            {"role": "user",    "content": user_prompt}
        ],
        "max_tokens":  4096,
        "temperature": 0.4,
    }

    try:
        res        = requests.post(url, headers=headers, json=data, timeout=90)
        exam_paper = res.json()["choices"][0]["message"]["content"].strip()

        if not exam_paper or len(exam_paper) < 100:
            raise ValueError("Empty exam paper returned")

        return _json.dumps({"exam_paper": exam_paper}), 200, {"Content-Type": "application/json"}

    except Exception as e:
        return _json.dumps({"error": f"Exam generation failed: {str(e)}"}), 500, {"Content-Type": "application/json"}
