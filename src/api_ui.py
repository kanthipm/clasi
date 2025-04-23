import os
import sqlite3, hashlib, binascii, datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from src.db import create_table, insert_many, query, connect_db
from werkzeug.utils import secure_filename

# Paths
BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, 'static')
UPLOAD_PROFILE_PICS = os.path.join(STATIC_DIR, 'profile_pics')
os.makedirs(UPLOAD_PROFILE_PICS, exist_ok=True)

# Flask setup
app = Flask(__name__, static_folder=STATIC_DIR)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "replace_this_with_getenv_secret_key_soon")
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_PROFILE_PICS

# Database tables
create_table("users", {"id": "INTEGER PRIMARY KEY AUTOINCREMENT", "name": "TEXT NOT NULL", "username": "TEXT UNIQUE NOT NULL", "password_hash": "TEXT NOT NULL", "year": "TEXT", "major": "TEXT"})
create_table("reviews", {"id": "INTEGER PRIMARY KEY AUTOINCREMENT", "course_id": "TEXT NOT NULL", "user_id": "INTEGER NOT NULL", "review_text": "TEXT", "rating": "INTEGER", "timestamp": "TEXT"})
create_table("favorites", {"user_id": "INTEGER", "course_id": "TEXT", "PRIMARY KEY (user_id, course_id)": ""})

# Auth helpers
def hash_password(pw):
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', pw.encode(), salt, 200_000)
    return f"{binascii.hexlify(salt).decode()}:{binascii.hexlify(dk).decode()}"

def verify_password(stored, pw):
    try:
        salt_hex, stored_hash = stored.split(":")
        salt = binascii.unhexlify(salt_hex)
    except ValueError:
        return False
    new_hash = hashlib.pbkdf2_hmac('sha256', pw.encode(), salt, 200_000)
    return binascii.hexlify(new_hash).decode() == stored_hash

# Login decorator
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# Routes\ @app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == 'POST':
        name = request.form['name'].strip()
        username = request.form['username'].strip()
        password = request.form['password']
        hashed = hash_password(password)
        try:
            insert_many('users', [{'name': name, 'username': username, 'password_hash': hashed}])
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already taken.', 'danger')
    return render_template('signup.html')

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        rows = query('users', {'username': username})
        if rows and verify_password(rows[0][3], password):
            session['user_id'] = rows[0][0]
            session['username'] = rows[0][2]
            return redirect(url_for('index'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    conn = connect_db()
    subjects = [r[0] for r in conn.execute('SELECT DISTINCT subject FROM courses').fetchall()]
    conn.close()
    return render_template('index.html', subjects=subjects, current_user_id=session['user_id'])

@app.route('/profile')
@login_required
def profile():
    rows = query('users', {'id': session['user_id']})
    if not rows:
        return redirect(url_for('login'))
    r = rows[0]
    user = {'id': r[0], 'name': r[1], 'username': r[2], 'year': r[4], 'major': r[5]}
    return render_template('profile.html', user=user)

# API: simplified courses without AOK/MOI
@app.route('/api/courses', methods=['GET'])
def api_courses():
    subject = request.args.get('subject', '').strip()
    professor = request.args.get('professor', '').strip()
    conn = connect_db()
    base_sql = '''
      SELECT c.crse_id,
             c.subject,
             c.catalog_nbr,
             c.course_title_long,
             GROUP_CONCAT(DISTINCT i.name_display) AS professors
      FROM courses c
      LEFT JOIN class_listings cl ON c.crse_id = cl.crse_id
      LEFT JOIN instructors i ON cl.class_id = i.class_id
    '''
    clauses, params = [], []
    if subject:
        clauses.append('c.subject = ?')
        params.append(subject)
    if professor:
        clauses.append('i.name_display LIKE ?')
        params.append(f"%{professor}%")
    if clauses:
        base_sql += ' WHERE ' + ' AND '.join(clauses)
    base_sql += ' GROUP BY c.crse_id'
    rows = conn.execute(base_sql, params).fetchall()
    conn.close()
    return jsonify([
        {'id': r[0], 'subject': r[1], 'catalog_nbr': r[2], 'title': r[3], 'professors': r[4]}
        for r in rows
    ])

# API: favorites simple list
@app.route('/api/favorites', methods=['GET','POST','DELETE'])
@login_required
def api_favorites():
    user_id = session['user_id']
    conn = connect_db()
    if request.method == 'GET':
        favs = [r[0] for r in conn.execute('SELECT course_id FROM favorites WHERE user_id = ?', (user_id,)).fetchall()]
        conn.close()
        return jsonify(favs)
    data = request.get_json() or {}
    cid = data.get('course_id')
    if request.method == 'POST':
        try:
            conn.execute('INSERT INTO favorites (user_id, course_id) VALUES (?,?)', (user_id, cid))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        conn.close()
        return jsonify({'success': True})
    # DELETE
    conn.execute('DELETE FROM favorites WHERE user_id = ? AND course_id = ?', (user_id, cid))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=False)
