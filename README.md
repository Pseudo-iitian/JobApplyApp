# 🚀 JobApplyApp - AI Automated Job Hunter & Jira Kanban ATS

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React" />
  <img src="https://img.shields.io/badge/Vite-5.0-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite" />
  <img src="https://img.shields.io/badge/TailwindCSS-3.4-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind CSS" />
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/Groq_AI-Ultra_Fast-F55036?style=for-the-badge&logo=groq&logoColor=white" alt="Groq AI" />
  <img src="https://img.shields.io/badge/Google_Gemini-2.5%2F3.8-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="Gemini AI" />
  <img src="https://img.shields.io/badge/Database-SQLite_%7C_PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="Database" />
</p>

An intelligent, full-stack automated job application and applicant tracking system (ATS). Built with **FastAPI**, **React (Vite + Tailwind CSS)**, **SQLAlchemy**, and high-performance LLM engines (**Groq** + **Google Gemini**). 

It runs a **24/7 background scheduler** to hunt relevant jobs across LinkedIn, ATS portals, and direct HR postings, extracts recruiter contacts and application forms, tracks candidates across a **Jira-style Kanban pipeline**, computes real-time ATS match scores, tailors resumes with AI, and autofills external company job portals in **1-Click** using a Chrome Extension.

---

## 🌟 Key Features

1. **🤖 24/7 Autonomous Job Hunter Daemon**:
   - Built-in daemon (`AsyncIOScheduler`) that continuously runs multi-platform job hunting cycles.
   - Intelligent backoff and rate-limit circuit breakers (e.g., 45-second cooloff when LinkedIn hits 429).
   - Real-time updates delivered to the browser UI via **WebSockets**.

2. **⚡ Ultra-Fast 3-Tier AI Evaluation Engine**:
   - **Tier 1: Groq AI** (`openai/gpt-oss-20b` / `qwen/qwen3.8-27b`) delivering candidate match evaluations in **under 300ms** with structured JSON output.
   - **Tier 2: Google Gemini AI** (`gemini-2.5-flash`, `gemini-3.8-flash`) as seamless fallback for deep reasoning and resume tailoring.
   - **Tier 3: Built-in Heuristics**: Zero-dependency offline NLP fallback ensures you can run the system even without API keys!

3. **🌐 Wide Multi-Platform Job Coverage**:
   - **LinkedIn**: Public jobs directory (`jobs-guest`) + live Recruiter `#hiring` status posts.
   - **Direct Startup ATS Boards**: Direct Greenhouse & Lever API queries across 35+ top startups (Cred, Razorpay, Swiggy, Meesho, Groww, Zepto, Postman, etc.).
   - **Monster / Foundit**: Structured Search API integration.
   - **Instahyre**: Web search listings.
   - **Remote Developer Portals**: Remotive and Jobicy global developer feeds.
   - **DuckDuckGo Web Hunter**: Hunts direct Google Forms (`forms.gle`) and HR emails (`hr@...`, `talent@...`).

4. **📧 Direct HR Contact Extraction & Cold Email Generator**:
   - Detects direct HR and recruiter emails from postings.
   - One-click **"Copy HR Email"** and **"Draft Cold Email in Gmail"** with tailored subject and pitch.
   - Direct Google Form link detection to skip lengthy ATS application queues.

5. **📊 Pipeline Analytics & ATS Funnel Dashboard**:
   - Visual dashboard tracking total discovered jobs, high match targets (>=80%), and direct HR contact counts.
   - Conversion funnel across stages: *Discovered ➔ Applied ➔ Screening ➔ Interviewing ➔ Offer*.
   - Platform discovery source breakdown.

6. **📋 Jira-Style Kanban ATS Pipeline**:
   - Drag-and-drop or status-click job cards across 6 recruitment stages.
   - Full-text search and filters ("With HR Email", "With Google Form", Experience range).

7. **✨ 1-Click AI Resume Tailoring & ATS PDF Generation**:
   - Tailors professional summary and job experience bullet points for specific job descriptions.
   - Generates and downloads clean, ATS-friendly PDF resumes on demand (`reportlab`).

8. **🔔 Instant Multi-Channel Alerts (WebSockets, Telegram, Discord)**:
   - Live browser toast notifications via persistent WebSockets.
   - **Telegram Bot**: Instant mobile alerts on new matching job discoveries.
   - **Discord Webhook**: Post job announcements directly into your Discord channel.

9. **🧩 1-Click Form Autofill Chrome Extension & Bookmarklet**:
   - Injects a floating action button on external career portals (Workday, Naukri, LinkedIn, Greenhouse, Virtusa).
   - Automatically fills candidate profile details in under 3 seconds.

10. **🐳 Zero-Config Docker & Dual Database Architecture**:
    - Ready-to-go `docker-compose.yml` for 1-command startup.
    - Out of the box, runs locally on **SQLite** with zero setup.
    - Production-ready for **PostgreSQL** / **AWS RDS** via a single `.env` variable.

---

## 🏗️ Project Architecture

```
JobApplyApp/
├── backend/
│   ├── app/
│   │   ├── config.py              # Settings with Pydantic & .env loading
│   │   ├── database.py            # SQLite & PostgreSQL engine configuration
│   │   ├── models/                # SQLAlchemy models (Job, Resume, Notification)
│   │   ├── schemas/               # Pydantic validation schemas
│   │   ├── services/
│   │   │   ├── scraper.py         # Multi-platform async scraper & circuit breakers
│   │   │   ├── llm_service.py     # Groq & Gemini 3-tier AI evaluation engine
│   │   │   ├── scheduler.py       # 24/7 background job hunter daemon
│   │   │   ├── notifier.py        # WebSockets, Telegram & Discord notifications
│   │   │   ├── pdf_generator.py   # ATS PDF resume generator
│   │   │   ├── resume_parser.py   # PDF text extraction & skill parser
│   │   │   └── auto_apply_agent.py# Candidate profile & autofill engine
│   │   ├── routers/               # FastAPI REST endpoints & WebSocket handlers
│   │   └── main.py                # FastAPI lifecycle, CORS & startup
│   ├── uploads/                   # Uploaded candidate resumes (gitignored)
│   ├── static/screenshots/        # Scraper screenshots (gitignored)
│   ├── requirements.txt           # Python backend dependencies
│   ├── Dockerfile                 # Backend container definition
│   └── .env.example               # Backend environment template
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.jsx         # Live status, search trigger & navigation
│   │   │   ├── KanbanBoard.jsx    # Jira-style Kanban board
│   │   │   ├── JobCard.jsx        # Job card with match score & quick actions
│   │   │   ├── TailorModal.jsx    # AI resume tailoring & PDF download modal
│   │   │   ├── AnalyticsModal.jsx # ATS funnel & pipeline metrics dashboard
│   │   │   ├── HunterLogsModal.jsx# Live daemon terminal & inspection logs
│   │   │   ├── AutoApplyModal.jsx # Autofill profile & extension setup modal
│   │   │   └── NotificationDropdown.jsx # Real-time alerts center
│   │   ├── api.js                 # API & WebSocket client
│   │   ├── App.jsx                # Main application entry
│   │   └── index.css              # Tailwind CSS styles
│   ├── Dockerfile                 # Multi-stage frontend container
│   ├── nginx.conf                 # Nginx reverse proxy configuration
│   └── package.json               # Frontend dependencies
├── extension/                     # Chrome Extension (Manifest V3)
│   ├── manifest.json              # Extension manifest
│   ├── content.js                 # 1-Click floating autofill engine
│   ├── content.css                # Floating widget styles
│   └── popup.html                 # Extension popup interface
├── docker-compose.yml             # 1-Command container orchestration
├── .env.example                   # Root environment configuration template
├── .gitignore                     # Git ignore rules protecting credentials
├── start.sh                       # 1-Click startup script (Backend + Frontend)
├── run_backend.sh                 # Run backend standalone
└── run_frontend.sh                # Run frontend standalone
```

---

## ⚡ Quick Start Options

### Option 1: Docker Compose (Fastest & Containerized)

Ensure you have [Docker](https://docs.docker.com/get-docker/) installed, then run:

```bash
# 1. Clone the repository
git clone <YOUR_GITHUB_REPO_URL>
cd JobApplyApp

# 2. Copy the sample environment file
cp .env.example .env

# 3. Start both backend and frontend containers
docker compose up --build
```

- **Web UI**: [http://localhost:5173](http://localhost:5173)
- **FastAPI Backend**: [http://localhost:8000](http://localhost:8000)
- **Interactive API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Option 2: 1-Click Local Script

If running locally on Linux / macOS:

```bash
# 1. Clone the repository
git clone <YOUR_GITHUB_REPO_URL>
cd JobApplyApp

# 2. Copy the sample environment file
cp .env.example .env

# 3. Make scripts executable and launch
chmod +x start.sh run_backend.sh run_frontend.sh
./start.sh
```

`./start.sh` automatically creates the Python virtual environment, installs backend and frontend packages, and launches both services simultaneously.

---

### Option 3: Manual Step-by-Step Setup

#### Terminal 1: Backend Setup
```bash
cd backend

# Create and activate Python virtual environment
python3 -m venv venv
source venv/bin/activate       # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Terminal 2: Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```

---

## ⚙️ Environment Configuration (`.env`)

Copy `.env.example` to `.env` and configure your preferences:

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `DATABASE_URL` | Database connection string. SQLite (zero setup) or PostgreSQL. | `sqlite:///./jobapply.db` |
| `GROQ_API_KEY` | *(Recommended)* Groq API Key for ultra-fast candidate scoring (<300ms). | Get free key at [console.groq.com](https://console.groq.com/) |
| `GEMINI_API_KEY` | *(Optional)* Google Gemini API Key for deep resume tailoring. | Get free key at [Google AI Studio](https://aistudio.google.com/) |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token for instant mobile job notifications. | *(Optional)* From [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_CHAT_ID` | Telegram chat ID to receive job alerts. | *(Optional)* From [@userinfobot](https://t.me/userinfobot) |
| `DISCORD_WEBHOOK_URL`| Discord webhook URL for channel announcements. | *(Optional)* Discord Webhook URL |
| `SCRAPE_INTERVAL_MINUTES` | Frequency (in minutes) for the 24/7 background job hunter. | `5` |
| `DEFAULT_KEYWORDS` | Target job titles and skills to search for. | `Spring Boot, Java Developer, Microservices` |
| `DEFAULT_EXPERIENCE` | Target candidate years of experience. | `2.0` |
| `DEFAULT_LOCATION` | Preferred job locations / Remote. | `All India, Remote, Noida, Bangalore, Pune` |

### Using PostgreSQL / AWS RDS:
To connect to an external PostgreSQL database (AWS RDS, Supabase, Neon):
```env
DATABASE_URL=postgresql://<DB_USER>:<DB_PASSWORD>@<DB_HOST>:5432/<DB_NAME>?sslmode=require
```

---

## 🧩 Installing the 1-Click Form Autofill Chrome Extension

1. Open **Google Chrome** and navigate to:
   ```text
   chrome://extensions
   ```
2. Enable the **"Developer mode"** toggle in the top-right corner.
3. Click the **"Load unpacked"** button in the top-left corner.
4. Select the `extension/` folder inside this repository:
   ```text
   JobApplyApp/extension
   ```
5. Navigate to any career portal (e.g. Workday, Naukri, LinkedIn, Greenhouse, Virtusa). A floating **⚡ round button** will appear on the bottom-right, allowing you to fill candidate details in 1 click!

---

## 🔒 Security & Credentials (Pushing to GitHub Safely)

This repository includes a strict `.gitignore` that guarantees secrets, local database records, and personal resumes are never committed:

### Protected Files:
- ❌ `.env` and `backend/.env` are **NEVER** tracked by Git.
- ❌ Database files (`jobapply.db`, `backend/jobapply.db`, `*.sqlite3`) are **NEVER** pushed.
- ❌ Uploaded candidate resumes (`backend/uploads/*.pdf`) are **NEVER** pushed.
- ❌ Screenshots and temporary cache folders are **NEVER** pushed.

### Git Push Commands:
```bash
# 1. Check status (verify no secrets are staged)
git status

# 2. Stage safe files
git add .

# 3. Commit
git commit -m "feat: AI Job Hunter with Groq inference, Jira Kanban ATS, and Docker support"

# 4. Push to your GitHub repository
git branch -M main
git remote add origin https://github.com/<YOUR-USERNAME>/<YOUR-REPO-NAME>.git
git push -u origin main
```

---

## 📡 REST API Documentation

When the backend is running, explore interactive endpoints at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Key Endpoints:
- `GET /api/jobs` - Retrieve all tracked jobs sorted with newest on top.
- `GET /api/jobs/analytics` - Pipeline ATS funnel metrics, match score averages, and platform distribution.
- `GET /api/jobs/hunter-status` - Live 24/7 scheduler daemon status and scraper logs.
- `POST /api/jobs/trigger-search` - Trigger an immediate job hunt cycle.
- `PATCH /api/jobs/{id}/status` - Move job across Kanban stages.
- `POST /api/jobs/{id}/tailor-resume` - AI ATS score, missing keywords, and tailored bullet points.
- `GET /api/jobs/{id}/download-tailored-resume` - Download tailored PDF resume.
- `WS /api/notifications/ws` - Real-time WebSocket connection for live job alerts.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1. Fork the project.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
