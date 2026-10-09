# Advanced Healthcare Chatbot — Major Project

A runnable Flask + SQLite web application with a responsive healthcare-themed UI, bilingual (English/Telugu) rule-based chat responses, browser voice input, symptom urgency prompts, demo doctor directory and appointment requests, basic PDF/TXT text extraction, and admin dashboard.

## Features
- Patient registration and login; passwords hashed with Werkzeug.
- English and Telugu chat responses using a small rule-based demo engine.
- Voice input via browser Web Speech API where supported (Chrome is recommended). Voice transcription is sent only after the user presses Send.
- Symptom checker for basic urgency guidance. It does not diagnose.
- Doctor directory with seeded fictional demo profiles and appointment requests.
- Upload PDF/TXT reports; extract selectable text (scanned-PDF OCR is not included).
- Admin dashboard with counts and appointment status updates.
- SQLite database initialized automatically at first run.

## Requirements
- Python 3.10+
- pip
- A recent browser. Microphone permissions and HTTPS/localhost are usually required for speech recognition.

## Setup (Windows)
1. Extract the ZIP file.
2. Open Command Prompt/PowerShell in the extracted `advanced_healthcare_chatbot` folder.
3. Create a virtual environment:
   ```powershell
   py -m venv .venv
   .venv\Scripts\activate
   ```
4. Install dependencies:
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
5. Start the app:
   ```powershell
   python app.py
   ```
6. Open `http://127.0.0.1:5000` in your browser.

## Setup (macOS / Linux)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Then open `http://127.0.0.1:5000`.

## Demo admin login
- Email: `admin@healthcare.local`
- Password: `Admin@123`

Change the demo password before deployment. To reset the local demo database, stop the server and delete `healthcare.db`; it will be recreated at next startup.

## Database
SQLite file: `healthcare.db` (created automatically).
Tables:
- `users`: account, password hash, role
- `doctors`: seeded sample doctor profiles
- `appointments`: patient booking requests and status
- `reports`: uploaded report metadata and text summary
- `chat_logs`: user chat messages and assistant responses

Uploaded files are stored in `uploads/`.

## Project structure
```text
advanced_healthcare_chatbot/
├── app.py
├── requirements.txt
├── README.md
├── healthcare.db          # created on first run
├── uploads/               # created automatically
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── auth.html
│   ├── dashboard.html
│   ├── doctors.html
│   ├── book.html
│   ├── symptoms.html
│   ├── chat.html
│   ├── reports.html
│   └── admin.html
└── static/
    ├── style.css
    ├── app.js
    └── chat.js
```

## Important limitations / production checklist
This is a college project prototype, not a certified medical product. Chat answers are rule-based (not a connected LLM). The symptom checker is not a diagnostic model. Doctor profiles are fictional. PDF extraction handles selectable text only and does not include OCR. Voice input depends on browser capabilities and may require a network connection. Before real deployment: use a strong environment `SECRET_KEY`, CSRF protection, HTTPS, secure cookie settings, rate limiting, robust upload scanning/storage, consent and retention policies, audit logging, access controls, tested backups, and applicable privacy/health-data compliance. Do not use this prototype to make medical decisions.
