# Jarvis AI


# Note 

This project is discontinued, Since having no Premium Features On several Platforms puts me in a difficult area to 
to make up a decision And I personally Can't spend Money for this project so ive decided to dis-continue. 
The Website Wouldn't taken Down it ill be still Hosted via Vercel but There won't Be new updates or fixes





A personal AI chatbot web app powered by **Groq LLaMA**, built with Flask and deployed on Vercel. Jarvis has a warm, conversational personality, supports image generation and analysis, real-time math, and a full user authentication system with a PostgreSQL backend.

 **Live Demo:** [jarvis-ai-aadin.vercel.app](https://jarvis-ai-aadin.vercel.app/)

---

## Features

- **AI Chat** — Powered by Groq's LLaMA 3.1 model. Jarvis replies conversationally, matches user energy, uses emojis naturally, and keeps responses short unless detail is asked for.
- **Image Generation** — Generate images from text prompts via Pollinations.ai (no API key needed). Supports download of generated images.
- **Image Analysis & Editing** — Upload an image and ask Jarvis to describe, analyse, or edit it. Analysis uses Groq's LLaMA 4 Scout vision model; editing uses NVIDIA's Qwen image-edit model.
- **Smart Math** — Automatically detects arithmetic expressions and evaluates them safely using AST-based parsing, saving results to calculation history.
- **Time & Date Awareness** — Jarvis knows the current IST time and date and answers naturally when asked.
- **Code Formatting** — Detects code requests and responds with proper markdown code blocks with syntax highlighting.
- **User Profiles** — Tracks user interests, message patterns, peak hours, and sentiment using keyword scoring. Every 15 messages, Groq enriches the profile with a smarter AI-generated summary.
- **User Authentication** — Sign up / log in with hashed passwords (Werkzeug). Sessions persist for 30 days.
- **Admin Dashboard** — Password-protected panel showing registered users, visit stats (last 7 days), calculation history, and user profiles.
- **Security Alerts** — Discord webhook alerts fire when a user attempts to extract secrets, claims owner identity, or uses abusive language.
- **Rate Limiting** — All sensitive routes are rate-limited to prevent brute-force attacks and API abuse.
- **Dark / Light Mode** — Full theme toggle with smooth transitions across all pages.
- **Privacy & Terms Page** — Dedicated beta terms and privacy policy page.
- **Custom 404 / 500 Pages** — Friendly error pages instead of raw Flask errors.

---

##  Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| AI / LLM | Groq API (LLaMA 3.1 8B, LLaMA 4 Scout 17B vision) |
| Image Generation | Pollinations.ai |
| Image Editing | NVIDIA API (Qwen image-edit) |
| Database | PostgreSQL via Neon (psycopg2) |
| Frontend | HTML, CSS, Vanilla JS, Marked.js |
| Rate Limiting | flask-limiter |
| Deployment | Vercel |
| Analytics | Vercel Web Analytics |
| Alerts | Discord Webhooks |

---

## Project Structure

```
Jarvis-Ai/
├── app.py              # Main Flask app — all routes and logic
├── requirements.txt    # Python dependencies
├── templates/
│   ├── landing.html    # Post-login landing page
│   ├── chat.html       # Main chat interface
│   ├── login.html      # Login page
│   ├── signup.html     # Sign up page
│   ├── privacy.html    # Beta terms & privacy policy
│   ├── quiz.html       # Quiz page
│   ├── 404.html        # Custom 404 error page
│   └── 500.html        # Custom 500 error page
└── README.md
```

---

## Environment Variables

Never commit secrets. Set these in your Vercel project settings (or a local `.env` file):

| Variable | Description |
|---|---|
| `SECRET_KEY` | Flask session secret key |
| `DATABASE_URL` | Neon PostgreSQL connection string |
| `GROQ_API_KEY` | Primary Groq API key (chat + profile) |
| `GROQ_API_KEY_2` | Secondary Groq key for vision (higher limits) |
| `GROQ_API_KEY_3` | Third Groq key for quiz/exam generation rotation |
| `NVIDIA_API_KEY` | NVIDIA API key for image editing |
| `ADMIN_PASSWORD` | Password for the `/admin` dashboard |
| `OWNER_CODE` | Secret owner verification code |
| `DISCORD_WEBHOOK` | Discord webhook URL for security alerts |
| `ENGLISH_BAD_WORDS` | Comma-separated English words to block |
| `MALAYALAM_BAD_WORDS` | Comma-separated Malayalam words to block |

---

## Running Locally

```bash
# 1. Clone the repo
git clone https://github.com/heyitsaadin/Jarvis-Ai.git
cd Jarvis-Ai

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables
export GROQ_API_KEY=your_key_here
export DATABASE_URL=your_neon_db_url
export SECRET_KEY=any_random_string
export ADMIN_PASSWORD=your_admin_password
export OWNER_CODE=your_owner_code
export DISCORD_WEBHOOK=your_webhook_url
export ENGLISH_BAD_WORDS=shit,fuck,ass
export MALAYALAM_BAD_WORDS=word1,word2

# 4. Run
python app.py
```

Then open [http://localhost:5000](http://localhost:5000)

---

##  Database

Uses **Neon PostgreSQL**. Tables are auto-created on first run via `init_db()`:

- `users` — username + hashed password
- `history` — per-user calculation history
- `visits` — timestamped page visits for analytics
- `user_profiles` — JSON-stored interest profiles, sentiment, message stats

---

## Security

This project went through a full security review before going public. Here's what was hardened:

| # | Issue | Fix Applied |
|---|---|---|
| 1 | Bad words hardcoded in source | Moved entirely to `ENGLISH_BAD_WORDS` and `MALAYALAM_BAD_WORDS` env variables — nothing sensitive in the code |
| 2 | Math used raw `eval()` | Replaced with AST-based parser — only allows actual math nodes, no code execution possible |
| 3 | No rate limiting on login/chat/signup | Added `flask-limiter` — login (15/min), signup (10/min), chat (30/min), admin (20/min) |
| 4 | Session cookie could overflow | Chat history capped at last 40 messages to keep the cookie size safe |
| 5 | Admin had no brute-force protection | Covered by the rate limiter on `/admin` (20/min) |
| 6 | Owner code used `==` comparison | Switched to `hmac.compare_digest()` — prevents timing attacks |

- Passwords hashed with Werkzeug's `generate_password_hash`
- Flask secret key randomly generated if not set via env
- All API keys and secrets loaded from environment variables only — never hardcoded
- Attempted secret extraction and owner impersonation trigger Discord alerts instantly

---

##  Built By

**Aadin KC** — [Portfolio](https://aadinkc-portfolio.vercel.app/) · [GitHub](https://github.com/heyitsaadin) · [LinkedIn](https://www.linkedin.com/in/aadin-kc-128bb3371)
