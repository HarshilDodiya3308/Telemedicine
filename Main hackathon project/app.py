from flask import Flask, request, render_template, redirect, url_for, flash, session, jsonify
import mysql.connector
from flask_cors import CORS
from datetime import datetime
from geopy.geocoders import Nominatim
from dotenv import load_dotenv
import google.generativeai as genai
import os


# ---------- Gemini Setup ----------
load_dotenv()  # load from .env file
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))  # ✅ set once globally

# ---------- Flask App Setup ----------
app = Flask(__name__)
app.secret_key = "supersecretkey"
CORS(app)

# DB connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="smart_healthcare"
)
cursor = db.cursor(dictionary=True)

# Helper functions
def get_specializations():
    cursor.execute("SELECT DISTINCT specialization FROM doctors ORDER BY specialization")
    specializations = [row['specialization'] for row in cursor.fetchall()]
    return specializations

def get_doctors():
    cursor.execute("SELECT id, name, specialization FROM doctors")
    return cursor.fetchall()

# Routes
@app.route('/')
def index():
    user_name = None
    if 'user' in session:
        user_name = session['user']['name']
    return render_template("index.html", user_name=user_name)

# ... (other routes remain the same until the appointment route)
@app.route("/appointment_page", methods=["GET", "POST"])
def appointment_page():
    # check if logged in as patient
    if "user" not in session or session.get("role") != "patient":
        return redirect(url_for("login"))

    if request.method == "POST":
        patient_id = session["user"]["id"]
        doctor_id = request.form.get("doctor_id")
        date = request.form["date"]
        time = request.form["time"]

        sql = "INSERT INTO appointments (patient_id, doctor_id, date, time, status) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(sql, (patient_id, doctor_id, date, time, "booked"))
        db.commit()

        specializations = get_specializations()
        return render_template(
            "appointment.html",
            message="✅ Appointment booked successfully!",
            specializations=specializations,
            min_date=datetime.now().strftime("%Y-%m-%d"),
            user_name=session["user"]["name"] if "user" in session else None,
        )

    # ----- GET request -----
    # Check if doctor was passed from doctors.html
    doctor_id = request.args.get("doctor_id")
    doctor_name = request.args.get("doctor_name")
    specialization = request.args.get("specialization")

    prefilled = False
    if doctor_id and doctor_name and specialization:
        prefilled = True

    specializations = get_specializations()
    if not specializations:
        flash("No doctors available for appointment", "warning")
        return redirect(url_for("index"))

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


# Add this endpoint to get doctors by specialization
@app.route('/get_doctors_by_specialization')
def get_doctors_by_specialization():
    specialization = request.args.get('specialization', '')
    
    if specialization:
        cursor.execute("SELECT id, name, specialization FROM doctors WHERE specialization = %s ORDER BY name", (specialization,))
    else:
        cursor.execute("SELECT id, name, specialization FROM doctors ORDER BY name")
    
    doctors = cursor.fetchall()
    return jsonify({'doctors': doctors})


# ---------- AUTH ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # check patient table
        cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s LIMIT 1", (email, password))
        user = cursor.fetchone()

        if user:
            session['user'] = user
            session['role'] = "patient"
            return redirect(url_for('index'))

        # check doctor table
        cursor.execute("SELECT * FROM doctors WHERE email=%s AND password=%s LIMIT 1", (email, password))
        doctor = cursor.fetchone()

        if doctor:
            session['user'] = doctor
            session['role'] = "doctor"
            return redirect(url_for('doctor_dashboard'))

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

        # 🔍 Check if email already exists in users or doctors
        cursor.execute("SELECT id FROM users WHERE email=%s UNION SELECT id FROM doctors WHERE email=%s", (email, email))
        existing = cursor.fetchone()

        if existing:
            flash("⚠️ This email is already registered. Please log in.", "warning")
            return redirect(url_for('login'))

        # Insert new user
        if role == "patient":
            sql = "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (name, email, password, role))
        elif role == "doctor":
            specialization = request.form['specialization']
            sql = "INSERT INTO doctors (name, email, password, specialization) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (name, email, password, specialization))

        db.commit()
        flash("✅ User registered successfully! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('auth.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('index'))


# Doctor Dashboard Page
@app.route('/doctor_dashboard')
def doctor_dashboard():
    if 'user' not in session or session.get('role') != 'doctor':
        flash("Access denied. Please log in as a doctor.", "danger")
        return redirect(url_for('login'))

    doctor_id = session['user']['id']

    sql = """
        SELECT a.id, a.date, a.time, a.status, u.name AS patient_name
        FROM appointments a
        JOIN users u ON a.patient_id = u.id
        WHERE a.doctor_id = %s
        ORDER BY a.date, a.time
    """
    cursor.execute(sql, (doctor_id,))
    appointments = cursor.fetchall()
    
    # Calculate counts for stats
    completed_count = sum(1 for appt in appointments if appt['status'].lower() == 'completed')
    pending_count = sum(1 for appt in appointments if appt['status'].lower() == 'booked')

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
    
    # Verify the doctor owns this appointment
    doctor_id = session['user']['id']
    cursor.execute("SELECT * FROM appointments WHERE id = %s AND doctor_id = %s", (appointment_id, doctor_id))
    appointment = cursor.fetchone()
    
    if not appointment:
        return jsonify({'success': False, 'message': 'Appointment not found'})
    
    # Update the status
    cursor.execute("UPDATE appointments SET status = %s WHERE id = %s", (status, appointment_id))
    db.commit()
    
    return jsonify({'success': True})


@app.route('/doctors')
def doctors_page():
    specialization = request.args.get('specialization', '')
    location_text = request.args.get('location', '')
    experience = request.args.get('experience', '')

    # Optional lat/lng search
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    radius = float(request.args.get('radius', 5))  # default 5 km

    query = "SELECT * FROM doctors WHERE 1=1"
    params = []

    if specialization:
        query += " AND specialization LIKE %s"
        params.append(f"%{specialization}%")

    if location_text:
        # ✅ Check hospital_name, city, AND area
        query += " AND (hospital_name LIKE %s OR city LIKE %s OR area LIKE %s)"
        params.append(f"%{location_text}%")
        params.append(f"%{location_text}%")
        params.append(f"%{location_text}%")

    if experience:
        query += " AND experience >= %s"
        params.append(experience)

    cursor.execute(query, params)
    doctors = cursor.fetchall()

    # ✅ Radius-based filtering
    area_name = None
    if lat and lng:
        import math
        lat = float(lat)
        lng = float(lng)

        def haversine(lat1, lon1, lat2, lon2):
            R = 6371  # km
            dLat = math.radians(lat2 - lat1)
            dLon = math.radians(lon2 - lon1)
            a = (math.sin(dLat/2)**2 +
                 math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
                 math.sin(dLon/2)**2)
            return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        doctors = [
            d for d in doctors
            if d['latitude'] and d['longitude']
            and haversine(lat, lng, float(d['latitude']), float(d['longitude'])) <= radius
        ]

        # ✅ Reverse geocoding
        from geopy.geocoders import Nominatim
        geolocator = Nominatim(user_agent="doctor_locator")
        location = geolocator.reverse(f"{lat}, {lng}")
        if location and "address" in location.raw:
            addr = location.raw["address"]
            area_name = addr.get("suburb") or addr.get("neighbourhood") or addr.get("city_district") or addr.get("city")

    # ✅ Get unique areas from the DB for location grid
    cursor.execute("SELECT DISTIpyNCT area FROM doctors ORDER BY area ASC")
    areas_result = cursor.fetchall()
    areas = [row['area'] for row in areas_result if row['area']]

    user_name = session.get('user', {}).get('name')

    return render_template(
        "doctors.html",
        doctors=doctors,
        specialization=specialization,
        location=location_text,
        experience=experience,
        user_name=user_name,
        radius=radius,
        area_name=area_name,
        areas=areas  # ✅ Pass dynamic areas to template
    )

# ---------- Chat Route ----------
from google.generativeai import types

# ---------- General Chat (Expert doctor & medicine adviser) ----------
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '')

    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction="""
                You are an expert doctor and medicine adviser. 
                Provide clear, professional, and practical medical guidance in English. 
                Explain possible causes, preventive steps, and remedies. 
                Keep the tone empathetic and simple so even rural patients can understand. 
                Answer briefly, unless the user explicitly asks for a detailed explanation.
            """
        )
        response = model.generate_content(user_message)
        bot_reply = response.text if hasattr(response, 'text') else "No response from Gemini."
    except Exception as e:
        bot_reply = f"Error: {str(e)}"

    return jsonify({'reply': bot_reply})


# ---------- Health Assistant Chat (Expert doctor, max 50 words) ----------
@app.route("/chatbot_health", methods=["POST", "GET"])
def chatbot_health():
    if request.method == "POST":
        user_id = session.get("user", {}).get("id")
        question = request.form.get("question")

        if question:
            # 1) Check chat_history
            cursor.execute("SELECT answer FROM chat_history WHERE question = %s LIMIT 1", (question,))
            row = cursor.fetchone()
            if row:
                return jsonify({"answer": row["answer"], "source": "database"})

            # 2) Call Gemini if not found
            model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                system_instruction="""
                    You are an expert doctor. 
                    Always reply only in English. 
                    Solve the user's health problem in a maximum of 50 words. 
                    Be precise, empathetic, and solution-oriented. 
                    Do not add unnecessary details, focus only on direct and helpful medical advice.
                """
            )
            response = model.generate_content(question)
            answer = response.text

            # 3) Save in DB
            sql = "INSERT INTO chat_history (user_id, question, answer) VALUES (%s, %s, %s)"
            cursor.execute(sql, (user_id, question, answer))
            db.commit()

            return jsonify({"answer": answer, "source": "gemini"})

    return render_template("chatbot_health.html")


# ---------- Medicine Advisor Chat (Expert medicine adviser, max 50 words) ----------
@app.route("/chatbot_medicine", methods=["POST", "GET"])
def chatbot_medicine():
    if request.method == "POST":
        symptom = request.form.get("symptom")

        if symptom:
            # 1) Check remedies DB first
            sql = "SELECT remedy FROM remedies WHERE symptom LIKE %s LIMIT 1"
            cursor.execute(sql, ("%" + symptom + "%",))
            remedy = cursor.fetchone()

            if remedy:
                return jsonify({"answer": remedy["remedy"], "source": "remedies-db"})

            # 2) If not found in DB → ask Gemini
            model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                system_instruction="""
                    You are an expert medicine adviser. 
                    Always reply only in English. 
                    Provide safe and practical medicine or home remedy suggestions in a maximum of 50 words. 
                    Keep the tone helpful, avoid long explanations, and never suggest harmful or unsafe treatments. 
                    If the symptom is unclear or not health-related, politely inform the user that you can only assist with health-related queries.
                """
            )
            response = model.generate_content(f"Suggest remedies for {symptom}")
            answer = response.text

            # 3) Store the new remedy into DB
            insert_sql = "INSERT INTO remedies (symptom, remedy) VALUES (%s, %s)"
            cursor.execute(insert_sql, (symptom, answer))
            db.commit()

            return jsonify({"answer": answer, "source": "gemini"})

    return render_template("chatbot_medicine.html")



# ---------------- RUN ---------------- #
if __name__ == '__main__':
    app.run(debug=True)