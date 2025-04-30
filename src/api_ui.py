# src/api_ui.py

import os, re, sqlite3, hashlib, binascii, datetime
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

def normalize_codes(raw: list[str]) -> list[str]:
    """
    Accept query strings such as
        ?aok=NS&aok=SS
        ?aok=NS, SS
        ?moi=CCI, EI, W
    and return a flat list of bare codes:
        ["NS", "SS"]   or   ["CCI", "EI", "W"]
    """
    codes = []
    for item in raw:
        codes.extend(code.strip() for code in item.split(",") if code.strip())
    return codes


# make every connection return rows you can address by column name
def _get_conn():
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    return conn

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
    "difficulty": "INTEGER",
    "timestamp": "TEXT"
})

# Favorites table: mapping user_id to course_id
create_table("favorites", {
    "user_id": "INTEGER",
    "course_id": "TEXT",
    "PRIMARY KEY (user_id, course_id)": ""
})

# ---------------------------
# Professor ratings table
# ---------------------------
create_table("professor_ratings", {
    "professor":            "TEXT PRIMARY KEY",
    "avg_rating":           "REAL",
    "avg_difficulty":       "REAL",
    "would_take_again_pct": "REAL",
    "tags":                 "TEXT"
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
    subjects = [r[0] for r in conn.execute("SELECT DISTINCT subject FROM courses").fetchall()]
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
    subjects = [r[0] for r in conn.execute("SELECT DISTINCT subject FROM courses").fetchall()]
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

@app.route("/api/courses", methods=["GET"])
def api_courses():
    subject = request.args.get("subject", "").strip()
    professor  = request.args.get("professor", "").strip()
    raw_aok = request.args.getlist("aok")
    raw_moi = request.args.getlist("moi")

    min_nbr = request.args.get("min_nbr", type=int)
    max_nbr = request.args.get("max_nbr", type=int)

    aok_codes = normalize_codes(raw_aok)   # ["NS", "SS", …]
    moi_codes = normalize_codes(raw_moi)   # ["CCI", "EI", "W", …]

    base_sql = """
    SELECT
        c.crse_id                      AS id,
        c.subject                      AS subject,
        c.catalog_nbr                  AS catalog_nbr,
        c.course_title_long            AS title,
        ca.curriculum_areas_of_knowledge AS aok,
        ca.curriculum_modes_of_inquiry   AS moi,
        GROUP_CONCAT(DISTINCT i.name_display) AS professors
    FROM courses            AS c
    LEFT JOIN class_listings AS cl ON c.crse_id = cl.crse_id
    LEFT JOIN course_offerings AS co ON c.crse_id = co.crse_id 
    LEFT JOIN course_attributes AS ca ON co.offering_id = ca.offering_id
    LEFT JOIN instructors    AS i  ON cl.class_id = i.class_id
    """

    clauses = []
    params  = []

    if subject:
        clauses.append("c.subject = ?")
        params.append(subject)

    for aok in aok_codes:
        clauses.append("ca.curriculum_areas_of_knowledge LIKE ?")
        params.append(f"%({aok})%")

    for moi in moi_codes:
        clauses.append("ca.curriculum_modes_of_inquiry LIKE ?")
        params.append(f"%({moi})%")

    if professor:
        clauses.append("i.name_display LIKE ?")
        params.append(f"%{professor}%")

    if min_nbr is not None:
        clauses.append("CAST(c.catalog_nbr AS INTEGER) >= ?")
        params.append(min_nbr)
    if max_nbr is not None:
        clauses.append("CAST(c.catalog_nbr AS INTEGER) <= ?")
        params.append(max_nbr)

    if clauses:
        base_sql += " WHERE " + " AND ".join(clauses)

    base_sql += " GROUP BY c.crse_id"

    conn = _get_conn()
    rows = conn.execute(base_sql, params).fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows])

# 2. /api/course/<course_id> - Detailed info for a single course.
@app.route("/api/course/<course_id>", methods=["GET"])
def api_course_detail(course_id):
    sql = """
    SELECT
        c.crse_id                      AS id,
        c.subject                      AS subject,
        c.catalog_nbr                  AS catalog_nbr,
        c.course_title_long            AS title,
        ca.curriculum_areas_of_knowledge AS aok,
        ca.curriculum_modes_of_inquiry   AS moi,
        GROUP_CONCAT(DISTINCT i.name_display) AS professors
    FROM courses            AS c
    LEFT JOIN class_listings AS cl ON c.crse_id = cl.crse_id
    LEFT JOIN course_offerings AS co ON c.crse_id = co.crse_id 
    LEFT JOIN course_attributes AS ca ON co.offering_id = ca.offering_id
    LEFT JOIN instructors    AS i  ON cl.class_id = i.class_id
    WHERE c.crse_id = ?
    GROUP BY c.crse_id
    """

    conn = _get_conn()
    row = conn.execute(sql, (course_id,)).fetchone()
    conn.close()

    if row:
        return jsonify(dict(row))
    else:
        return jsonify({"error": "Course not found"}), 404


# 3. /api/departments - List of departments.
@app.route("/api/departments", methods=["GET"])
def api_departments():
    conn = _get_conn()
    rows = conn.execute("SELECT DISTINCT subject FROM courses ORDER BY subject").fetchall()
    conn.close()
    departments = [{"code": r["subject"], "name": r["subject"]} for r in rows]
    return jsonify(departments)


@app.route("/api/professors", methods=["GET"])
def api_professors():
    query_text = request.args.get("query", "").strip()
    conn = _get_conn()

    # Base query: grab distinct professor names + any ratings
    sql = """
    SELECT DISTINCT
      i.name_display    AS professor,
      pr.avg_rating,
      pr.avg_difficulty,
      pr.would_take_again_pct,
      pr.tags
    FROM instructors i
    LEFT JOIN professor_ratings pr
      ON i.name_display = pr.professor
    """
    params = []
    if query_text:
        sql += " WHERE i.name_display LIKE ?"
        params.append(f"%{query_text}%")
    sql += " ORDER BY i.name_display"

    rows = conn.execute(sql, params).fetchall()
    conn.close()

    # Build JSON array
    suggestions = []
    for r in rows:
        suggestions.append({
            "professor":            r["professor"],
            "avg_rating":           r["avg_rating"],
            "avg_difficulty":       r["avg_difficulty"],
            "would_take_again_pct": r["would_take_again_pct"],
            "tags":                 r["tags"],
        })
    return jsonify(suggestions)


# 5. /api/reviews - Get reviews and submit a new review.
@app.route("/api/reviews", methods=["GET", "POST"])
def api_reviews():
    if request.method == "POST":
        data = request.get_json()
        print("Review POST Data:", data)
        course_id = data.get("course_id")
        user_id = session.get("user_id")
        review_text = data.get("review_text")
        rating = data.get("rating")
        difficulty = data.get("difficulty")
        timestamp = datetime.datetime.now().isoformat()
        if not course_id or not user_id:
            return jsonify({"error": "course_id and user_id are required"}), 400
        conn = connect_db()
        conn.execute(
            "INSERT INTO reviews (course_id, user_id, review_text, rating, difficulty, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (course_id, user_id, review_text, rating, difficulty, timestamp)
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True}), 201
    else:
        course_id = request.args.get("course_id")
        conn = connect_db()
        if course_id:
            rows = conn.execute(
                "SELECT id, course_id, user_id, review_text, rating, difficulty, timestamp FROM reviews WHERE course_id = ? ORDER BY timestamp DESC", 
                (course_id,)
            ).fetchall()


        else:
            rows = conn.execute(
                "SELECT id, course_id, user_id, review_text, rating, difficulty, timestamp FROM reviews ORDER BY timestamp DESC"
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
                "difficulty": r[5],
                "timestamp": r[6]
            })
        return jsonify(reviews)

# ---------------------------
# Favorites (Heart) API Endpoints
# ---------------------------
@app.route("/api/favorites", methods=["GET"])
@login_required
def api_favorites_get():
    user_id = session["user_id"]
    conn = _get_conn()
    fav_ids = [r["course_id"] for r in conn.execute(
        "SELECT course_id FROM favorites WHERE user_id = ?", (user_id,)
    ).fetchall()]
    conn.close()

    if not fav_ids:
        return jsonify([])

    placeholders = ",".join("?" * len(fav_ids))
    sql = f"""
    SELECT
        c.crse_id                      AS id,
        c.subject                      AS subject,
        c.catalog_nbr                  AS catalog_nbr,
        c.course_title_long            AS title,
        ca.curriculum_areas_of_knowledge AS aok,
        ca.curriculum_modes_of_inquiry   AS moi,
        GROUP_CONCAT(DISTINCT i.name_display) AS professors
    FROM courses            AS c
    LEFT JOIN course_offerings  AS co ON c.crse_id   = co.crse_id
    LEFT JOIN course_attributes AS ca ON co.offering_id = ca.offering_id
    LEFT JOIN class_listings    AS cl ON c.crse_id   = cl.crse_id
    LEFT JOIN instructors       AS i  ON cl.class_id = i.class_id
    """

    conn = _get_conn()

    placeholders = ",".join("?" for _ in fav_ids)
    sql += f" WHERE c.crse_id IN ({placeholders}) GROUP BY c.crse_id"

    rows = conn.execute(sql, fav_ids).fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows])

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
