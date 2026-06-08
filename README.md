# Jarvis AI

A personal AI assistant web app powered by **Groq LLaMA**, built with Flask and deployed on Vercel. Jarvis has a warm, conversational personality and supports image generation, image analysis and editing, PDF-based quiz and exam generation, real-time math, chat sharing, and a full user authentication system with a PostgreSQL backend.

**Live Demo:** [jarvis-ai-aadin.vercel.app](https://jarvis-ai-aadin.vercel.app/)

---

## 🚀 Features

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

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python, Flask |
| **AI / LLM** | Groq API (LLaMA 3.1 8B, LLaMA 4 Scout 17B vision) |
| **Image Generation** | Pollinations.ai, HuggingFace, Together AI |
| **Image Editing** | NVIDIA API (Qwen image-edit) |
| **Database** | PostgreSQL via Neon (psycopg2) |
| **Frontend** | HTML, CSS, Vanilla JS, Marked.js |
| **Rate Limiting** | flask-limiter |
| **Deployment** | Vercel |
| **Analytics** | Vercel Web Analytics |
| **Alerts** | Discord Webhooks |

---

## 📂 Project Structure

```text
Jarvis-ai/
├── app/                    # Main application package
│   ├── routes/             # Route handlers (Blueprints)
│   ├── services/           # Business logic and external API integrations
│   ├── utils/              # Helper functions and utilities
│   ├── static/             # Static assets (JS, CSS, Images)
│   ├── templates/          # HTML templates
│   ├── __init__.py         # App factory and initialization
│   └── models.py           # Database models and schema
├── .env.example            # Template for environment variables
├── .gitignore              # Files to exclude from Git
├── app.py                  # Legacy entry point (kept for Vercel compatibility)
├── run.py                  # Local development entry point
├── requirements.txt        # Python dependencies
├── vercel.json             # Vercel deployment configuration
└── README.md               # Project documentation
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.8+
- PostgreSQL database (e.g., Neon.tech)
- API keys for Groq, NVIDIA, etc.

### Installation
1. **Clone the repo**
   ```bash
   git clone https://github.com/heyitsaadin/Jarvis-ai.git
   cd Jarvis-ai
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   Copy `.env.example` to `.env` and fill in your details:
   ```bash
   cp .env.example .env
   ```

4. **Run Locally**
   ```bash
   python run.py
   ```
   Open [http://localhost:5000](http://localhost:5000) in your browser.

---

## 🛡 Security Features

- **AST-based Math Parsing**: Securely evaluates math expressions without using `eval()`.
- **Rate Limiting**: Protects sensitive routes from brute-force and abuse.
- **Password Hashing**: Secure storage of user credentials using Werkzeug.
- **Timing Attack Protection**: Uses `hmac.compare_digest()` for secret comparisons.
- **Content Filtering**: Configurable bad words filter via environment variables.

---

## 📄 License

This project is for educational purposes.

---

## 👨‍💻 Built By

**Aadin KC** — [Portfolio](https://aadinkc-portfolio.vercel.app/) · [GitHub](https://github.com/heyitsaadin) · [LinkedIn](https://www.linkedin.com/in/aadin-kc-128bb3371)
