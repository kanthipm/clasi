import os, sys, time
from collections import defaultdict

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.api_client import (
    get_all_subjects,
    get_all_terms,
    get_course_listings,
    get_course_offering_metadata,
)
from src.db import create_table, insert_many, add_columns_if_missing

# --------------------
# Create Tables
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

create_table("course_attributes", {
    "offering_id": "TEXT PRIMARY KEY"
})

create_table("class_listings", {
    "class_id": "TEXT PRIMARY KEY",
    "crse_id": "TEXT",
    "crse_offer_nbr": "TEXT"
})

create_table("meeting_patterns", {
    "class_id": "TEXT",
    "ssr_mtg_loc_long": "TEXT",
    "ssr_mtg_sched_long": "TEXT"
})

create_table("instructors", {
    "class_id": "TEXT",
    "name_display": "TEXT",
    "last_name": "TEXT",
    "first_name": "TEXT"
})

# --------------------
# Build DB Content with Progress
# --------------------
subjects = get_all_subjects()["scc_lov_resp"]["lovs"]["lov"]["values"]["value"]
terms = get_all_terms()["scc_lov_resp"]["lovs"]["lov"]["values"]["value"]

total_subjects = len(subjects)
print(f"Starting scrape: {total_subjects} subjects, {len(terms)} terms")

courses_seen = set()
course_rows = []
offering_rows = []
attributes_rows = []
class_rows = []
meeting_rows = []
instructor_rows = []
attribute_columns = set()

for subj_idx, subject in enumerate(subjects, start=1):
    code = subject.get("code")
    print(f"\n[{subj_idx}/{total_subjects}] Subject: {code}")

    resp = get_course_listings(code)
    try:
        course_list = (
            resp["ssr_get_courses_resp"]["course_search_result"]
                ["subjects"]["subject"]["course_summaries"]["course_summary"]
        )
    except (KeyError, TypeError):
        print(f"⚠️  No courses for {code}")
        continue

    if isinstance(course_list, dict):
        course_list = [course_list]
    print(f"   ↳ {len(course_list)} courses")

    for crs_idx, course in enumerate(course_list, start=1):
        crse_id = course.get("crse_id")
        if not crse_id or crse_id in courses_seen:
            continue
        courses_seen.add(crse_id)
        course_rows.append({
            "crse_id": crse_id,
            "subject": code,
            "course_title_long": course.get("course_title_long"),
            "catalog_nbr": course.get("catalog_nbr"),
            "ssr_crse_typeoff_cd": course.get("ssr_crse_typeoff_cd"),
        })
        print(f"      • [{crs_idx}/{len(course_list)}] {crse_id}")

        for term in terms:
            strm = term.get("code")
            data = get_course_offering_metadata(strm, crse_id) or {}

            # Drill into classes
            classes_resp = data.get("ssr_get_classes_resp") or {}
            result = classes_resp.get("search_result") or {}
            subj_block = result.get("subjects") or {}
            subj_items = subj_block.get("subject") or []
            if isinstance(subj_items, dict):
                subj_items = [subj_items]

            for subj_data in subj_items:
                summaries = (subj_data.get("classes_summary", {})
                                    .get("class_summary", []))
                if isinstance(summaries, dict):
                    summaries = [summaries]
                if not summaries:
                    continue

                for listing in summaries:
                    offer_nbr = listing.get("crse_offer_nbr")
                    off_id = f"{crse_id}_{offer_nbr}"
                    offering_rows.append({
                        "offering_id": off_id,
                        "crse_id": crse_id,
                        "descrlong": listing.get("ssr_descrlong"),
                        "consent_lov_descr": listing.get("consent_lov_descr"),
                        "acad_career": listing.get("acad_career"),
                        "ssr_component": listing.get("ssr_component"),
                    })

                    # Attributes pivot
                    ad = defaultdict(list)
                    for attr in listing.get("course_attributes", []) or []:
                        k = attr.get("crse_attr_lov_descr")
                        v = attr.get("crse_attr_value_lov_descr")
                        if k and v:
                            ad[k].append(v)
                            attribute_columns.add(k)
                    attributes_rows.append({"offering_id": off_id, **{k: ", ".join(v) for k, v in ad.items()}})

                    # Class listings
                    cid = f"{off_id}_{strm}"
                    class_rows.append({"class_id": cid, "crse_id": crse_id, "crse_offer_nbr": offer_nbr})

                    # Meeting patterns
                    patterns = subj_data.get("classes_meeting_patterns", {})
                    pats = patterns.get("class_meeting_pattern", [])
                    if isinstance(pats, dict): pats = [pats]
                    for p in pats or []:
                        meeting_rows.append({"class_id": cid, "ssr_mtg_loc_long": p.get("ssr_mtg_loc_long"), "ssr_mtg_sched_long": p.get("ssr_mtg_sched_long")})

                    # Instructors
                    instructors = subj_data.get("class_instructors", {})
                    insts = instructors.get("class_instructor", [])
                    if isinstance(insts, dict): insts = [insts]
                    for inst in insts or []:
                        instructor_rows.append({"class_id": cid, "name_display": inst.get("name_display"), "last_name": inst.get("last_name"), "first_name": inst.get("first_name")})

            time.sleep(0.1)

# Finalize attribute schema
add_columns_if_missing("course_attributes", {col: "TEXT" for col in attribute_columns})

# Bulk insert
insert_many("courses", course_rows)
insert_many("course_offerings", offering_rows)
insert_many("course_attributes", attributes_rows)
insert_many("class_listings", class_rows)
insert_many("meeting_patterns", meeting_rows)
insert_many("instructors", instructor_rows)

print(f"\n✅ Done: {len(courses_seen)} courses, {len(offering_rows)} offerings, {len(class_rows)} listings, {len(attribute_columns)} attribute columns")
