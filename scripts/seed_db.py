import os
import sys

# Add project root to Python path so we can import src.db regardless of working directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db import create_table, insert_many

DB_FILE = "courses.db"

def reset_db():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)


def create_tables():
    create_table("departments", {
        "code": "TEXT PRIMARY KEY",
        "desc": "TEXT"
    })
    create_table("courses", {
        "id": "TEXT PRIMARY KEY",
        "subject": "TEXT",
        "subject_name": "TEXT",
        "catalog_nbr": "TEXT",
        "title": "TEXT",
        "term_code": "TEXT",
        "term_desc": "TEXT",
        "effdt": "TEXT",
        "multi_off": "TEXT",
        "topic_id": "TEXT"
    })
    create_table("course_terms", {
        "crse_id": "TEXT",
        "strm": "TEXT",
        "strm_descr": "TEXT",
        "PRIMARY KEY (crse_id, strm)": ""
    })
    create_table("course_offerings", {
        "crse_id": "TEXT",
        "strm": "TEXT",
        "catalog_nbr": "TEXT",
        "title": "TEXT",
        "description": "TEXT",
        "grading_basis": "TEXT",
        "acad_career": "TEXT",
        "acad_group": "TEXT",
        "drop_consent": "TEXT",
        "rqrmnt_group": "TEXT",
        "components": "TEXT",
        "curriculum_codes": "TEXT",
        "PRIMARY KEY (crse_id, strm)": ""
    })


def seed_data():
    insert_many("departments", [{"code": "CSC", "desc": "Computer Science"}])

    insert_many("courses", [{
        "id": "014361",
        "subject": "CSC",
        "subject_name": "Computer Science",
        "catalog_nbr": "101",
        "title": "Intro to Programming",
        "term_code": "1940",
        "term_desc": "Fall 2025",
        "effdt": "2025-01-01",
        "multi_off": "",
        "topic_id": ""
    }])

    insert_many("course_terms", [{"crse_id": "014361", "strm": "1940", "strm_descr": "Fall 2025"}])

    insert_many("course_offerings", [{
        "crse_id": "014361",
        "strm": "1940",
        "catalog_nbr": "101",
        "title": "Intro to Programming",
        "description": "Learn the basics of Python programming.",
        "grading_basis": "Letter",
        "acad_career": "Undergraduate",
        "acad_group": "UG",
        "drop_consent": "",
        "rqrmnt_group": "",
        "components": "Lecture",
        "curriculum_codes": ""
    }])


def main():
    reset_db()
    create_tables()
    seed_data()
    print(f"✅ Seeded database created at {DB_FILE}")


if __name__ == "__main__":
    main()