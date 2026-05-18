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
import re
import time
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

# ── Groq helper: try keys in rotation, batch if needed ──
def _groq_call(system_prompt, user_prompt, max_tokens=4096, temperature=0.5):
    """Call Groq API, rotating through available API keys. Returns raw content string."""
    keys = [os.environ.get("GROQ_API_KEY","")]
    key2 = os.environ.get("GROQ_API_KEY_2","")
    if key2:
        keys.append(key2)
    keys = [k for k in keys if k]
    if not keys:
        raise ValueError("No GROQ_API_KEY configured")

    url  = "https://api.groq.com/openai/v1/chat/completions"
    # Try models in order — larger models handle more tokens
    models = ["llama-3.3-70b-versatile", "llama3-70b-8192", "llama-3.1-8b-instant"]
    data = {
        "messages":    [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt}
        ],
        "max_tokens":  max_tokens,
        "temperature": temperature,
    }

    last_err = "Unknown error"
    for ki, key in enumerate(keys):
        headers = {"Authorization": "Bearer " + key, "Content-Type": "application/json"}
        for model in models:
            data["model"] = model
            try:
                res = requests.post(url, headers=headers, json=data, timeout=90)
                rj  = res.json()
                if "choices" in rj:
                    return rj["choices"][0]["message"]["content"].strip()
                err = rj.get("error", {})
                last_err = err.get("message", str(rj))
                # Rate limit on this key — try next key immediately
                if err.get("code") in ("rate_limit_exceeded", "tokens_exceeded"):
                    break
            except Exception as ex:
                last_err = str(ex)
    raise ValueError(last_err)


def _parse_json_response(raw):
    """Strip markdown fences and parse JSON."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z]*\n?", "", raw)
        raw = raw.rstrip("`").strip()
    return _json.loads(raw)


@app.route("/generate_quiz", methods=["POST"])
def generate_quiz():
    """
    Accepts: PDF upload + count + difficulty.
    Returns: { "questions": [ ... ] }  or  { "error": "..." }
    Each question: { question, options (4 strings), answer, explanation }
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
        "easy":  "All questions should be straightforward recall questions testing basic facts and definitions. Keep language simple.",
        "mixed": "Mix difficulty: one-third easy recall, one-third application/analysis, one-third deeper conceptual questions.",
        "hard":  "All questions should require analysis, comparison, inference, or critical evaluation. Avoid simple recall."
    }
    diff_note = diff_instructions[difficulty]

    # Batch into chunks of 10 to avoid token limits
    BATCH = 10
    all_questions = []
    batches = []
    remaining = count
    batch_num = 1
    while remaining > 0:
        b = min(BATCH, remaining)
        batches.append((batch_num, b))
        remaining -= b
        batch_num += 1

    for bn, b_count in batches:
        system_prompt = f"""You are an expert academic exam question writer.
Return EXACTLY {b_count} multiple-choice questions as a raw JSON array.
DIFFICULTY: {diff_note}
RULES:
1. Return ONLY a valid JSON array. No preamble, no markdown fences.
2. Each element: {{"question":"...","options":["A","B","C","D"],"answer":"exact option string","explanation":"2-3 sentences"}}
3. Questions must come from the study material only.
4. Vary question types: recall, conceptual, comparison, application, why/how.
5. All 4 options must be specific and plausible. No "None/All of the above".
6. Return exactly {b_count} questions."""

        # Add context about previous batch to avoid repeats
        avoid_note = ""
        if all_questions:
            prev_qs = "; ".join(q["question"][:60] for q in all_questions[-5:])
            avoid_note = f"\nDo NOT repeat these questions already generated: {prev_qs}"

        user_prompt = f"Study material:\n\n{study_material}\n\nGenerate {b_count} MCQ questions now.{avoid_note}"

        try:
            raw = _groq_call(system_prompt, user_prompt, max_tokens=min(4096, 300 + b_count * 380), temperature=0.5)
            batch_qs = _parse_json_response(raw)
            if isinstance(batch_qs, list):
                all_questions.extend(batch_qs)
        except Exception as e:
            if not all_questions:
                return _json.dumps({"error": f"Quiz generation failed: {str(e)}"}), 500, {"Content-Type": "application/json"}
            break  # partial success — return what we have

    if not all_questions:
        return _json.dumps({"error": "No questions could be generated. Please try again."}), 500, {"Content-Type": "application/json"}

    return _json.dumps({"questions": all_questions[:count]}), 200, {"Content-Type": "application/json"}


# ──────────────────────────────────────────────
# GENERATE MODEL EXAM PAPER FROM PDF
# ──────────────────────────────────────────────

@app.route("/generate_exam", methods=["POST"])
def generate_exam():
    """
    Returns: { "exam": {subject, difficulty, date, questions:[...]}, "exam_paper": "plain text" }
    Uses batching + key rotation so 5-20 questions always work.
    """
    if "user" not in session:
        return _json.dumps({"error": "not_logged_in"}), 401, {"Content-Type": "application/json"}
    heartbeat(session["user"])

    pdf_file = request.files.get("pdf")
    if not pdf_file or not pdf_file.filename.lower().endswith(".pdf"):
        return _json.dumps({"error": "Please upload a valid PDF file."}), 400, {"Content-Type": "application/json"}

    try:
        count = max(5, min(20, int(request.form.get("count", 10))))
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
        "easy":  "Straightforward recall questions testing basic facts and definitions.",
        "mixed": "Mix: one-third recall, one-third application, one-third conceptual/evaluative.",
        "hard":  "All questions require analysis, comparison, inference, or critical evaluation."
    }
    diff_note = diff_instructions[difficulty]

    # First call: get subject + first batch of questions
    BATCH = 10
    all_questions = []
    subject = "Examination"

    # Build batches
    batches = []
    remaining = count
    while remaining > 0:
        b = min(BATCH, remaining)
        batches.append(b)
        remaining -= b

    for bi, b_count in enumerate(batches):
        is_first = (bi == 0)

        if is_first:
            system_prompt = f"""You are an expert exam question writer.
Return a JSON object with this EXACT structure:
{{"subject":"<inferred subject>","questions":[{{"question":"...","options":["A","B","C","D"],"answer":"exact option","explanation":"2-3 sentences"}}]}}

DIFFICULTY: {diff_note}
RULES:
1. Return ONLY valid JSON. No markdown. No extra text.
2. Infer subject from the material (e.g. "Computer Science", "Biology").
3. Generate EXACTLY {b_count} questions.
4. Each option must be a full sentence/phrase, specific and plausible.
5. "answer" must be the EXACT string from options array.
6. Vary question types: recall, conceptual, comparison, application, why/how."""
        else:
            prev_qs = "; ".join(q["question"][:50] for q in all_questions[-5:])
            system_prompt = f"""You are an expert exam question writer.
Return a JSON ARRAY of EXACTLY {b_count} more multiple-choice questions.
DIFFICULTY: {diff_note}
Format: [{{"question":"...","options":["A","B","C","D"],"answer":"exact option","explanation":"2-3 sentences"}}]
RULES: Return ONLY a JSON array. No markdown. Do NOT repeat: {prev_qs}
Vary question types. All options specific and plausible."""

        user_prompt = f"Study material:\n\n{study_material}\n\nGenerate {'the exam questions' if is_first else f'{b_count} more questions'} now."

        try:
            raw = _groq_call(system_prompt, user_prompt, max_tokens=min(4096, 400 + b_count * 380), temperature=0.4)
            parsed = _parse_json_response(raw)

            if is_first and isinstance(parsed, dict):
                subject = parsed.get("subject", "Examination")
                qs = parsed.get("questions", [])
                if isinstance(qs, list):
                    all_questions.extend(qs)
            elif isinstance(parsed, list):
                all_questions.extend(parsed)
            elif isinstance(parsed, dict) and "questions" in parsed:
                all_questions.extend(parsed["questions"])

        except Exception as e:
            if not all_questions:
                return _json.dumps({"error": f"Exam generation failed: {str(e)}"}), 500, {"Content-Type": "application/json"}
            break  # partial success — return what we have

    if not all_questions:
        return _json.dumps({"error": "No questions could be generated. Please try again."}), 500, {"Content-Type": "application/json"}

    questions_list = all_questions[:count]
    today = _dt.now().strftime("%B %d, %Y")

    exam_obj = {
        "subject":    subject,
        "difficulty": difficulty.capitalize(),
        "date":       today,
        "questions":  questions_list
    }

    # Build plain-text download version
    txt  = "MODEL EXAMINATION PAPER\n"
    txt += f"Subject: {subject}\n"
    txt += f"Difficulty: {difficulty.capitalize()}\n"
    txt += f"Date: {today}\n\n"
    txt += "INSTRUCTIONS:\n"
    txt += "- Answer ALL questions.\n"
    txt += "- Each question carries equal marks.\n"
    txt += "- Select the BEST answer.\n\n"
    for i, q in enumerate(questions_list):
        txt += f"{i+1}. {q.get('question','')}\n"
        for j, opt in enumerate(q.get('options', [])):
            txt += f"   {'ABCD'[j]}) {opt}\n"
        txt += "\n"
    txt += "ANSWER KEY\n"
    for i, q in enumerate(questions_list):
        opts = q.get('options', [])
        ans  = q.get('answer', '')
        li   = 'ABCD'[opts.index(ans)] if ans in opts else '?'
        txt += f"{i+1}. {li}) {ans}\n"

    return _json.dumps({"exam": exam_obj, "exam_paper": txt}), 200, {"Content-Type": "application/json"}
