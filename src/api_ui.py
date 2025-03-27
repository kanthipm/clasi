from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from .db import create_table, insert_many, query, connect_db
from functools import wraps
import sqlite3

app = Flask(__name__)
app.secret_key = "replace_this_with_a_strong_secret"

# 1️⃣ Ensure users table exists
create_table("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
    "username": "TEXT UNIQUE NOT NULL",
    "password_hash": "TEXT NOT NULL"
})

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
        hashed = generate_password_hash(password)
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
        if user and check_password_hash(user[0][3], password):
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
    # Connect to the database
    conn = connect_db()
    cursor = conn.cursor()
    
    # Fetch distinct subjects from the courses table
    cursor.execute("SELECT DISTINCT subject FROM courses")
    rows = cursor.fetchall()
    conn.close()
    
    # Convert rows to a simple list, e.g., ["CSC", "ECON", "MATH"]
    subjects = [row[0] for row in rows]
    
    # Render the index.html template, passing the subjects list
    return render_template("index.html", subjects=subjects)

@app.route("/courses")
def courses_from_db():
    subject = request.args.get("subject", "")
    # Build and execute your SQL query here (as before)
    # For example:
    base_sql = "SELECT * FROM courses"
    filters = []
    params = []
    if subject:
        filters.append("subject = ?")
        params.append(subject)
    if filters:
        base_sql += " WHERE " + " AND ".join(filters)
    
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(base_sql, params)
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        results.append({
            "id": row[0],
            "subject": row[1],
            "subject_name": row[2],
            "catalog_nbr": row[3],
            "title": row[4],
            "term_code": row[5],
            "term_desc": row[6],
            "effdt": row[7],
            "multi_off": row[8],
            "topic_id": row[9]
        })
    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)
