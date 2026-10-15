# 🚀 JobApplyApp - AI Automated Job Hunter & Jira Kanban ATS

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React" />
  <img src="https://img.shields.io/badge/Vite-5.0-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite" />
  <img src="https://img.shields.io/badge/TailwindCSS-3.4-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind CSS" />
  <img src="https://img.shields.io/badge/Google_Gemini_AI-2.5%2F3.8-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="Gemini AI" />
  <img src="https://img.shields.io/badge/SQLite_%7C_PostgreSQL-Supported-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="Database" />
</p>

An intelligent, full-stack automated job application and applicant tracking system (ATS). Built with **FastAPI**, **React (Vite + Tailwind CSS)**, **SQLAlchemy**, and **Google Gemini AI**. 

It runs a **24/7 background scheduler** to hunt relevant jobs, extracts recruiter contacts and application forms, tracks candidates across a **Jira-style Kanban pipeline**, tailors resumes with AI, and autofills external company job portals in **1-Click** using a custom Chrome Extension.

---

## 🌟 Key Features

1. **🤖 24/7 Background Autonomous Job Hunter**:
   - Built-in daemon (`AsyncIOScheduler`) that periodically scrapes job feeds across the web.
   - Configurable hunting intervals (default: every 5 minutes).
   - Real-time updates delivered to the browser UI via **WebSockets**.

2. **🎯 Strict Experience Matching Filter**:
   - Tuned to hunt targeted roles (e.g., **2 Years Experience** Java Developer, Spring Boot, Microservices).
   - Intelligently skips irrelevant senior (5+, 7+, 10+ years) positions to save candidate time.

3. **📧 HR Email & Google Forms Extraction**:
   - Automatically parses job descriptions to detect HR/recruiter emails (`hr@...`, `careers@...`, `talent@...`).
   - Detects Google Form links (`forms.gle/...`, `docs.google.com/forms/...`).
   - One-click "Copy HR Email" and "Draft Cold Email in Gmail" with tailored subject & body.

4. **📋 Jira-Style Kanban ATS Pipeline**:
   - Visual stages:
     - 📥 **Discovered / New** (Freshly scraped jobs arrive here automatically)
     - 📝 **Applied**
     - 📞 **HR Screening**
     - 💻 **Tech Interview**
     - 🎉 **Offer Received**
     - ❌ **Archived / Rejected**
   - Quick filters: Search by keyword/company, "Only with HR Email", "Only with Google Form".

5. **✨ AI-Powered Resume Tailoring (Google Gemini AI)**:
   - Calculates ATS Match Score (70% - 98%).
   - Identifies missing keywords from the job description.
   - Rewrites tailored professional summary and targeted experience bullet points.
   - Generates personalized cover letters and cold outreach email drafts.
   - *Intelligent fallback*: Even without an API key, built-in heuristic algorithms ensure full functionality.

6. **🧩 1-Click Form Autofill Chrome Extension & Bookmarklet**:
   - Works on popular career portals (Workday, Naukri, LinkedIn, Greenhouse, Virtusa, etc.).
   - Injects a floating action button on any job application page.
   - Fills personal details, experience, CTC, notice period, and answers in 1 click.

7. **💾 Dual Database Support (Zero-Config SQLite & AWS RDS PostgreSQL)**:
   - Out of the box, runs immediately on local **SQLite** (`jobapply.db`) with zero setup.
   - Production-ready for **PostgreSQL** / **AWS RDS** simply by configuring `.env`.

---

## 🏗️ Project Architecture

```
JobApplyApp/
├── backend/
│   ├── app/
│   │   ├── config.py              # Configuration & Pydantic settings
│   │   ├── database.py            # PostgreSQL & SQLite engine configuration
│   │   ├── models/                # SQLAlchemy database models
│   │   ├── schemas/               # Pydantic validation schemas
│   │   ├── services/
│   │   │   ├── scraper.py         # Multi-source scraper & contact extractor
│   │   │   ├── llm_service.py     # Gemini AI & heuristic fallback engine
│   │   │   ├── scheduler.py       # 24/7 background job hunter
│   │   │   ├── notifier.py        # WebSockets real-time manager
│   │   │   ├── resume_parser.py   # PDF text extraction & skill parser
│   │   │   └── auto_apply_agent.py# Autonomous application engine
│   │   ├── routers/               # FastAPI REST endpoints & WebSocket routes
│   │   └── main.py                # FastAPI lifecycle, CORS & startup
│   ├── uploads/                   # Uploaded candidate resumes (gitignored)
│   ├── static/screenshots/        # Scraper screenshots (gitignored)
│   ├── requirements.txt           # Python backend dependencies
│   └── .env.example               # Backend environment template
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.jsx         # Live hunter status & quick actions
│   │   │   ├── KanbanBoard.jsx    # Jira-style Kanban board
│   │   │   ├── JobCard.jsx        # Job ticket card with contacts & actions
│   │   │   ├── TailorModal.jsx    # AI ATS score & resume tailoring modal
│   │   │   ├── AutoApplyModal.jsx # Autofill profile & extension setup modal
│   │   │   └── NotificationDropdown.jsx # Real-time alerts center
│   │   ├── api.js                 # Axios API & WebSocket client
│   │   ├── App.jsx                # Main application entry
│   │   └── index.css              # Tailwind CSS styles
│   └── package.json               # Frontend dependencies
├── extension/                     # Chrome Extension (Manifest V3)
│   ├── manifest.json              # Extension manifest
│   ├── content.js                 # 1-Click floating autofill engine
│   ├── content.css                # Floating widget styles
│   ├── background.js              # Service worker
│   └── popup.html                 # Extension popup interface
├── .env.example                   # Root environment configuration template
├── .gitignore                     # Git ignore rules protecting credentials
├── start.sh                       # 1-Click startup script (Backend + Frontend)
├── run_backend.sh                 # Run backend standalone
└── run_frontend.sh                # Run frontend standalone
```

---

## 📋 Prerequisites

Before running the application, ensure you have the following installed on your machine:

- **Python**: `3.10` or higher
- **Node.js**: `18.0` or higher (with `npm`)
- **Git**
- **Google Chrome** (Optional, for using the 1-Click Autofill Extension)

---

## ⚡ Quick Start (Recommended)

The easiest way to get everything running locally:

### 1. Clone the repository
```bash
git clone <YOUR_GITHUB_REPO_URL>
cd JobApplyApp
```

### 2. Create your `.env` configuration
Copy the sample environment file:
```bash
cp .env.example .env
```
*(By default, SQLite is preconfigured, so you don't need to change anything to test it immediately!)*

### 3. Launch with 1-Click Script
```bash
chmod +x start.sh run_backend.sh run_frontend.sh
./start.sh
```
`./start.sh` will automatically:
- Create a Python virtual environment (`backend/venv`) if missing.
- Install all backend requirements (`pip install -r requirements.txt`).
- Install all frontend dependencies (`npm install`) if missing.
- Launch the **FastAPI backend** on `http://localhost:8000`.
- Launch the **React frontend** on `http://localhost:5173`.
- Start the **24/7 background job hunter**.

---

## 🛠️ Manual Step-by-Step Setup

If you prefer running Backend and Frontend in separate terminal windows:

### Terminal 1: Backend Setup
```bash
# 1. Navigate to backend directory
cd backend

# 2. Create and activate a Python virtual environment
python3 -m venv venv
source venv/bin/activate       # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Set up your .env file
cp .env.example .env

# 5. Start the FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- **Backend API**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **Alternative ReDoc**: `http://localhost:8000/redoc`

---

### Terminal 2: Frontend Setup
```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install Node dependencies
npm install

# 3. Start Vite development server
npm run dev
```
- **Web UI**: `http://localhost:5173`

---

## ⚙️ Environment Configuration (`.env`)

Configure your settings in `.env` (in the project root or in `backend/.env`):

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `DATABASE_URL` | Database connection string. Use SQLite for zero-setup, or PostgreSQL for production. | `sqlite:///./jobapply.db` |
| `GEMINI_API_KEY` | Google Gemini API Key for ATS matching & AI tailoring. | *(Optional)* Get free key at [Google AI Studio](https://aistudio.google.com/) |
| `GEMINI_MODEL_CANDIDATES` | Comma-separated list of Gemini models for rate-limit failover. | `gemini-3.8-flash,gemini-2.5-flash` |
| `SCRAPE_INTERVAL_MINUTES` | Frequency (in minutes) for the 24/7 background job hunter. | `5` |
| `DEFAULT_KEYWORDS` | Target job titles and skills to search for. | `Spring Boot, Java Developer, Microservices` |
| `DEFAULT_EXPERIENCE` | Target candidate years of experience. | `2.0` |
| `DEFAULT_LOCATION` | Preferred job locations / Remote. | `All India, Remote, Noida, Bangalore, Pune` |

### Using PostgreSQL / AWS RDS:
To connect to an external PostgreSQL database (such as AWS RDS, Supabase, or Neon):
```env
DATABASE_URL=postgresql://<DB_USER>:<DB_PASSWORD>@<DB_HOST>:5432/<DB_NAME>?sslmode=require
```

---

## 🧩 Installing the 1-Click Form Autofill Chrome Extension

The application comes with a Chrome Extension that automatically recognizes job application forms and fills them with your candidate profile:

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

This repository includes a strict `.gitignore` that prevents sensitive information from being pushed to GitHub:

### Protected Files:
- ❌ `.env` and all secret files (`*.env`, `backend/.env`) are **NEVER** tracked by Git.
- ❌ Database files (`jobapply.db`, `backend/jobapply.db`, `*.sqlite3`) are **NEVER** pushed.
- ❌ Uploaded candidate resumes (`backend/uploads/*.pdf`) are **NEVER** pushed.
- ❌ Automated screenshots (`backend/static/screenshots/*.png`) are **NEVER** pushed.
- ❌ `venv/` and `node_modules/` folders are **NEVER** pushed.

### How to Safely Push to GitHub:

1. **Initialize Git (if not already done):**
   ```bash
   git init
   ```

2. **Verify that secrets are ignored:**
   ```bash
   git status
   ```
   > 🔍 **Check:** Ensure `.env`, `jobapply.db`, and `uploads/` are **NOT** listed in `Untracked files`!

3. **Stage all safe files:**
   ```bash
   git add .
   ```

4. **Verify staged files:**
   ```bash
   git status
   ```

5. **Commit and Push:**
   ```bash
   git commit -m "Initial commit: JobApplyApp AI Hunter & Kanban ATS"
   git branch -M main
   git remote add origin https://github.com/<YOUR-USERNAME>/<YOUR-REPO-NAME>.git
   git push -u origin main
   ```

---

## 📡 REST API Documentation

Once the backend is running, explore all interactive endpoints at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Key Endpoints:
- `GET /api/jobs` - Retrieve all tracked jobs with filters (search, stage, contacts).
- `PATCH /api/jobs/{id}/stage` - Move a job across Kanban stages.
- `POST /api/jobs/{id}/tailor` - Generate Gemini ATS resume match, score, and cold email draft.
- `GET /api/jobs/{id}/download-tailored-resume` - Download an ATS-optimized PDF resume.
- `POST /api/scrape/trigger` - Manually trigger an immediate job hunt cycle.
- `GET /api/notifications` - Retrieve background hunter alerts.
- `WS /api/notifications/ws` - Real-time WebSocket connection for live job updates.
- `GET /api/auto-apply/profile` - View candidate autofill profile details.

---

## ❓ Troubleshooting & FAQs

### 1. `uvicorn: command not found`
Activate your virtual environment first:
```bash
source backend/venv/bin/activate
```

### 2. Port `8000` or `5173` is already in use
Kill any existing processes on those ports:
```bash
# On Linux / macOS:
lsof -ti :8000 | xargs kill -9 2>/dev/null
lsof -ti :5173 | xargs kill -9 2>/dev/null
```

### 3. What if I don't have a Gemini API Key?
No problem! The application includes an intelligent **heuristic fallback engine**. Even without an API key, the ATS score, resume keyword extraction, bullet point generator, and cold email builder will work out of the box.

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).
