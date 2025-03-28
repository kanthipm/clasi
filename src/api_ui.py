# final updated code with static in src folder
import os
import sqlite3, hashlib, binascii
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
import sqlite3, hashlib, os, binascii
<<<<<<< HEAD
from src.db import create_table, insert_many, query, connect_db
=======
from .db import create_table, insert_many, query, connect_db, add_columns_if_missing
from werkzeug.utils import secure_filename

from .db import create_table, insert_many, query, connect_db, add_columns_if_missing

# Build absolute paths
BASE_DIR = os.path.dirname(__file__)         # e.g., /Users/you/clasier/src
STATIC_DIR = os.path.join(BASE_DIR, 'static')
UPLOAD_PROFILE_PICS = os.path.join(STATIC_DIR, 'profile_pics')

# Ensure the upload folder exists
os.makedirs(UPLOAD_PROFILE_PICS, exist_ok=True)

# Create Flask app, telling it where static/ is
app = Flask(__name__, static_folder=STATIC_DIR)
app.secret_key = "replace_this_with_getenv_secret_key_soon"

<<<<<<< HEAD
# Ensure the users table exists
=======
# Max 2MB for pictures
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
# Allowed image file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# This is the folder path used by your upload logic
app.config['UPLOAD_FOLDER'] = UPLOAD_PROFILE_PICS


####################
# Setup DB schema
####################

>>>>>>> f77b0ed51d67d2e9609f886c6fd66d6544ef67fd
create_table("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
    "username": "TEXT UNIQUE NOT NULL",
    "password_hash": "TEXT NOT NULL",
    "year": "TEXT",
    "major": "TEXT"
})

add_columns_if_missing("users", {
    "second_major": "TEXT",
    "minor": "TEXT",
    "advisor_name": "TEXT",
    "advisor_email": "TEXT",
    "expected_grad_term": "TEXT",
    "admit_term": "TEXT",
    "gpa": "REAL",
    "units": "REAL",
    "profile_pic": "TEXT"
})


####################
# Utilities
####################

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 200_000)
    return f"{binascii.hexlify(salt).decode()}:{binascii.hexlify(dk).decode()}"

def verify_password(stored_hash: str, provided_password: str) -> bool:
    try:
        salt_hex, hash_hex = stored_hash.split(":")
    except ValueError:
        return False
    salt = binascii.unhexlify(salt_hex)
    new_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode(), salt, 200_000)
    return binascii.hexlify(new_hash).decode() == hash_hex

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


####################
# Routes
####################

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"].strip()
        username = request.form["username"].strip()
        password = request.form["password"]
        hashed = hash_password(password)
        try:
            insert_many("users", [{"name": name, "username": username, "password_hash": hashed}])
            flash("Account created! Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already taken.", "danger")
    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        user = query("users", {"username": username})
        if user and verify_password(user[0][3], password):
            session["user_id"] = user[0][0]
            session["username"] = user[0][2]
            return redirect(url_for("index"))
        flash("Invalid credentials", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    conn = connect_db()
    # Get distinct department values from the courses table
    subjects = [r[0] for r in conn.execute("SELECT DISTINCT department FROM courses").fetchall()]
    conn.close()
    return render_template("index.html", subjects=subjects)


# Updated /courses endpoint: All selected AOK and MOI filters must be satisfied.
@app.route("/courses")
def courses_from_db():
    # Get query parameters
    department = request.args.get("department", "").strip()
    professor = request.args.get("professor", "").strip()
    aok_list = request.args.getlist("aok")
    moi_list = request.args.getlist("moi")

    base_sql = """
    SELECT courses.*, GROUP_CONCAT(DISTINCT sections.professor) as professors
    FROM courses
    LEFT JOIN sections ON courses.id = sections.crse_id
    """
    clauses = []
    params = []

    if department:
        clauses.append("courses.department = ?")
        params.append(department)
    
    # For each selected AOK, add an individual condition (AND)
    if aok_list:
        for aok in aok_list:
            clauses.append("courses.aok LIKE ?")
            params.append(f"%{aok}%")
    
    # For each selected MOI, add an individual condition (AND)
    if moi_list:
        for moi in moi_list:
            clauses.append("courses.moi LIKE ?")
            params.append(f"%{moi}%")
    
    if professor:
        clauses.append("sections.professor LIKE ?")
        params.append(f"%{professor}%")
    
    final_sql = base_sql
    if clauses:
        final_sql += " WHERE " + " AND ".join(clauses)
    
    final_sql += " GROUP BY courses.id"

    conn = connect_db()
    rows = conn.execute(final_sql, params).fetchall()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "id": r[0],
            "department": r[1],
            "catalog_nbr": r[2],
            "title": r[3],
            "topic_id": r[4],
            "aok": r[5],
            "moi": r[6],
            "professors": r[7]
        })

    return jsonify(results)

# New endpoint for professor name suggestions (autocomplete)
@app.route("/professors")
def professor_suggestions():
    query_text = request.args.get("query", "").strip()
    conn = connect_db()
    if query_text:
        sql = "SELECT DISTINCT professor FROM sections WHERE professor LIKE ? ORDER BY professor"
        param = (f"%{query_text}%",)
        rows = conn.execute(sql, param).fetchall()
    else:
        rows = []
    conn.close()
    return jsonify([
        {
            "id": r[0], "subject": r[1], "subject_name": r[2], "catalog_nbr": r[3],
            "title": r[4], "term_code": r[5], "term_desc": r[6], "effdt": r[7],
            "multi_off": r[8], "topic_id": r[9]
        } for r in rows
    ])


@app.route("/profile")
@login_required
def profile():
    row = query("users", {"id": session["user_id"]})[0]
    user = {
        "id": row[0],
        "name": row[1],
        "username": row[2],
        # row[3] is password_hash
        "year": row[4],
        "major": row[5],
        "second_major": row[6],
        "minor": row[7],
        "advisor_name": row[8],
        "advisor_email": row[9],
        "expected_grad_term": row[10],
        "admit_term": row[11],
        "gpa": row[12],
        "units": row[13],
        "profile_pic": row[14]
    }
    return render_template("profile.html", user=user)


@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    row = query("users", {"id": session["user_id"]})[0]
<<<<<<< HEAD
    current_year, current_major = row[4], row[5]
    conn = connect_db()
    subjects = [r[0] for r in conn.execute("SELECT DISTINCT department FROM courses").fetchall()]
    conn.close()
    years = [("2029","Incoming Freshman"),("2028","Freshman"),("2027","Sophomore"),("2026","Junior"),("2025","Senior")]
=======
    current = {
        "year": row[4],
        "major": row[5],
        "second_major": row[6],
        "minor": row[7],
        "advisor_name": row[8],
        "advisor_email": row[9],
        "expected_grad_term": row[10],
        "admit_term": row[11],
        "gpa": row[12],
        "units": row[13],
        "profile_pic": row[14]
    }

>>>>>>> f77b0ed51d67d2e9609f886c6fd66d6544ef67fd
    if request.method == "POST":
        # Grab all the form fields
        year = request.form.get("year", current["year"])
        major = request.form.get("major", current["major"])
        second_major = request.form.get("second_major", current["second_major"])
        minor = request.form.get("minor", current["minor"])
        advisor_name = request.form.get("advisor_name", current["advisor_name"])
        advisor_email = request.form.get("advisor_email", current["advisor_email"])
        expected_grad_term = request.form.get("expected_grad_term", current["expected_grad_term"])
        admit_term = request.form.get("admit_term", current["admit_term"])
        gpa = request.form.get("gpa", current["gpa"])
        units = request.form.get("units", current["units"])

        # Handle file upload if provided
        file = request.files.get("profile_pic")
        filename = current["profile_pic"]  # default to existing
        if file and allowed_file(file.filename):
            safe_filename = secure_filename(file.filename)
            filename = f"{session['user_id']}_{safe_filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            print("Saving profile pic and fields...")
            print("Received file:", file.filename if file else "No file")
            print("Final saved filename:", filename)
            print("Saved to:", file_path)

        # Update DB
        conn = connect_db()
        conn.execute("""
            UPDATE users
            SET year=?, major=?, second_major=?, minor=?, advisor_name=?, advisor_email=?,
                expected_grad_term=?, admit_term=?, gpa=?, units=?, profile_pic=?
            WHERE id=?
        """, (
            year, major, second_major, minor,
            advisor_name, advisor_email,
            expected_grad_term, admit_term,
            gpa, units,
            filename, session["user_id"]
        ))
        conn.commit()
        conn.close()

        flash("Profile updated!", "success")
        return redirect(url_for("profile"))

    return render_template("edit_profile.html", **current)


if __name__ == "__main__":
    # Make sure to run from the project root ("clasier/"):
    #   FLASK_APP=src.api_ui FLASK_ENV=development flask run
    # Or pass the --port if needed:
    #   flask run --port=5050
<<<<<<< HEAD
    app.run(debug=True, use_reloader=False)
=======
    app.run(debug=True)
>>>>>>> f77b0ed51d67d2e9609f886c6fd66d6544ef67fd
