import os, sys, time
from collections import defaultdict

# Remove existing database file to ensure fresh schema
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
db_file = os.path.join(project_root, "courses.db")
if os.path.exists(db_file):
    print(f"🔄 Removing old DB at {db_file}")
    os.remove(db_file)

# Add project root to Python path
sys.path.append(project_root)

from src.api_client import (
    get_all_subjects,
    get_all_terms,
    get_course_listings,
    get_course_offering_metadata,
)
from src.db import create_table, insert_many, add_columns_if_missing

# --------------------
# Create Tables (fresh)
# --------------------
create_table("courses", {
    "crse_id": "TEXT PRIMARY KEY",
    "subject": "TEXT",
    "course_title_long": "TEXT",
    "catalog_nbr": "TEXT",
    "ssr_crse_typeoff_cd": "TEXT"
})
create_table("course_offerings", {
    "offering_id": "TEXT PRIMARY KEY",
    "crse_id": "TEXT",
    "descrlong": "TEXT",
    "consent_lov_descr": "TEXT",
    "acad_career": "TEXT",
    "ssr_component": "TEXT"
})
create_table("course_attributes", {"offering_id": "TEXT PRIMARY KEY"})
create_table("class_listings", {"class_id": "TEXT PRIMARY KEY", "crse_id": "TEXT", "crse_offer_nbr": "TEXT"})
create_table("meeting_patterns", {"class_id": "TEXT", "ssr_mtg_loc_long": "TEXT", "ssr_mtg_sched_long": "TEXT"})
create_table("instructors", {"class_id": "TEXT", "name_display": "TEXT", "last_name": "TEXT", "first_name": "TEXT"})

# --------------------
# Select the most recent term
# --------------------
terms = get_all_terms()["scc_lov_resp"]["lovs"]["lov"]["values"]["value"]
if not terms:
    print("❌ No terms found.")
    sys.exit(1)
latest = terms[-1]
term_code = latest.get("code")
term_name = latest.get("descrlong", term_code)
print(f"🔖 Scraping only most recent term: {term_name} (code {term_code})")

# --------------------
# Build DB Content: one course per subject, flush after each
# --------------------
subjects = get_all_subjects()["scc_lov_resp"]["lovs"]["lov"]["values"]["value"]
print(f"Starting scrape: {len(subjects)} subjects @ {term_name}")

courses_seen = set()
buffers = {"courses": [], "offerings": [], "attrs": [], "classes": [], "meetings": [], "instructors": []}
attribute_columns = set()

# Helper to flush buffers to DB and clear

def flush():
    insert_many("courses", buffers["courses"])
    insert_many("course_offerings", buffers["offerings"])
    add_columns_if_missing("course_attributes", {c: "TEXT" for c in attribute_columns})
    insert_many("course_attributes", buffers["attrs"])
    insert_many("class_listings", buffers["classes"])
    insert_many("meeting_patterns", buffers["meetings"])
    insert_many("instructors", buffers["instructors"])
    print(f"💾 Flushed: {len(buffers['courses'])} courses, {len(buffers['offerings'])} offerings")
    for key in buffers:
        buffers[key].clear()

try:
    for idx, subj in enumerate(subjects, start=1):
        code = subj.get("code")
        print(f"\n[{idx}/{len(subjects)}] Subject: {code}")
        # fetch first course
        resp = get_course_listings(code)
        try:
            clist = resp["ssr_get_courses_resp"]["course_search_result"]["subjects"]["subject"]["course_summaries"]["course_summary"]
            if isinstance(clist, dict): clist = [clist]
        except Exception:
            print(f"⚠️ No courses for {code}")
            continue
        if not clist:
            print(f"⚠️ Empty course list for {code}")
            continue
        course = clist[0]
        cid = course.get("crse_id")
        if not cid or cid in courses_seen:
            print("⏭ Skipping invalid or duplicate course")
            continue
        # record course
        buffers["courses"].append({
            "crse_id": cid,
            "subject": code,
            "course_title_long": course.get("course_title_long"),
            "catalog_nbr": course.get("catalog_nbr"),
            "ssr_crse_typeoff_cd": course.get("ssr_crse_typeoff_cd"),
        })
        courses_seen.add(cid)
        print(f" ✔ Course: {cid}")

        # fetch offerings for the selected term only
        data = get_course_offering_metadata(term_code, cid) or {}
        sr = data.get("ssr_get_classes_resp", {}).get("search_result", {})
        subjects_block = sr.get("subjects") or {}
        items = subjects_block.get("subject")
        if isinstance(items, dict): items = [items]
        entries = items or []
        if not entries:
            print(f" ⚠️ No sections for {cid} in {term_name}")
        else:
            lst = entries[0]
            off_nbr = lst.get("crse_offer_nbr")
            off_id = f"{cid}_{off_nbr}"
            buffers["offerings"].append({
                "offering_id": off_id,
                "crse_id": cid,
                "descrlong": lst.get("ssr_descrlong"),
                "consent_lov_descr": lst.get("consent_lov_descr"),
                "acad_career": lst.get("acad_career"),
                "ssr_component": lst.get("ssr_component"),
            })
            # pivot attributes
            amap = defaultdict(list)
            for a in lst.get("course_attributes", []) or []:
                k = a.get("crse_attr_lov_descr"); v = a.get("crse_attr_value_lov_descr")
                if k and v:
                    amap[k].append(v)
                    attribute_columns.add(k)
            buffers["attrs"].append({
                "offering_id": off_id,
                **{k: ", ".join(v) for k, v in amap.items()}
            })
            # class listing
            cls_id = f"{off_id}_{term_code}"
            buffers["classes"].append({"class_id": cls_id, "crse_id": cid, "crse_offer_nbr": off_nbr})
            # first meeting pattern
            mp = lst.get("classes_meeting_patterns", {}).get("class_meeting_pattern")
            if isinstance(mp, dict): mp = [mp]
            if mp:
                p = mp[0]
                buffers["meetings"].append({
                    "class_id": cls_id,
                    "ssr_mtg_loc_long": p.get("ssr_mtg_loc_long"),
                    "ssr_mtg_sched_long": p.get("ssr_mtg_sched_long")
                })
            # first instructor
            inst = lst.get("class_instructors", {}).get("class_instructor")
            if isinstance(inst, dict): inst = [inst]
            if inst:
                i0 = inst[0]
                buffers["instructors"].append({
                    "class_id": cls_id,
                    "name_display": i0.get("name_display"),
                    "last_name": i0.get("last_name"),
                    "first_name": i0.get("first_name")
                })
        # flush per subject
        flush()

except KeyboardInterrupt:
    print("\nInterrupted! Flushing remaining data...")
    flush()
    sys.exit(0)

# final flush
flush()
print(f"\n✅ Finished scrape: {len(courses_seen)} subjects processed, one each.")
