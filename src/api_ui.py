from flask import Flask, render_template, request, jsonify
from src.db import connect_db  # adjust import based on your project structure

app = Flask(__name__)

@app.route("/")
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
