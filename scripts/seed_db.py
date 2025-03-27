import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db import create_table, insert_many

DB_FILE = "courses.db"

def reset_db():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

def create_tables():
    create_table("departments", {
        "code": "TEXT PRIMARY KEY",
        "name": "TEXT"
    })

    create_table("courses", {
        "id": "TEXT PRIMARY KEY",
        "department": "TEXT",
        "catalog_nbr": "TEXT",
        "title": "TEXT",
        "topic_id": "TEXT",
        "aok": "TEXT",
        "moi": "TEXT"
    })

    create_table("course_offerings", {
        "crse_id": "TEXT",
        "crse_offer_nbr": "TEXT",
        "strm": "TEXT",
        "description": "TEXT",
        "grading_basis": "TEXT",
        "acad_career": "TEXT",
        "acad_group": "TEXT",
        "drop_consent": "TEXT",
        "rqrmnt_group": "TEXT",
        "components": "TEXT",
        "curriculum_codes": "TEXT",
        "PRIMARY KEY (crse_id, crse_offer_nbr)": ""
    })

    create_table("sections", {
        "crse_id": "TEXT",
        "strm": "TEXT",
        "section": "TEXT",
        "professor": "TEXT",
        "days": "TEXT",
        "start_time": "TEXT",
        "end_time": "TEXT",
        "location": "TEXT",
        "component": "TEXT",
        "PRIMARY KEY (crse_id, strm, section)": ""
    })

def seed_data():
    insert_many("departments", [
        {"code": "CSC", "name": "Computer Science"},
        {"code": "MATH", "name": "Mathematics"},
        {"code": "ENG", "name": "English Literature"},
        {"code": "BIO", "name": "Biology"},
    ])

    # Note: For courses, multiple AOKs/MOIs are stored as comma-separated strings.
    courses = [
        {"id": "CSC101", "department": "CSC", "catalog_nbr": "101", "title": "Intro to Programming", "topic_id": "", "aok": "QS,ALP", "moi": "W"},
        {"id": "CSC201", "department": "CSC", "catalog_nbr": "201", "title": "Data Structures", "topic_id": "", "aok": "QS", "moi": "EI,STS"},
        {"id": "MATH101", "department": "MATH", "catalog_nbr": "101", "title": "Calculus I", "topic_id": "", "aok": "NS", "moi": "STS"},
        {"id": "MATH201", "department": "MATH", "catalog_nbr": "201", "title": "Linear Algebra", "topic_id": "", "aok": "QS", "moi": "W"},
        {"id": "ENG101", "department": "ENG", "catalog_nbr": "101", "title": "English Literature I", "topic_id": "", "aok": "ALP", "moi": "R"},
        {"id": "ENG201", "department": "ENG", "catalog_nbr": "201", "title": "Shakespearean Studies", "topic_id": "", "aok": "ALP,CZ", "moi": "CCI,R"},
        {"id": "BIO101", "department": "BIO", "catalog_nbr": "101", "title": "Intro to Biology", "topic_id": "", "aok": "NS", "moi": "STS"},
        {"id": "BIO201", "department": "BIO", "catalog_nbr": "201", "title": "Genetics", "topic_id": "", "aok": "NS", "moi": "EI"},
    ]
    insert_many("courses", courses)

    offerings = []
    sections = []

    # Map each course ID to a distinct professor name.
    professor_map = {
        "CSC101": "Dr. Alice Johnson",
        "CSC201": "Dr. Bob Williams",
        "MATH101": "Dr. Carol Smith",
        "MATH201": "Dr. David Brown",
        "ENG101": "Dr. Emily Davis",
        "ENG201": "Dr. Frank Miller",
        "BIO101": "Dr. Grace Wilson",
        "BIO201": "Dr. Henry Taylor"
    }

    for course in courses:
        crse = course["id"]
        offerings.append({
            "crse_id": crse,
            "crse_offer_nbr": "1",
            "strm": "FALL2025",
            "description": f"{course['title']} description",
            "grading_basis": "Letter",
            "acad_career": "Undergraduate",
            "acad_group": "UG",
            "drop_consent": "None",
            "rqrmnt_group": "",
            "components": "Lecture",
            "curriculum_codes": course["aok"]
        })
        sections.append({
            "crse_id": crse,
            "strm": "FALL2025",
            "section": "001",
            "professor": professor_map.get(crse, "Dr. Unknown"),
            "days": "MWF",
            "start_time": "09:00",
            "end_time": "10:15",
            "location": "Building A",
            "component": "Lecture"
        })

    insert_many("course_offerings", offerings)
    insert_many("sections", sections)

def main():
    reset_db()
    create_tables()
    seed_data()
    print(f"✅ Seeded database created at {DB_FILE}")

if __name__ == "__main__":
    main()
