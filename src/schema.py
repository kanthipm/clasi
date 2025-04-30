# src/schema.py
"""
Ensures all tables (and new columns) exist every time the app starts.
Import and call ensure_schema() at the top of any script that touches
the SQLite database so you never lose columns.
"""
from src.db import create_table, add_columns_if_missing

def ensure_schema():
    # base users table (already had these)
    create_table("users", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "name": "TEXT NOT NULL",
        "username": "TEXT UNIQUE NOT NULL",
        "password_hash": "TEXT NOT NULL",
        "year": "TEXT",
        "major": "TEXT"
    })

    # extra profile fields
    add_columns_if_missing("users", {
        "second_major":        "TEXT",
        "minor":               "TEXT",
        "advisor_name":        "TEXT",
        "advisor_email":       "TEXT",
        "expected_grad_term":  "TEXT",
        "admit_term":          "TEXT",
        "gpa":                 "REAL",
        "units":               "REAL",
        "profile_pic_path":    "TEXT"
    })
