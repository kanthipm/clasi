import os
import sqlite3, hashlib, binascii, datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from src.db import create_table, insert_many, query, connect_db
from werkzeug.utils import secure_filename

# ----------------------------------------------------
# Build absolute paths
# ----------------------------------------------------
BASE_DIR = os.path.dirname(__file__)         # e.g., /Users/you/clasier/src
STATIC_DIR = os.path.join(BASE_DIR, 'static')
UPLOAD_PROFILE_PICS = os.path.join(STATIC_DIR, 'profile_pics')

# Ensure the upload folder exists
os.makedirs(UPLOAD_PROFILE_PICS, exist_ok=True)

# ----------------------------------------------------
# Create Flask app, telling it where static/ is
# ----------------------------------------------------
app = Flask(__name__, static_folder=STATIC_DIR)
app.secret_key = "replace_this_with_getenv_secret_key_soon"
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB for images
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_PROFILE_PICS

# ---------------------------
# Database Table Setup
# ---------------------------
# Users table
create_table("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
    "username": "TEXT UNIQUE NOT NULL",
    "password_hash": "TEXT NOT NULL",
    "year": "TEXT",
    "major": "TEXT"
})

# Reviews table for course reviews
create_table("reviews", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "course_id": "TEXT NOT NULL",
    "user_id": "INTEGER NOT NULL",
    "review_text": "TEXT",
    "rating": "INTEGER",
    "timestamp": "TEXT"
})

# Favorites table: mapping user_id to course_id
create_table("favorites", {
    "user_id": "INTEGER",
    "course_id": "TEXT",
    "PRIMARY KEY (user_id, course_id)": ""
})

# ---------------------------
# Utilities
# ---------------------------
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

# ---------------------------
# Login-required Decorator
# ---------------------------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# ---------------------------
# HTML Routes
# ---------------------------
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
    subjects = [r[0] for r in conn.execute("SELECT DISTINCT department FROM courses").fetchall()]
    conn.close()
    # Pass current_user_id for favorites actions.
    return render_template("index.html", subjects=subjects, current_user_id=session["user_id"])

# Profile route; only accessible when logged in.
@app.route("/profile", endpoint="profile")
@login_required
def profile():
    rows = query("users", {"id": session.get("user_id")})
    if not rows:
        # If no user found (stale session), redirect to login.
        return redirect(url_for("login"))
    row = rows[0]
    user = {
        "id": row[0],
        "name": row[1],
        "username": row[2],
        "year": row[4],
        "major": row[5]
        # Additional fields (profile_pic, etc.) can be added if present.
    }
    return render_template("profile.html", user=user)

@app.route("/profile/edit", endpoint="edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    row = query("users", {"id": session["user_id"]})[0]
    current_year, current_major = row[4], row[5]
    conn = connect_db()
    subjects = [r[0] for r in conn.execute("SELECT DISTINCT department FROM courses").fetchall()]
    conn.close()
    years = [("2029", "Incoming Freshman"), ("2028", "Freshman"), ("2027", "Sophomore"), ("2026", "Junior"), ("2025", "Senior")]
    if request.method == "POST":
        year = request.form["year"]
        major = request.form["major"]
        conn = connect_db()
        conn.execute("UPDATE users SET year=?, major=? WHERE id=?", (year, major, session["user_id"]))
        conn.commit()
        conn.close()
        flash("Profile updated!", "success")
        return redirect(url_for("profile"))
    return render_template("edit_profile.html", years=years, subjects=subjects, current_year=current_year, current_major=current_major)

# ---------------------------
# API Endpoints (JSON)
# ---------------------------
# 1. /api/courses - List courses with filtering.
@app.route("/api/courses", methods=["GET"])
def api_courses():
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
    for aok in aok_list:
        clauses.append("courses.aok LIKE ?")
        params.append(f"%{aok}%")
    for moi in moi_list:
        clauses.append("courses.moi LIKE ?")
        params.append(f"%{moi}%")
    if professor:
        clauses.append("sections.professor LIKE ?")
        params.append(f"%{professor}%")
    if clauses:
        base_sql += " WHERE " + " AND ".join(clauses)
    base_sql += " GROUP BY courses.id"
    conn = connect_db()
    rows = conn.execute(base_sql, params).fetchall()
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

# 2. /api/course/<course_id> - Detailed info for a single course.
@app.route("/api/course/<course_id>", methods=["GET"])
def api_course_detail(course_id):
    sql = """
    SELECT courses.*, GROUP_CONCAT(DISTINCT sections.professor) as professors
    FROM courses
    LEFT JOIN sections ON courses.id = sections.crse_id
    WHERE courses.id = ?
    GROUP BY courses.id
    """
    conn = connect_db()
    row = conn.execute(sql, (course_id,)).fetchone()
    conn.close()
    if row:
        result = {
            "id": row[0],
            "department": row[1],
            "catalog_nbr": row[2],
            "title": row[3],
            "topic_id": row[4],
            "aok": row[5],
            "moi": row[6],
            "professors": row[7]
        }
        return jsonify(result)
    else:
        return jsonify({"error": "Course not found"}), 404

# 3. /api/departments - List of departments.
@app.route("/api/departments", methods=["GET"])
def api_departments():
    conn = connect_db()
    rows = conn.execute("SELECT code, name FROM departments").fetchall()
    conn.close()
    departments = [{"code": r[0], "name": r[1]} for r in rows]
    return jsonify(departments)

# 4. /api/professors - Professor suggestions for autocomplete.
@app.route("/api/professors", methods=["GET"])
def api_professors():
    query_text = request.args.get("query", "").strip()
    conn = connect_db()
    if query_text:
        sql = "SELECT DISTINCT professor FROM sections WHERE professor LIKE ? ORDER BY professor"
        param = (f"%{query_text}%",)
        rows = conn.execute(sql, param).fetchall()
    else:
        rows = conn.execute("SELECT DISTINCT professor FROM sections ORDER BY professor").fetchall()
    conn.close()
    suggestions = [r[0] for r in rows if r[0]]
    return jsonify(suggestions)

# 5. /api/reviews - Get reviews and submit a new review.
@app.route("/api/reviews", methods=["GET", "POST"])
def api_reviews():
    if request.method == "POST":
        data = request.get_json()
        course_id = data.get("course_id")
        user_id = session.get("user_id")
        review_text = data.get("review_text")
        rating = data.get("rating")
        timestamp = datetime.datetime.utcnow().isoformat()
        if not course_id or not user_id:
            return jsonify({"error": "course_id and user_id are required"}), 400
        conn = connect_db()
        conn.execute(
            "INSERT INTO reviews (course_id, user_id, review_text, rating, timestamp) VALUES (?, ?, ?, ?, ?)",
            (course_id, user_id, review_text, rating, timestamp)
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True}), 201
    else:
        course_id = request.args.get("course_id")
        conn = connect_db()
        if course_id:
            rows = conn.execute(
                "SELECT id, course_id, user_id, review_text, rating, timestamp FROM reviews WHERE course_id = ? ORDER BY timestamp DESC", 
                (course_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, course_id, user_id, review_text, rating, timestamp FROM reviews ORDER BY timestamp DESC"
            ).fetchall()
        conn.close()
        reviews = []
        for r in rows:
            reviews.append({
                "id": r[0],
                "course_id": r[1],
                "user_id": r[2],
                "review_text": r[3],
                "rating": r[4],
                "timestamp": r[5]
            })
        return jsonify(reviews)

# ---------------------------
# Favorites (Heart) API Endpoints
# ---------------------------
@app.route("/api/favorites", methods=["GET"])
@login_required
def api_favorites_get():
    user_id = session["user_id"]
    conn = connect_db()
    rows = conn.execute("SELECT course_id FROM favorites WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()
    fav_course_ids = [r[0] for r in rows]
    if fav_course_ids:
        conn = connect_db()
        placeholders = ",".join("?" * len(fav_course_ids))
        sql = f"SELECT courses.*, GROUP_CONCAT(DISTINCT sections.professor) as professors FROM courses LEFT JOIN sections ON courses.id = sections.crse_id WHERE courses.id IN ({placeholders}) GROUP BY courses.id"
        rows = conn.execute(sql, fav_course_ids).fetchall()
        conn.close()
        favorites = []
        for r in rows:
            favorites.append({
                "id": r[0],
                "department": r[1],
                "catalog_nbr": r[2],
                "title": r[3],
                "topic_id": r[4],
                "aok": r[5],
                "moi": r[6],
                "professors": r[7]
            })
        return jsonify(favorites)
    else:
        return jsonify([])

@app.route("/api/favorites", methods=["POST"])
@login_required
def api_favorites_post():
    data = request.get_json()
    course_id = data.get("course_id")
    user_id = session["user_id"]
    if not course_id:
        return jsonify({"error": "course_id is required"}), 400
    conn = connect_db()
    try:
        conn.execute("INSERT INTO favorites (user_id, course_id) VALUES (?, ?)", (user_id, course_id))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"message": "Already favorited"}), 200
    conn.close()
    return jsonify({"success": True}), 201

@app.route("/api/favorites", methods=["DELETE"])
@login_required
def api_favorites_delete():
    data = request.get_json()
    course_id = data.get("course_id")
    user_id = session["user_id"]
    if not course_id:
        return jsonify({"error": "course_id is required"}), 400
    conn = connect_db()
    conn.execute("DELETE FROM favorites WHERE user_id = ? AND course_id = ?", (user_id, course_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True}), 200

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
