# src/api_ui.py
import os, re, sqlite3, hashlib, binascii, datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)
from werkzeug.utils import secure_filename

from src.db import (
    create_table, insert_many, query,
    connect_db, add_columns_if_missing
)
from src.schema import ensure_schema          # central schema helper

# ──────────────────────────────────────────────────────────────
# Ensure tables & columns exist
# ──────────────────────────────────────────────────────────────
ensure_schema()

# ─── Paths & Flask config ─────────────────────────────────────
BASE_DIR            = os.path.dirname(__file__)
STATIC_DIR          = os.path.join(BASE_DIR, "static")
UPLOAD_PROFILE_PICS = os.path.join(STATIC_DIR, "profile_pics")
os.makedirs(UPLOAD_PROFILE_PICS, exist_ok=True)

DEFAULT_PIC_NAME    = "default_avatar.png"    # match your file
app = Flask(__name__, static_folder=STATIC_DIR)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "replace_this_in_prod")
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # 2 MB
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
app.config["UPLOAD_FOLDER"] = UPLOAD_PROFILE_PICS

# ─── Utility helpers ─────────────────────────────────────────
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk   = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return f"{binascii.hexlify(salt).decode()}:{binascii.hexlify(dk).decode()}"

def verify_password(stored: str, pw: str) -> bool:
    try:
        salt_hex, stored_hash = stored.split(":")
        salt = binascii.unhexlify(salt_hex)
    except ValueError:
        return False
    new_hash = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 200_000)
    return binascii.hexlify(new_hash).decode() == stored_hash

def normalize_codes(raw: list[str]) -> list[str]:
    codes = []
    for item in raw:
        codes.extend(code.strip() for code in item.split(",") if code.strip())
    return codes

def _get_conn():
    conn = connect_db()
    conn.row_factory = sqlite3.Row
    return conn

# ─── Auth decorator ──────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# ──────────────────────────────────────────────────────────────
# ROUTES
# ──────────────────────────────────────────────────────────────

# ---------- Signup ---------------------------------------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name     = request.form["name"].strip()
        username = request.form["username"].strip()
        password = request.form["password"]
        hashed   = hash_password(password)
        try:
            insert_many("users", [{
                "name": name,
                "username": username,
                "password_hash": hashed,
                "profile_pic_path": DEFAULT_PIC_NAME   # set default avatar
            }])
            flash("Account created! Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already taken.", "danger")
    return render_template("signup.html")

# ---------- Login / Logout --------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        rows = query("users", {"username": username})
        if rows and verify_password(rows[0][3], password):
            session["user_id"]  = rows[0][0]
            session["username"] = rows[0][2]
            return redirect(url_for("index"))
        flash("Invalid credentials", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------- Home ------------------------------------------------------------
@app.route("/")
@login_required
def index():
    conn = connect_db()
    subjects = [
        r[0] for r in conn.execute(
            "SELECT DISTINCT subject FROM courses ORDER BY subject"
        ).fetchall()
    ]
    conn.close()
    return render_template("index.html",
                           subjects=subjects,
                           current_user_id=session["user_id"])

# ---------- Profile ---------------------------------------------------------
@app.route("/profile")
@login_required
def profile():
    conn = _get_conn()
    row  = conn.execute(
        "SELECT * FROM users WHERE id=?", (session["user_id"],)
    ).fetchone()
    conn.close()
    if not row:
        return redirect(url_for("login"))

    def fallback(val, default):
        return val if val not in (None, "", "None") else default

    user = {
        "id":                 row["id"],
        "name":               row["name"],
        "username":           row["username"],
        "year":               fallback(row["year"], "Unknown"),
        "major":              fallback(row["major"], "Unknown"),
        "second_major":       fallback(row["second_major"], "None"),
        "minor":              fallback(row["minor"], "None"),
        "advisor_name":       fallback(row["advisor_name"], "N/A"),
        "advisor_email":      fallback(row["advisor_email"], "N/A"),
        "expected_grad_term": fallback(row["expected_grad_term"], "Unknown"),
        "admit_term":         fallback(row["admit_term"], "Unknown"),
        "gpa":                fallback(row["gpa"], "N/A"),
        "units":              fallback(row["units"], "N/A"),
        "profile_pic_path":   row["profile_pic_path"] or DEFAULT_PIC_NAME
    }
    return render_template("profile.html", user=user)

# ---------- Edit Profile ----------------------------------------------------
@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    conn = _get_conn()
    row  = conn.execute(
        "SELECT * FROM users WHERE id=?", (session["user_id"],)
    ).fetchone()

    subjects = [
        r["subject"] for r in conn.execute(
            "SELECT DISTINCT subject FROM courses ORDER BY subject"
        )
    ]
    conn.close()

    years = [
        ("2029", "Incoming Freshman"),
        ("2028", "Freshman"),
        ("2027", "Sophomore"),
        ("2026", "Junior"),
        ("2025", "Senior"),
    ]

    if request.method == "POST":
        # text fields
        fields = {
            "year":               request.form.get("year"),
            "major":              request.form.get("major"),
            "second_major":       request.form.get("second_major"),
            "minor":              request.form.get("minor"),
            "advisor_name":       request.form.get("advisor_name"),
            "advisor_email":      request.form.get("advisor_email"),
            "expected_grad_term": request.form.get("expected_grad_term"),
            "admit_term":         request.form.get("admit_term"),
            "gpa":                request.form.get("gpa"),
            "units":              request.form.get("units"),
        }

        # picture upload
        file = request.files.get("profile_pic")
        if file and allowed_file(file.filename):
            filename  = secure_filename(f"{session['user_id']}_{file.filename}")
            file.save(os.path.join(UPLOAD_PROFILE_PICS, filename))
            fields["profile_pic_path"] = filename

        set_clause = ", ".join(f"{k}=?" for k in fields)
        values     = list(fields.values()) + [session["user_id"]]

        conn = connect_db()
        conn.execute(f"UPDATE users SET {set_clause} WHERE id=?", values)
        conn.commit()
        conn.close()

        flash("Profile updated!", "success")
        return redirect(url_for("profile"))

    def val(col, default=""):
        return row[col] if row and row[col] is not None else default

    return render_template(
        "edit_profile.html",
        years            = years,
        subjects         = subjects,
        current_year     = val("year"),
        current_major    = val("major"),
        second_major     = val("second_major"),
        minor            = val("minor"),
        advisor_name     = val("advisor_name"),
        advisor_email    = val("advisor_email"),
        expected_grad_term = val("expected_grad_term"),
        admit_term       = val("admit_term"),
        gpa              = val("gpa"),
        units            = val("units")
    )

# ---------- API: /api/courses ----------------------------------------------
@app.route("/api/courses", methods=["GET"])
def api_courses():
    # pagination
    page         = max(request.args.get("page", 1, type=int), 1)
    per_page_req = request.args.get("per_page", 20, type=int)
    PER_PAGE_MAX = 200
    per_page     = max(1, min(per_page_req, PER_PAGE_MAX))
    offset       = (page - 1) * per_page

    # filters
    subject   = request.args.get("subject", "").strip()
    professor = request.args.get("professor", "").strip()
    raw_aok   = request.args.getlist("aok")
    raw_moi   = request.args.getlist("moi")
    min_nbr   = request.args.get("min_nbr", type=int)
    max_nbr   = request.args.get("max_nbr", type=int)
    location_filter = request.args.get("location", "").strip()
    schedule_filter = request.args.get("schedule",     "").strip()


    aok_codes = normalize_codes(raw_aok)
    moi_codes = normalize_codes(raw_moi)

    where, params = [], []
    if subject:
        where.append("c.subject=?");                   params.append(subject)
    for a in aok_codes:
        where.append("ca.curriculum_areas_of_knowledge LIKE ?"); params.append(f"%({a})%")
    for m in moi_codes:
        where.append("ca.curriculum_modes_of_inquiry LIKE ?");   params.append(f"%({m})%")
    if professor:
        where.append("i.name_display LIKE ?");        params.append(f"%{professor}%")
    if min_nbr is not None:
        where.append("CAST(c.catalog_nbr AS INTEGER) >= ?"); params.append(min_nbr)
    if max_nbr is not None:
        where.append("CAST(c.catalog_nbr AS INTEGER) <= ?"); params.append(max_nbr)
    if location_filter:
        where.append("mp.ssr_mtg_loc_long LIKE ?")
        params.append(f"%{location_filter}%")
    if schedule_filter:
        where.append("mp.ssr_mtg_sched_long LIKE ?")
        params.append(f"%{schedule_filter}%")

    where_sql = " WHERE " + " AND ".join(where) if where else ""

    count_sql = f"""
        SELECT COUNT(DISTINCT c.crse_id)
        FROM courses c
        LEFT JOIN class_listings cl ON c.crse_id = cl.crse_id
        LEFT JOIN meeting_patterns mp ON cl.class_id = mp.class_id
        LEFT JOIN course_offerings co ON c.crse_id = co.crse_id
        LEFT JOIN course_attributes ca ON co.offering_id = ca.offering_id
        LEFT JOIN instructors i ON cl.class_id = i.class_id
        {where_sql}
    """

    data_sql = f"""
        SELECT
            c.crse_id AS id,
            c.subject,
            c.catalog_nbr,
            c.course_title_long AS title,
            GROUP_CONCAT(DISTINCT mp.ssr_mtg_sched_long) AS schedule,
            GROUP_CONCAT(DISTINCT mp.ssr_mtg_loc_long) AS location,
            GROUP_CONCAT(DISTINCT i.name_display) AS professors,
            MAX(pr.avg_rating) AS best_prof_rating
        FROM courses c
        LEFT JOIN class_listings   cl ON c.crse_id = cl.crse_id
        INNER JOIN meeting_patterns mp
            ON cl.class_id = mp.class_id
            AND mp.ssr_mtg_sched_long IS NOT NULL
        LEFT JOIN course_offerings co ON c.crse_id = co.crse_id
        LEFT JOIN course_attributes ca ON co.offering_id = ca.offering_id
        LEFT JOIN instructors i ON cl.class_id = i.class_id
        LEFT JOIN professor_ratings pr ON i.name_display = pr.professor
        {where_sql}
        GROUP BY c.crse_id
        ORDER BY 
            COALESCE(MAX(pr.avg_rating), -1) DESC,
            c.subject,
            CAST(c.catalog_nbr AS INTEGER)
        LIMIT ? OFFSET ?
    """

    conn   = _get_conn()
    total  = conn.execute(count_sql, params).fetchone()[0]
    rows   = conn.execute(data_sql, params + [per_page, offset]).fetchall()
    conn.close()

    return jsonify({
        "page":        page,
        "per_page":    per_page,
        "total":       total,
        "total_pages": (total + per_page - 1) // per_page,
        "courses":     [dict(r) for r in rows]
    })

# ---------- API: /api/course/<id> ------------------------------------------
@app.route("/api/course/<course_id>", methods=["GET"])
def api_course_detail(course_id):
    sql = """
    SELECT
        c.crse_id AS id,
        c.subject,
        c.catalog_nbr,
        c.course_title_long AS title,
        ca.curriculum_areas_of_knowledge AS aok,
        ca.curriculum_modes_of_inquiry   AS moi,
        GROUP_CONCAT(DISTINCT i.name_display) AS professors
    FROM courses c
    LEFT JOIN class_listings   cl ON c.crse_id = cl.crse_id
    LEFT JOIN course_offerings co ON c.crse_id = co.crse_id
    LEFT JOIN course_attributes ca ON co.offering_id = ca.offering_id
    LEFT JOIN instructors      i  ON cl.class_id = i.class_id
    WHERE c.crse_id = ?
    GROUP BY c.crse_id
    """
    conn = _get_conn()
    row  = conn.execute(sql, (course_id,)).fetchone()
    conn.close()
    if row:
        return jsonify(dict(row))
    return jsonify({"error": "Course not found"}), 404

# ---------- API: /api/departments ------------------------------------------
@app.route("/api/departments", methods=["GET"])
def api_departments():
    conn = _get_conn()
    rows = conn.execute(
        "SELECT DISTINCT subject FROM courses ORDER BY subject"
    ).fetchall()
    conn.close()
    return jsonify([{"code": r["subject"], "name": r["subject"]} for r in rows])

# ---------- API: /api/professors -------------------------------------------
@app.route("/api/professors", methods=["GET"])
def api_professors():
    query_text = request.args.get("query", "").strip()
    conn = _get_conn()
    sql = """
    SELECT DISTINCT
      i.name_display AS professor,
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
    return jsonify([dict(r) for r in rows])

# ---------- API: /api/reviews ----------------------------------------------
@app.route("/api/reviews", methods=["GET", "POST"])
def api_reviews():
    # POST: submit a new review
    if request.method == "POST":
        data        = request.get_json()
        course_id   = data.get("course_id")
        review_text = data.get("review_text")
        rating      = data.get("rating")
        difficulty  = data.get("difficulty")
        user_id     = session.get("user_id")
        timestamp   = datetime.datetime.now().isoformat()

        if not course_id or not user_id:
            return jsonify({"error": "course_id and user_id are required"}), 400

        conn = connect_db()
        conn.execute(
            """
            INSERT INTO reviews
               (course_id, user_id, review_text, rating, difficulty, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (course_id, user_id, review_text, rating, difficulty, timestamp)
        )
        conn.commit()
        conn.close()

        return jsonify({"success": True}), 201

    # GET: fetch reviews (optionally filtered by course_id)
    course_id = request.args.get("course_id")

    # Use _get_conn so we get sqlite3.Row objects
    conn = _get_conn()
    if course_id:
        cursor = conn.execute(
            """
            SELECT id, course_id, user_id, review_text,
                   rating, difficulty, timestamp
              FROM reviews
             WHERE course_id = ?
             ORDER BY timestamp DESC
            """,
            (course_id,)
        )
    else:
        cursor = conn.execute(
            """
            SELECT id, course_id, user_id, review_text,
                   rating, difficulty, timestamp
              FROM reviews
             ORDER BY timestamp DESC
            """
        )
    rows = cursor.fetchall()
    conn.close()

    # Build a list of dicts by iterating over sqlite3.Row.keys()
    reviews = []
    for row in rows:
        review = {}
        for col in row.keys():
            review[col] = row[col]
        reviews.append(review)

    return jsonify(reviews)


# ---------- API: Favorites --------------------------------------------------
@app.route("/api/favorites", methods=["GET"])
@login_required
def api_favorites_get():
    user_id = session["user_id"]
    conn = _get_conn()
    fav_ids = [r["course_id"] for r in conn.execute(
        "SELECT course_id FROM favorites WHERE user_id=?", (user_id,)
    ).fetchall()]
    conn.close()
    if not fav_ids:
        return jsonify([])
    placeholders = ",".join("?" * len(fav_ids))
    sql = f"""
    SELECT
        c.crse_id AS id,
        c.subject,
        c.catalog_nbr,
        c.course_title_long AS title,
        ca.curriculum_areas_of_knowledge AS aok,
        ca.curriculum_modes_of_inquiry   AS moi,
        GROUP_CONCAT(DISTINCT i.name_display) AS professors
    FROM courses c
    LEFT JOIN course_offerings  co ON c.crse_id = co.crse_id
    LEFT JOIN course_attributes ca ON co.offering_id = ca.offering_id
    LEFT JOIN class_listings    cl ON c.crse_id = cl.crse_id
    LEFT JOIN instructors       i  ON cl.class_id = i.class_id
    WHERE c.crse_id IN ({placeholders})
    GROUP BY c.crse_id
    """
    conn = _get_conn()
    rows = conn.execute(sql, fav_ids).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/favorites", methods=["POST"])
@login_required
def api_favorites_post():
    data      = request.get_json()
    course_id = data.get("course_id")
    user_id   = session["user_id"]
    if not course_id:
        return jsonify({"error": "course_id is required"}), 400
    conn = connect_db()
    try:
        conn.execute(
            "INSERT INTO favorites (user_id, course_id) VALUES (?, ?)",
            (user_id, course_id)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # already favorited
    conn.close()
    return jsonify({"success": True})

@app.route("/api/favorites", methods=["DELETE"])
@login_required
def api_favorites_delete():
    """
    Body JSON: { "course_id": "012345" }
    Removes one favorite row for the logged-in user.
    """
    data       = request.get_json() or {}
    course_id  = data.get("course_id")
    user_id    = session["user_id"]

    if not course_id:
        return jsonify({"error": "course_id is required"}), 400

    conn = connect_db()
    conn.execute(
        "DELETE FROM favorites WHERE user_id=? AND course_id=?",
        (user_id, course_id)
    )
    conn.commit()
    conn.close()

    return jsonify({"success": True})

# ─── Schedule Builder page ──────────────────────────────────────
@app.route("/schedule")
@login_required
def schedule():
    # need the list of subjects (majors) for the dropdown
    conn = connect_db()
    subjects = [r[0] for r in conn.execute("SELECT DISTINCT subject FROM courses ORDER BY subject").fetchall()]
    conn.close()
    return render_template("schedule.html", subjects=subjects)

# ─── Schedule Builder API ───────────────────────────────────────
@app.route("/api/schedule")
@login_required
def api_schedule():
    major = request.args.get("major", "").strip()
    if not major:
        return jsonify({"error":"major is required"}), 400

    sql = """
    SELECT
      c.crse_id                AS id,
      c.catalog_nbr            AS catalog_nbr,
      c.course_title_long      AS title,
      GROUP_CONCAT(DISTINCT mp.ssr_mtg_sched_long) AS schedule,
      MAX(pr.avg_rating)       AS avg_rating
    FROM courses c
    LEFT JOIN class_listings   cl ON c.crse_id = cl.crse_id
    LEFT JOIN meeting_patterns mp
      ON cl.class_id = mp.class_id
      AND mp.ssr_mtg_sched_long IS NOT NULL
    LEFT JOIN instructors     i  ON cl.class_id = i.class_id
    LEFT JOIN professor_ratings pr
      ON i.name_display = pr.professor
    WHERE c.subject = ?
    GROUP BY c.crse_id
    ORDER BY avg_rating DESC
    """

    conn = _get_conn()
    rows = conn.execute(sql, (major,)).fetchall()
    conn.close()

    # pick first 5 courses with unique schedule strings
    selected = []
    seen = set()
    for r in rows:
        sched = r["schedule"]
        if not sched or sched in seen:
            continue
        seen.add(sched)
        selected.append({
            "id":          r["id"],
            "catalog_nbr": r["catalog_nbr"],
            "title":       r["title"],
            "schedule":    sched,
            "avg_rating":  float(r["avg_rating"] or 0)
        })
        if len(selected) == 5:
            break

    return jsonify(selected)


# ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)   # auto-reload in development
