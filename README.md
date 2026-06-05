# Jarvis AI

A personal AI assistant web app powered by **Groq LLaMA**, built with Flask and deployed on Vercel. Jarvis has a warm, conversational personality and supports image generation, image analysis and editing, PDF-based quiz and exam generation, real-time math, chat sharing, and a full user authentication system with a PostgreSQL backend.

**Live Demo:** [jarvis-ai-aadin.vercel.app](https://rekai.vercel.app/)

---

## Features

- **AI Chat** — Powered by Groq's LLaMA model. Jarvis replies conversationally, matches user energy, and keeps responses natural and to the point.
- **Image Generation** — Generate images from text prompts via Pollinations.ai. Supports download of generated images. Jarvis auto-analyses each generated image for context.
- **Image Recognition** — Upload an image and ask Jarvis anything about it. Powered by Groq's LLaMA 4 Scout vision model. Supports two images at once.
- **Image Editing** — Upload an image and describe the edit. Powered by NVIDIA's Qwen image-edit model. Optionally upload a second image as a mask.
- **Quiz Generator** — Upload a PDF and Jarvis generates a full multiple-choice quiz from its content.
- **Model Exam Generator** — Same as the quiz but produces a structured exam paper with questions, options, answers, and explanations.
- **Smart Math** — Detects arithmetic expressions and evaluates them securely using AST-based parsing. Results saved to calculation history.
- **Time & Date Awareness** — Jarvis knows the current IST time and date and answers naturally when asked.
- **Code Formatting** — Detects code requests and responds with proper markdown code blocks and syntax highlighting.
- **User Profiles** — Tracks interests, message patterns, peak hours, and sentiment via keyword scoring. Every 15 messages, Groq enriches the profile with an AI-generated summary.
- **Chat Sessions** — Chats are saved, organised into sessions, and accessible from the account page. Sessions can be pinned to the top.
- **Chat Sharing** — Generate a public share link for any chat session. Accessible to anyone with the link, no login required.
- **Account Management** — Change username or password, view and delete saved chats, clear your profile, or permanently delete your account — all from the account page.
- **User Authentication** — Sign up / log in with hashed passwords. Sessions persist for 30 days.
- **Admin Dashboard** — Password-protected panel showing registered users, visit stats, active sessions, calculation history, user profiles, and shared chats. Includes a ban system (user and IP) and the ability to push notifications to any user.
- **Security Alerts** — Discord webhook alerts fire when a user attempts to extract secrets, claims owner identity, or uses abusive language.
- **Rate Limiting** — All sensitive routes are rate-limited to prevent brute-force attacks and API abuse.
- **Dark / Light Mode** — Full theme toggle with smooth transitions across all pages.
- **Privacy & Terms Page** — Dedicated privacy policy page.
- **Custom 404 / 500 Pages** — Friendly error pages instead of raw Flask errors.

---

## Tech Stack

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
├── app.py                  # Main Flask app — all routes and logic
├── requirements.txt        # Python dependencies
├── templates/
│   ├── landing.html        # Post-login landing page
│   ├── chat.html           # Main chat interface
│   ├── shared_chat.html    # Public shared chat view
│   ├── login.html          # Login page
│   ├── signup.html         # Sign up page
│   ├── privacy.html        # Privacy policy
│   ├── quiz.html           # Quiz / exam generator page
│   ├── banned.html         # Banned user page
│   ├── 404.html            # Custom 404 error page
│   └── 500.html            # Custom 500 error page
└── README.md
```

---

## Environment Variables

Never commit secrets. Set these in your Vercel project settings or a local `.env` file:

| Variable | Description |
|---|---|
| `SECRET_KEY` | Flask session secret key |
| `DATABASE_URL` | Neon PostgreSQL connection string |
| `GROQ_API_KEY` | Primary Groq API key (chat + profile) |
| `GROQ_API_KEY_2` | Secondary Groq key for vision (higher limits) |
| `GROQ_API_KEY_3` | Third Groq key for quiz/exam generation rotation |
| `NVIDIA_API_KEY` | NVIDIA API key for image editing |
| `ADMIN_PASSWORD` | Password for the admin dashboard |
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
export ENGLISH_BAD_WORDS=word1,word2
export MALAYALAM_BAD_WORDS=word1,word2

# 4. Run
python app.py
```

Then open [http://localhost:5000](http://localhost:5000)

---

## Database

Uses **Neon PostgreSQL**. Tables are auto-created on first run via `init_db()`:

- `users` — username and hashed password
- `history` — per-user calculation history
- `visits` — timestamped page visits for analytics
- `chat_sessions` — saved chat sessions with pin support
- `user_profiles` — JSON-stored interest profiles, sentiment, and message stats
- `shared_chats` — public shared chat snapshots
- `bans` — banned users and IPs

---

## Security

| # | Issue | Fix Applied |
|---|---|---|
| 1 | Bad words hardcoded in source | Moved to `ENGLISH_BAD_WORDS` and `MALAYALAM_BAD_WORDS` env variables |
| 2 | Math used raw `eval()` | Replaced with AST-based parser — only allows math nodes, no code execution |
| 3 | No rate limiting on sensitive routes | Added `flask-limiter` — login (15/min), signup (10/min), chat (30/min), admin (20/min) |
| 4 | Session cookie could overflow | Chat history capped at last 40 messages |
| 5 | Admin had no brute-force protection | Covered by rate limiter on the admin route |
| 6 | Owner code used `==` comparison | Switched to `hmac.compare_digest()` to prevent timing attacks |

- Passwords hashed with Werkzeug's `generate_password_hash`
- All API keys and secrets loaded from environment variables — never hardcoded
- Attempted secret extraction and owner impersonation trigger Discord alerts instantly

---

## Built By

**Aadin KC** — [Portfolio](https://aadinkc-portfolio.vercel.app/) · [GitHub](https://github.com/heyitsaadin) · [LinkedIn](https://www.linkedin.com/in/aadin-kc-128bb3371)
