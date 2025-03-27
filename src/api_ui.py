from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
import sqlite3, hashlib, os, binascii
from .db import create_table, insert_many, query, connect_db, add_columns_if_missing
from werkzeug.utils import secure_filename


##### IMPORTANT: for final product, replace app.secret_key using os.getenv("SECRET_KEY") for secure protection
#import os
#from flask import Flask
#app = Flask(__name__)
#app.secret_key = os.getenv("SECRET_KEY") or os.urandom(32)

app = Flask(__name__)
app.secret_key = "replace_this_with_getenv_secret_key_soon"

# Configure file upload for profile pictures
app.config['UPLOAD_FOLDER'] = 'static/profile_pics'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


# Ensure users table exists + add year & major columns if missing
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

# Password hashing utilities

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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Login-required decorator

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

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
    return render_template("index.html", subjects=subjects)

@app.route("/courses")
def courses_from_db():
    subject = request.args.get("subject", "")
    sql = "SELECT * FROM courses" + (" WHERE subject = ?" if subject else "")
    params = [subject] if subject else []
    conn = connect_db()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return jsonify([{"id":r[0], "subject":r[1], "subject_name":r[2], "catalog_nbr":r[3], "title":r[4], "term_code":r[5], "term_desc":r[6], "effdt":r[7], "multi_off":r[8], "topic_id":r[9]} for r in rows])

# Update profile route
@app.route("/profile")
@login_required
def profile():
    row = query("users", {"id": session["user_id"]})[0]
    user = {
        "id": row[0], "name": row[1], "username": row[2], "year": row[4], "major": row[5],
        "second_major": row[6], "minor": row[7], "advisor_name": row[8], "advisor_email": row[9],
        "expected_grad_term": row[10], "admit_term": row[11], "gpa": row[12], "units": row[13],
        "profile_pic": row[14]
    }
    return render_template("profile.html", user=user)

@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    row = query("users", {"id": session["user_id"]})[0]
    current = {
        "year": row[4], "major": row[5], "second_major": row[6], "minor": row[7],
        "advisor_name": row[8], "advisor_email": row[9], "expected_grad_term": row[10],
        "admit_term": row[11], "gpa": row[12], "units": row[13], "profile_pic": row[14]
    }

    if request.method == "POST":
        year = request.form["year"]
        major = request.form["major"]
        second_major = request.form.get("second_major")
        minor = request.form.get("minor")
        advisor_name = request.form.get("advisor_name")
        advisor_email = request.form.get("advisor_email")
        expected_grad_term = request.form.get("expected_grad_term")
        admit_term = request.form.get("admit_term")
        gpa = request.form.get("gpa")
        units = request.form.get("units")
        file = request.files.get("profile_pic")

        filename = current["profile_pic"]
        if file and allowed_file(file.filename):
            safe_filename = secure_filename(file.filename)
            filename = f"{session['user_id']}_{safe_filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # ✅ Helpful debug logs
        print("Saving profile pic and fields...")
        print("Received file:", file.filename if file else "No file")
        print("Final saved filename:", filename)

        conn = connect_db()
        conn.execute("""
            UPDATE users SET year=?, major=?, second_major=?, minor=?, advisor_name=?, advisor_email=?,
            expected_grad_term=?, admit_term=?, gpa=?, units=?, profile_pic=? WHERE id=?
        """, (year, major, second_major, minor, advisor_name, advisor_email,
              expected_grad_term, admit_term, gpa, units, filename, session["user_id"]))
        conn.commit()
        conn.close()
        flash("Profile updated!", "success")
        return redirect(url_for("profile"))

    return render_template("edit_profile.html", **current)


if __name__ == "__main__":
    app.run(debug=True)