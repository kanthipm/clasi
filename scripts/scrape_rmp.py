#!/usr/bin/env python3
import os
import sys
import re
import time
from tqdm import tqdm

# allow import of your app’s db module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from db import connect_db

# RateMyProfessor-Database-APIs client
import RateMyProfessor_Database_APIs as rmpdb

DUKE_SCHOOL_ID = "1350"  # Duke University on RMP

# regex patterns to parse repr(Professor_Gist)
_PAT_ID          = re.compile(r"Professor_ID *: *(\d+)")
_PAT_AVG_RATING  = re.compile(r"Avg Rating *: *([\d.]+)")
_PAT_AVG_DIFF    = re.compile(r"Avg Difficulty *: *([\d.]+)")
_PAT_NUM_RATINGS = re.compile(r"Num Ratings *: *(\d+)")
_PAT_WOULD_TAKE  = re.compile(r"Would Take Again *: *(-?\d+)")

def parse_professor_repr(prof) -> dict:
    """
    Extract name, ID, and metrics from repr(prof).
    """
    rep = repr(prof)
    # name: between 'Professor(' and first comma
    name = rep.split("Professor(", 1)[1].split(",", 1)[0].strip()
    # id
    m = _PAT_ID.search(rep)
    pid = int(m.group(1)) if m else None
    # metrics
    ar = _PAT_AVG_RATING.search(rep)
    ad = _PAT_AVG_DIFF.search(rep)
    nr = _PAT_NUM_RATINGS.search(rep)
    wt = _PAT_WOULD_TAKE.search(rep)
    return {
        "professor":            name,
        "professor_id":         pid,
        "avg_rating":           float(ar.group(1)) if ar else None,
        "avg_difficulty":       float(ad.group(1)) if ad else None,
        "num_ratings":          int(nr.group(1))   if nr else None,
        "would_take_again_pct": int(wt.group(1))   if wt else None,
    }

def main():
    conn = connect_db()
    cur  = conn.cursor()

    # 1) Ensure the ratings table exists with all columns
    cur.execute("""
    CREATE TABLE IF NOT EXISTS professor_ratings (
        professor            TEXT PRIMARY KEY,
        professor_id         INTEGER,
        avg_rating           REAL,
        avg_difficulty       REAL,
        num_ratings          INTEGER,
        would_take_again_pct INTEGER
    )
    """)
    conn.commit()

    # 2) Add professor_id column if missing (migrate older schemas)
    cols = [row[1] for row in cur.execute("PRAGMA table_info(professor_ratings)").fetchall()]
    if "professor_id" not in cols:
        cur.execute("ALTER TABLE professor_ratings ADD COLUMN professor_id INTEGER")
        conn.commit()

    # 3) Load already-scraped names
    cur.execute("SELECT professor FROM professor_ratings")
    scraped = {r[0] for r in cur.fetchall()}

    # 4) Bulk fetch all professors for Duke
    all_profs = rmpdb.fetch_all_professors_from_a_school(DUKE_SCHOOL_ID)
    print(f"🎯 {len(scraped)} already scraped; {len(all_profs) - len(scraped)} pending of {len(all_profs)} total")

    # 5) Iterate, parse, and upsert
    for prof in tqdm(all_profs, desc="RMP scrape", unit="prof"):
        info = parse_professor_repr(prof)
        name = info["professor"]
        if not name or name in scraped or info["professor_id"] is None:
            continue

        cur.execute("""
        INSERT OR REPLACE INTO professor_ratings
          (professor, professor_id, avg_rating, avg_difficulty, num_ratings, would_take_again_pct)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            name,
            info["professor_id"],
            info["avg_rating"],
            info["avg_difficulty"],
            info["num_ratings"],
            info["would_take_again_pct"]
        ))
        conn.commit()
        scraped.add(name)
        time.sleep(0.01)  # polite pacing

    conn.close()
    print("✅ All done.")

if __name__ == "__main__":
    main()
