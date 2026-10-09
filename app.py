import os, sqlite3, re
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "healthcare.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_EXTENSIONS = {"txt", "pdf"}
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-development-secret")
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'patient', created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS doctors(
      id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, specialty TEXT NOT NULL,
      location TEXT NOT NULL DEFAULT 'Online', fee INTEGER NOT NULL DEFAULT 500,
      available TEXT NOT NULL DEFAULT 'Mon-Fri'
    );
    CREATE TABLE IF NOT EXISTS appointments(
      id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, doctor_id INTEGER NOT NULL,
      appointment_date TEXT NOT NULL, reason TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Pending',
      created_at TEXT NOT NULL, FOREIGN KEY(user_id) REFERENCES users(id),
      FOREIGN KEY(doctor_id) REFERENCES doctors(id)
    );
    CREATE TABLE IF NOT EXISTS reports(
      id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, filename TEXT NOT NULL,
      summary TEXT NOT NULL, created_at TEXT NOT NULL, FOREIGN KEY(user_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS chat_logs(
      id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, message TEXT NOT NULL,
      response TEXT NOT NULL, language TEXT NOT NULL DEFAULT 'en', created_at TEXT NOT NULL
    );
    """)
    if conn.execute("SELECT COUNT(*) FROM users WHERE role='admin'").fetchone()[0] == 0:
        conn.execute("INSERT INTO users(name,email,password_hash,role,created_at) VALUES(?,?,?,?,?)",
                     ("Administrator", "admin@healthcare.local", generate_password_hash("Admin@123"), "admin", datetime.now().isoformat(timespec="seconds")))
    if conn.execute("SELECT COUNT(*) FROM doctors").fetchone()[0] == 0:
        conn.executemany("INSERT INTO doctors(name,specialty,location,fee,available) VALUES(?,?,?,?,?)", [
            ("Dr. Ananya Rao", "General Physician", "City Health Clinic", 500, "Mon-Fri"),
            ("Dr. Kiran Kumar", "Dermatology", "Care Plus Centre", 700, "Tue-Sat"),
            ("Dr. Meera Shah", "Cardiology", "HeartWell Hospital", 900, "Mon-Sat"),
            ("Dr. Arjun Reddy", "Pediatrics", "Family Medical Centre", 600, "Mon-Fri"),
            ("Dr. Priya Nair", "Neurology", "NeuroCare Clinic", 850, "Wed-Sun")
        ])
    conn.commit()
    conn.close()

def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapped

def admin_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            flash("Administrator access required.", "danger")
            return redirect(url_for("dashboard"))
        return fn(*args, **kwargs)
    return wrapped

def now():
    return datetime.now().isoformat(timespec="seconds")

def assistant_reply(message, lang="en"):
    m = message.lower()
    emergency = ["chest pain", "can't breathe", "cannot breathe", "difficulty breathing", "unconscious", "severe bleeding", "stroke", "ఛాతి నొప్పి", "శ్వాస తీసుకోలేక"]
    if any(term in m for term in emergency):
        return ("మీకు అత్యవసర లక్షణాలు ఉంటే వెంటనే స్థానిక అత్యవసర సేవలకు కాల్ చేయండి లేదా సమీప అత్యవసర విభాగానికి వెళ్లండి. Chatbot సమాధానం కోసం వేచి ఉండకండి."
                if lang == "te" else
                "This may be an emergency. Contact your local emergency number or go to the nearest emergency department now. Do not wait for a chatbot response.")
    if lang == "te":
        if any(x in m for x in ["జ్వరం", "fever", "తలనొప్పి", "headache", "దగ్గు", "cough"]):
            return "మీ లక్షణాల గురించి విన్నాను. విశ్రాంతి తీసుకోండి, ద్రవాలు తాగండి, లక్షణాల తీవ్రతను గమనించండి. ఇవి నిర్ధారణ లేదా వ్యక్తిగత వైద్య సలహా కావు. లక్షణాలు తీవ్రమైతే లేదా కొనసాగితే వైద్యుడిని సంప్రదించండి."
        return "నేను ఆరోగ్య సమాచార సహాయకుడిని. మీ ప్రశ్నకు సాధారణ సమాచారం అందించగలను, కానీ వ్యాధిని నిర్ధారించలేను. లక్షణాలు, అవి ఎప్పటి నుంచి ఉన్నాయో వివరించండి; అవసరమైతే వైద్యుడిని సంప్రదించండి."
    if any(x in m for x in ["fever", "headache", "cough", "pain", "tired"]):
        return "I'm sorry you're not feeling well. I can offer general information, but I can't diagnose you. Note when symptoms began, stay hydrated if appropriate, and consider contacting a licensed clinician—especially if symptoms persist or worsen."
    if any(x in m for x in ["medicine", "medication", "tablet", "dose"]):
        return "For medication choice or dosage, consult a doctor or pharmacist who knows your medical history. Do not start, stop, or change prescription medicines based only on chatbot guidance."
    if any(x in m for x in ["appointment", "doctor"]):
        return "You can use the Find a Doctor section to browse sample doctor profiles and request an appointment. The included doctors are demo data, not verified real-world providers."
    return "I can help with general health education, navigating this demo, and preparing questions for a clinician. I can't diagnose conditions or replace professional care. What would you like to know?"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 8:
            flash("Enter your name, a valid email, and a password of at least 8 characters.", "danger")
        else:
            conn = db()
            try:
                conn.execute("INSERT INTO users(name,email,password_hash,role,created_at) VALUES(?,?,?,?,?)",
                             (name, email, generate_password_hash(password), "patient", now()))
                conn.commit()
                flash("Account created. Please sign in.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("That email is already registered.", "danger")
            finally:
                conn.close()
    return render_template("auth.html", mode="register")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        conn = db()
        user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session.update(user_id=user["id"], name=user["name"], role=user["role"], email=user["email"])
            return redirect(url_for("admin") if user["role"] == "admin" else url_for("dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("auth.html", mode="login")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    conn = db()
    appointments = conn.execute("""SELECT a.*, d.name doctor_name, d.specialty FROM appointments a
      JOIN doctors d ON d.id=a.doctor_id WHERE a.user_id=? ORDER BY a.appointment_date DESC""",
      (session["user_id"],)).fetchall()
    reports = conn.execute("SELECT * FROM reports WHERE user_id=? ORDER BY created_at DESC", (session["user_id"],)).fetchall()
    conn.close()
    return render_template("dashboard.html", appointments=appointments, reports=reports)

@app.route("/doctors")
def doctors():
    conn = db()
    items = conn.execute("SELECT * FROM doctors ORDER BY specialty,name").fetchall()
    conn.close()
    return render_template("doctors.html", doctors=items)

@app.route("/book/<int:doctor_id>", methods=["GET", "POST"])
@login_required
def book(doctor_id):
    conn = db()
    doctor = conn.execute("SELECT * FROM doctors WHERE id=?", (doctor_id,)).fetchone()
    if not doctor:
        conn.close()
        flash("Doctor not found.", "danger")
        return redirect(url_for("doctors"))
    if request.method == "POST":
        date = request.form.get("appointment_date", "")
        reason = request.form.get("reason", "").strip()
        if not date or not reason:
            flash("Please enter a date and reason for visit.", "danger")
        elif date < datetime.now().strftime("%Y-%m-%d"):
            flash("Choose a future date.", "danger")
        else:
            conn.execute("INSERT INTO appointments(user_id,doctor_id,appointment_date,reason,status,created_at) VALUES(?,?,?,?,?,?)",
                         (session["user_id"], doctor_id, date, reason[:500], "Pending", now()))
            conn.commit()
            conn.close()
            flash("Appointment request submitted (demo).", "success")
            return redirect(url_for("dashboard"))
    conn.close()
    return render_template("book.html", doctor=doctor)

@app.route("/symptom-checker", methods=["GET", "POST"])
def symptom_checker():
    result = None
    if request.method == "POST":
        symptoms = request.form.getlist("symptoms")
        duration = request.form.get("duration", "today")
        severity = request.form.get("severity", "mild")
        urgent = any(x in symptoms for x in ["chest_pain", "breathing", "fainting", "severe_bleeding"])
        result = {
            "urgent": urgent,
            "title": "Seek urgent medical care" if urgent else "General guidance",
            "message": ("These symptoms can indicate an emergency. Contact local emergency services or seek urgent care now."
                        if urgent else
                        "This tool cannot identify the cause of symptoms. Record when symptoms began (" + duration + "), monitor changes, and contact a licensed clinician if symptoms persist, worsen, or concern you."),
            "severity": severity
        }
    return render_template("symptoms.html", result=result)

@app.route("/chat")
@login_required
def chat():
    return render_template("chat.html")

@app.route("/api/chat", methods=["POST"])
@login_required
def api_chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()[:2000]
    lang = "te" if data.get("language") == "te" else "en"
    if not message:
        return jsonify(error="Please enter a message."), 400
    response = assistant_reply(message, lang)
    conn = db()
    conn.execute("INSERT INTO chat_logs(user_id,message,response,language,created_at) VALUES(?,?,?,?,?)",
                 (session["user_id"], message, response, lang, now()))
    conn.commit()
    conn.close()
    return jsonify(response=response)

@app.route("/reports", methods=["GET", "POST"])
@login_required
def reports():
    extracted = None
    if request.method == "POST":
        file = request.files.get("report")
        if not file or not file.filename:
            flash("Choose a PDF or TXT report.", "danger")
        elif "." not in file.filename or file.filename.rsplit(".", 1)[1].lower() not in ALLOWED_EXTENSIONS:
            flash("Only PDF and TXT files are supported.", "danger")
        else:
            safe_name = secure_filename(file.filename)
            unique_name = f"{session['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{safe_name}"
            path = os.path.join(UPLOAD_DIR, unique_name)
            file.save(path)
            text_content = ""
            try:
                if safe_name.lower().endswith(".txt"):
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        text_content = f.read(12000)
                else:
                    from pypdf import PdfReader
                    reader = PdfReader(path)
                    text_content = "\n".join((page.extract_text() or "") for page in reader.pages[:10])[:12000]
            except Exception:
                text_content = ""
            if text_content.strip():
                lines = [line.strip() for line in text_content.splitlines() if line.strip()]
                excerpt = " ".join(lines[:8])[:1000]
                summary = "Text extracted for review (not a diagnosis): " + excerpt
            else:
                summary = "No readable text was extracted. This may be a scanned PDF; OCR is not included in this demo. Ask a clinician to interpret the report."
            conn = db()
            conn.execute("INSERT INTO reports(user_id,filename,summary,created_at) VALUES(?,?,?,?)",
                         (session["user_id"], safe_name, summary, now()))
            conn.commit()
            conn.close()
            extracted = summary
            flash("Report uploaded and basic text extraction completed.", "success")
    conn = db()
    history = conn.execute("SELECT * FROM reports WHERE user_id=? ORDER BY created_at DESC", (session["user_id"],)).fetchall()
    conn.close()
    return render_template("reports.html", history=history, extracted=extracted)

@app.route("/admin")
@admin_required
def admin():
    conn = db()
    stats = {
        "patients": conn.execute("SELECT COUNT(*) FROM users WHERE role='patient'").fetchone()[0],
        "doctors": conn.execute("SELECT COUNT(*) FROM doctors").fetchone()[0],
        "appointments": conn.execute("SELECT COUNT(*) FROM appointments").fetchone()[0],
        "reports": conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0],
        "chats": conn.execute("SELECT COUNT(*) FROM chat_logs").fetchone()[0]
    }
    appointments = conn.execute("""SELECT a.*, u.name patient_name, d.name doctor_name FROM appointments a
        JOIN users u ON u.id=a.user_id JOIN doctors d ON d.id=a.doctor_id ORDER BY a.created_at DESC LIMIT 20""").fetchall()
    users = conn.execute("SELECT id,name,email,role,created_at FROM users ORDER BY created_at DESC LIMIT 20").fetchall()
    conn.close()
    return render_template("admin.html", stats=stats, appointments=appointments, users=users)

@app.route("/admin/appointment/<int:appointment_id>", methods=["POST"])
@admin_required
def update_appointment(appointment_id):
    status = request.form.get("status")
    if status not in {"Pending", "Confirmed", "Cancelled"}:
        flash("Invalid status.", "danger")
    else:
        conn = db()
        conn.execute("UPDATE appointments SET status=? WHERE id=?", (status, appointment_id))
        conn.commit()
        conn.close()
        flash("Appointment status updated.", "success")
    return redirect(url_for("admin"))

@app.errorhandler(413)
def too_large(_):
    flash("File is too large. Maximum upload size is 8 MB.", "danger")
    return redirect(url_for("reports"))

with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(debug=True)
