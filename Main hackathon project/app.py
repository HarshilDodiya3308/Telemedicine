import os
import sys
from datetime import datetime
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_cors import CORS
from geopy.geocoders import Nominatim
from dotenv import load_dotenv
import google.generativeai as genai
import psycopg2
from psycopg2.extras import RealDictCursor

# ---------- Gemini Setup ----------
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# ---------- Flask App Setup ----------
app = Flask(__name__)
app.secret_key = "supersecretkey"
CORS(app)

# ---------- DB connection ----------
DATABASE_URL = "postgresql://telemedicine_db_vnuk_user:2Iu3phQzrNlWs0BN0Klem4MmwR75ZzEc@dpg-db1q95u0tbcc73c14k1g-a.oregon-postgres.render.com/telemedicine_db_vnuk"
db = psycopg2.connect(DATABASE_URL)

# ऑटोमैटिक टेबल्स सेटअप
with db.cursor() as setup_cursor:
    setup_cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(100) UNIQUE,
            password VARCHAR(100),
            role VARCHAR(20)
        );
    """)
    setup_cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(100) UNIQUE,
            password VARCHAR(100),
            specialization VARCHAR(100),
            hospital_name VARCHAR(150),
            city VARCHAR(100),
            area VARCHAR(100),
            experience INT,
            latitude DECIMAL(10,7),
            longitude DECIMAL(10,7)
        );
    """)
    setup_cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id SERIAL PRIMARY KEY,
            patient_id INT,
            doctor_id INT,
            date DATE,
            time TIME,
            status VARCHAR(50)
        );
    """)
    setup_cursor.execute("SELECT COUNT(*) FROM doctors;")
    if setup_cursor.fetchone()[0] == 0:
        setup_cursor.execute("""
            INSERT INTO doctors (name, specialization, hospital_name, city, area) 
            VALUES ('Dr. Rahul Khanna', 'Oncologist', 'Smile Dental Studio', 'Ahmedabad', 'Memnagar');
        """)
    db.commit()

# Helper functions
def get_specializations():
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT DISTINCT specialization FROM doctors ORDER BY specialization;")
    specializations = [row['specialization'] for row in cursor.fetchall()]
    cursor.close()
    return specializations

def get_doctors():
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT id, name, specialization FROM doctors;")
    result = cursor.fetchall()
    cursor.close()
    return result

# Routes
@app.route('/')
def index():
    user_name = None
    if 'user' in session:
        user_name = session['user']['name']
    return render_template("index.html", user_name=user_name)

@app.route("/appointment_page", methods=["GET", "POST"])
def appointment_page():
    if "user" not in session or session.get("role") != "patient":
        return redirect(url_for("login"))

    cursor = db.cursor(cursor_factory=RealDictCursor)
    if request.method == "POST":
        patient_id = session["user"]["id"]
        doctor_id = request.form.get("doctor_id")
        date = request.form["date"]
        time = request.form["time"]

        sql = "INSERT INTO appointments (patient_id, doctor_id, date, time, status) VALUES (%s, %s, %s, %s, %s);"
        cursor.execute(sql, (patient_id, doctor_id, date, time, "booked"))
        db.commit()

        specializations = get_specializations()
        cursor.close()
        return render_template(
            "appointment.html",
            message="✅ Appointment booked successfully!",
            specializations=specializations,
            min_date=datetime.now().strftime("%Y-%m-%d"),
            user_name=session["user"]["name"] if "user" in session else None,
        )

    doctor_id = request.args.get("doctor_id")
    doctor_name = request.args.get("doctor_name")
    specialization = request.args.get("specialization")

    prefilled = False
    if doctor_id and doctor_name and specialization:
        prefilled = True

    specializations = get_specializations()
    if not specializations:
        cursor.close()
        flash("No doctors available for appointment", "warning")
        return redirect(url_for("index"))

    cursor.close()
    return render_template(
        "appointment.html",
        specializations=specializations,
        doctor_id=doctor_id,
        doctor_name=doctor_name,
        specialization=specialization,
        prefilled=prefilled,
        min_date=datetime.now().strftime("%Y-%m-%d"),
        user_name=session["user"]["name"] if "user" in session else None,
    )

@app.route('/get_doctors_by_specialization')
def get_doctors_by_specialization():
    specialization = request.args.get('specialization', '')
    cursor = db.cursor(cursor_factory=RealDictCursor)
    
    if specialization:
        cursor.execute("SELECT id, name, specialization FROM doctors WHERE specialization = %s ORDER BY name;", (specialization,))
    else:
        cursor.execute("SELECT id, name, specialization FROM doctors ORDER BY name;")
    
    doctors = cursor.fetchall()
    cursor.close()
    return jsonify({'doctors': doctors})

# ---------- AUTH ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cursor = db.cursor(cursor_factory=RealDictCursor)

        cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s LIMIT 1;", (email, password))
        user = cursor.fetchone()

        if user:
            session['user'] = dict(user)
            session['role'] = "patient"
            cursor.close()
            return redirect(url_for('index'))

        cursor.execute("SELECT * FROM doctors WHERE email=%s AND password=%s LIMIT 1;", (email, password))
        doctor = cursor.fetchone()

        if doctor:
            session['user'] = dict(doctor)
            session['role'] = "doctor"
            cursor.close()
            return redirect(url_for('doctor_dashboard'))

        cursor.close()
        flash("Invalid email or password", "danger")
        return redirect(url_for('login'))

    return render_template('auth.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        cursor = db.cursor(cursor_factory=RealDictCursor)

        cursor.execute("SELECT id FROM users WHERE email=%s UNION SELECT id FROM doctors WHERE email=%s;", (email, email))
        existing = cursor.fetchone()

        if existing:
            cursor.close()
            flash("⚠️ This email is already registered. Please log in.", "warning")
            return redirect(url_for('login'))

        if role == "patient":
            sql = "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s);"
            cursor.execute(sql, (name, email, password, role))
        elif role == "doctor":
            specialization = request.form['specialization']
            sql = "INSERT INTO doctors (name, email, password, specialization) VALUES (%s, %s, %s, %s);"
            cursor.execute(sql, (name, email, password, specialization))

        db.commit()
        cursor.close()
        flash("✅ User registered successfully! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('auth.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('index'))

@app.route('/doctor_dashboard')
def doctor_dashboard():
    if 'user' not in session or session.get('role') != 'doctor':
        flash("Access denied. Please log in as a doctor.", "danger")
        return redirect(url_for('login'))

    doctor_id = session['user']['id']
    cursor = db.cursor(cursor_factory=RealDictCursor)

    sql = """
        SELECT a.id, a.date, a.time, a.status, u.name AS patient_name
        FROM appointments a
        JOIN users u ON a.patient_id = u.id
        WHERE a.doctor_id = %s
        ORDER BY a.date, a.time;
    """
    cursor.execute(sql, (doctor_id,))
    appointments = cursor.fetchall()
    
    completed_count = sum(1 for appt in appointments if appt['status'].lower() == 'completed')
    pending_count = sum(1 for appt in appointments if appt['status'].lower() == 'booked')

    cursor.close()
    return render_template("doctor_dashboard.html", 
                         appointments=appointments, 
                         doctor=session['user'],
                         completed_count=completed_count,
                         pending_count=pending_count)

@app.route('/update_appointment_status', methods=['POST'])
def update_appointment_status():
    if 'user' not in session or session.get('role') != 'doctor':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.get_json()
    appointment_id = data.get('appointment_id')
    status = data.get('status')
    
    doctor_id = session['user']['id']
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM appointments WHERE id = %s AND doctor_id = %s;", (appointment_id, doctor_id))
    appointment = cursor.fetchone()
    
    if not appointment:
        cursor.close()
        return jsonify({'success': False, 'message': 'Appointment not found'})
    
    cursor.execute("UPDATE appointments SET status = %s WHERE id = %s;", (status, appointment_id))
    db.commit()
    cursor.close()
    
    return jsonify({'success': True})

@app.route('/doctors')
def doctors_page():
    specialization = request.args.get('specialization', '')
    location_text = request.args.get('location', '')
