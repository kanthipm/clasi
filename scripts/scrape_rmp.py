#!/usr/bin/env python3
import os
import sys
import time
import random
import threading
import sqlite3
from itertools import islice
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)
from webdriver_manager.chrome import ChromeDriverManager

# ─── Allow import of your app’s db module ─────────────────────────────────────
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from db import connect_db

DUKE_SCHOOL_ID = "1350"
NUM_WORKERS    = 3      # Number of parallel threads
CHUNK_SIZE     = 200    # Professors per thread (adjust for balance)
DB_PATH        = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                              "..", "courses.db"))

# Lock to serialize SQLite writes
db_lock = threading.Lock()

def init_driver():
    """Create one headless Chrome instance blocking images/stylesheets."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.page_load_strategy = "eager"
    prefs = {
        "profile.managed_default_content_settings.images":      2,
        "profile.managed_default_content_settings.stylesheets": 2,
        "profile.managed_default_content_settings.fonts":       2,
    }
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    driver.set_page_load_timeout(10)
    driver.implicitly_wait(5)
    return driver

def get_text(elem, sel):
    try:
        return elem.find_element(By.CSS_SELECTOR, sel).get_attribute("textContent").strip()
    except NoSuchElementException:
        return None

def scrape_professor(driver, name):
    """Fetch RMP data for one professor using an existing driver."""
    url = f"https://www.ratemyprofessors.com/search/professors/{DUKE_SCHOOL_ID}?q={name.replace(' ','%20')}"
    driver.get(url)
    # click first result
    first = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href^="/professor/"]'))
    )
    first.click()
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
    # overall rating
    raw_rating = get_text(driver, "div[class*='RatingValue__Numerator']")
    # feedback items
    overall_difficulty = None
    would_take = None
    for fb in driver.find_elements(By.CSS_SELECTOR, "div[class*='FeedbackItem__StyledFeedbackItem']"):
        desc = get_text(fb, "div[class*='FeedbackItem__FeedbackDescription']")
        num  = get_text(fb, "div[class*='FeedbackItem__FeedbackNumber']")
        if desc and num:
            d = desc.lower()
            if "difficulty" in d:
                overall_difficulty = num
            elif "would take again" in d:
                would_take = num
    # tags
    tags = ", ".join(
        t.get_attribute("textContent").strip()
        for t in driver.find_elements(
            By.CSS_SELECTOR,
            "div[class*='TeacherTags__TagsContainer'] span.Tag-bs9vf4-0"
        )
    ) or None

    # normalize into DB schema
    try:
        avg_rating = float(raw_rating) if raw_rating else None
    except ValueError:
        avg_rating = None

    try:
        avg_diff = float(overall_difficulty) if overall_difficulty else None
    except ValueError:
        avg_diff = None

    try:
        wta = float(would_take.strip("%")) if would_take else None
    except ValueError:
        wta = None

    return {
        "professor":           name,
        "avg_rating":          avg_rating,
        "avg_difficulty":      avg_diff,
        "would_take_again_pct": wta,
        "tags":                tags,
    }

def init_db():
    """Ensure professor_ratings table exists."""
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("""
      CREATE TABLE IF NOT EXISTS professor_ratings (
        professor            TEXT PRIMARY KEY,
        avg_rating           REAL,
        avg_difficulty       REAL,
        would_take_again_pct REAL,
        tags                 TEXT
      );
    """)
    conn.commit()
    conn.close()

def get_all_professors():
    """Read distinct instructor names from your courses.db."""
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("SELECT DISTINCT name_display FROM instructors")
    names = [r[0] for r in cur.fetchall() if r[0]]
    conn.close()
    return names

def get_scraped_set():
    """Load already-scraped professors from DB."""
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("SELECT professor FROM professor_ratings")
    done = {r[0] for r in cur.fetchall()}
    conn.close()
    return done

def worker_chunk(names_chunk):
    """Each thread runs this: scrape its chunk of names."""
    driver = init_driver()
    for name in names_chunk:
        try:
            data = scrape_professor(driver, name)
        except (TimeoutException, WebDriverException, NoSuchElementException) as e:
            print(f"❌ {name} error: {e}")
            time.sleep(random.uniform(2,5))
            continue
        # write to DB
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cur  = conn.cursor()
            cur.execute("""
              INSERT OR REPLACE INTO professor_ratings
                (professor, avg_rating, avg_difficulty, would_take_again_pct, tags)
              VALUES (?, ?, ?, ?, ?)
            """, (
                data["professor"],
                data["avg_rating"],
                data["avg_difficulty"],
                data["would_take_again_pct"],
                data["tags"]
            ))
            conn.commit()
            conn.close()
            print(f"✅ {name}")
        # polite pause
        time.sleep(random.uniform(1,3))
    driver.quit()

def chunked_iterable(iterable, size):
    """Yield successive chunks from iterable of length size."""
    it = iter(iterable)
    for first in it:
        yield [first] + list(islice(it, size-1))

def main():
    init_db()
    all_names = get_all_professors()
    done      = get_scraped_set()
    pending   = [n for n in all_names if n not in done]
    print(f"🎯 {len(done)} done; {len(pending)} to go (out of {len(all_names)})")

    # split pending into NUM_WORKERS chunks
    chunks = list(chunked_iterable(pending, max(1, len(pending)//NUM_WORKERS)))
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as exe:
        futures = [exe.submit(worker_chunk, chunk) for chunk in chunks]
        for _ in as_completed(futures):
            pass  # errors are printed inside worker

    print("✅ COMPLETE: all professors processed.")

if __name__ == "__main__":
    main()
