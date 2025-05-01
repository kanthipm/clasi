#!/usr/bin/env python3
"""
Sequantial, single‐browser RateMyProfessors scraper.
Keeps your machine responsive, resumes on restart,
and writes each result immediately.
"""

import os, sys, time, random, sqlite3, logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, WebDriverException
)
from webdriver_manager.chrome import ChromeDriverManager

# ─── CONFIG ─────────────────────────────────────────────────────────────────────
DUKE_SCHOOL_ID = "1350"
DB_PATH        = os.path.join(os.path.dirname(__file__), "..", "courses.db")
RESTART_EVERY  = 200        # restart browser after this many scrapes
MIN_DELAY      = 1.0        # seconds
MAX_DELAY      = 3.0        # seconds
LOG_LEVEL      = logging.INFO

# ─── LOGGING ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=LOG_LEVEL
)

# ─── DB UTILITIES ───────────────────────────────────────────────────────────────
def connect_db():
    return sqlite3.connect(DB_PATH)

def init_db():
    """Ensure professor_ratings table exists."""
    with connect_db() as conn:
        conn.execute("""
          CREATE TABLE IF NOT EXISTS professor_ratings (
            professor            TEXT PRIMARY KEY,
            avg_rating           REAL,
            avg_difficulty       REAL,
            would_take_again_pct REAL,
            tags                 TEXT
          );
        """)
        conn.commit()

def get_all_professors():
    """Fetch all distinct instructor names from instructors table."""
    with connect_db() as conn:
        cur = conn.execute("SELECT DISTINCT name_display FROM instructors")
        return [r[0] for r in cur.fetchall() if r[0]]

def get_scraped_professors():
    """Fetch the set of professor names already in professor_ratings."""
    with connect_db() as conn:
        cur = conn.execute("SELECT professor FROM professor_ratings")
        return {r[0] for r in cur.fetchall()}

def save_rating(record):
    """Insert or replace one professor record."""
    with connect_db() as conn:
        conn.execute("""
          INSERT OR REPLACE INTO professor_ratings
            (professor, avg_rating, avg_difficulty, would_take_again_pct, tags)
          VALUES (?, ?, ?, ?, ?)
        """, (
            record["professor"],
            record["avg_rating"],
            record["avg_difficulty"],
            record["would_take_again_pct"],
            record["tags"]
        ))
        conn.commit()

# ─── SELENIUM SCRAPERS ─────────────────────────────────────────────────────────
def init_driver():
    """Start a single headless Chrome with images/stylesheets/fonts disabled."""
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless")
    opts.add_argument("--disable-gpu")
    opts.page_load_strategy = "eager"
    prefs = {
        "profile.managed_default_content_settings.images":      2,
        "profile.managed_default_content_settings.stylesheets": 2,
        "profile.managed_default_content_settings.fonts":       2,
    }
    opts.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=opts
    )
    driver.set_page_load_timeout(15)
    driver.implicitly_wait(5)
    return driver

def get_text(elem, css):
    """Safe .find_element + .textContent.strip()."""
    try:
        return elem.find_element(By.CSS_SELECTOR, css).get_attribute("textContent").strip()
    except NoSuchElementException:
        return None

def scrape_professor(driver, name):
    """Navigate to search → click first result → extract ratings & tags."""
    url = f"https://www.ratemyprofessors.com/search/professors/{DUKE_SCHOOL_ID}?q={name.replace(' ','%20')}"
    driver.get(url)

    # 1) find and click first professor link
    first = WebDriverWait(driver, 7).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href^="/professor/"]'))
    )
    first.click()

    # 2) wait for page body
    WebDriverWait(driver, 7).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))

    # 3) extract overall rating
    raw_rating = get_text(driver, "div[class*='RatingValue__Numerator']")

    # 4) extract difficulty + would-take-again
    diff = wta = None
    for fb in driver.find_elements(By.CSS_SELECTOR, "div[class*='FeedbackItem__StyledFeedbackItem']"):
        desc = get_text(fb, "div[class*='FeedbackItem__FeedbackDescription']")
        num  = get_text(fb, "div[class*='FeedbackItem__FeedbackNumber']")
        if desc and num:
            d = desc.lower()
            if "difficulty" in d:
                diff = num
            elif "would take again" in d:
                wta = num

    # 5) extract tags
    tag_elems = driver.find_elements(
        By.CSS_SELECTOR,
        "div[class*='TeacherTags__TagsContainer'] span.Tag-bs9vf4-0"
    )
    tags = ", ".join(t.get_attribute("textContent").strip() for t in tag_elems) or None

    # 6) normalize numeric fields
    try:
        avg_rating = float(raw_rating) if raw_rating else None
    except ValueError:
        avg_rating = None
    try:
        avg_diff   = float(diff) if diff else None
    except ValueError:
        avg_diff = None
    try:
        wta_pct    = float(wta.strip("%")) if wta else None
    except ValueError:
        wta_pct = None

    return {
        "professor":            name,
        "avg_rating":           avg_rating,
        "avg_difficulty":       avg_diff,
        "would_take_again_pct": wta_pct,
        "tags":                 tags,
    }

# ─── MAIN LOOP ────────────────────────────────────────────────────────────────
def main():
    init_db()
    all_names = get_all_professors()
    done      = get_scraped_professors()
    pending   = [n for n in all_names if n not in done]
    total     = len(pending)

    logging.info(f"{len(done)} already scraped; {total} to go.")

    driver = init_driver()
    count = 0

    for idx, name in enumerate(pending, 1):
        try:
            record = scrape_professor(driver, name)
        except (TimeoutException, WebDriverException, NoSuchElementException) as e:
            logging.warning(f"[{idx}/{total}] {name} → SKIPPED ({e.__class__.__name__})")
            # small back-off on failure
            time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
            continue

        save_rating(record)
        count += 1
        logging.info(f"[{idx}/{total}] {name} → {record['avg_rating']} ⭐")

        # polite, randomized pause
        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

        # every RESTART_EVERY scrapes, restart the browser to clear memory
        if count and count % RESTART_EVERY == 0:
            logging.info(f"⟳ Restarting browser after {count} scrapes")
            driver.quit()
            driver = init_driver()

    driver.quit()
    logging.info("✅ All done.")

if __name__ == "__main__":
    main()
