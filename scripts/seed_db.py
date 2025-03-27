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
        "name": "TEXT"
    })

    create_table("courses", {
        "id": "TEXT PRIMARY KEY",
        "department": "TEXT",
        "catalog_nbr": "TEXT",
        "title": "TEXT",
        "topic_id": "TEXT"
    })

    create_table("course_offerings", {
        "crse_id": "TEXT",
        "crse_offer_nbr": "TEXT",
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
    insert_many("departments", [{
        "code": "COMPSCI",
        "name": "Computer Science"
    }])

    insert_many("courses", [{
        "id": "014361",
        "department": "CSC",
        "catalog_nbr": "101",
        "title": "Intro to Programming",
        "topic_id": ""
    }])

    insert_many("course_offerings", [{
        "crse_id": "014361",
        "crse_offer_nbr": "1",
        "description": "Learn the basics of Python programming.",
        "grading_basis": "Letter",
        "acad_career": "Undergraduate",
        "acad_group": "UG",
        "drop_consent": "None",
        "rqrmnt_group": "",
        "components": "Lecture",
        "curriculum_codes": "QS"
    }])

    insert_many("sections", [{
        "crse_id": "014361",
        "strm": "1940",
        "section": "001",
        "professor": "Susan Rodger",
        "days": "MWF",
        "start_time": "10:05",
        "end_time": "11:20",
        "location": "LSRC A156",
        "component": "Lecture"
    }])

def main():
    reset_db()
    create_tables()
    seed_data()
    print(f"✅ Seeded database created at {DB_FILE}")

if __name__ == "__main__":
    main()
