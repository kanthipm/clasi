from flask import Flask, render_template, request, jsonify
from src.dropdown_items import subj_list, term_list, acad_car_list
from src.api_client import get_course_listings

app = Flask(__name__)

@app.route("/")
def index():
    subjects = subj_list() or []
    terms = term_list() or []
    careers = acad_car_list() or []
    return render_template("index.html", subjects=subjects, terms=terms, careers=careers)

@app.route("/courses")
def courses():
    subject = request.args.get("subject")
    if not subject:
        return jsonify({"error": "Missing subject"}), 400

    # Assuming subject comes in the format "CODE - Description"
    subject_code = subject.split(" - ")[0].strip()
    data = get_course_listings(subject_code)
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)
