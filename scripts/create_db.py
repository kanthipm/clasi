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

# --------------
# Create Tables
# --------------
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

# --------------
# Build DB Content with progress
# --------------
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
    subject_code = subject.get("code")
    print(f"\n[{subj_idx}/{total_subjects}] Processing subject: {subject_code}")

    resp = get_course_listings(subject_code)
    try:
        course_list = resp["ssr_get_courses_resp"]["course_search_result"]["subjects"]["subject"]["course_summaries"]["course_summary"]
    except (KeyError, TypeError):
        print(f"⚠️  No courses for {subject_code}")
        continue
    print(f"    ↳ Found {len(course_list)} courses")

    for crs_idx, course in enumerate(course_list, start=1):
        crse_id = course.get("crse_id")
        if not crse_id or crse_id in courses_seen:
            continue

        courses_seen.add(crse_id)
        course_rows.append({
            "crse_id": crse_id,
            "subject": subject_code,
            "course_title_long": course.get("course_title_long"),
            "catalog_nbr": course.get("catalog_nbr"),
            "ssr_crse_typeoff_cd": course.get("ssr_crse_typeoff_cd"),
        })
        print(f"      • [{crs_idx}/{len(course_list)}] Course ID: {crse_id}")

        for term in terms:
            strm = term.get("code")
            offering_data = get_course_offering_metadata(strm, crse_id) or {}

            # Safely traverse nested JSON, guarding against None
            classes_resp = offering_data.get("ssr_get_classes_resp") or {}
            search_result = classes_resp.get("search_result") or {}
            subjects_block = search_result.get("subjects") or {}
            subj_data = subjects_block.get("subject") or {}

            # Extract class summaries (can be dict or list)
            summaries = subj_data.get("classes_summary", {}).get("class_summary", [])
            if isinstance(summaries, dict):
                summaries = [summaries]
            if not summaries:
                continue

            for listing in summaries:
                offer_nbr = listing.get("crse_offer_nbr")
                offering_id = f"{crse_id}_{offer_nbr}"
                offering_rows.append({
                    "offering_id": offering_id,
                    "crse_id": crse_id,
                    "descrlong": listing.get("ssr_descrlong"),
                    "consent_lov_descr": listing.get("consent_lov_descr"),
                    "acad_career": listing.get("acad_career"),
                    "ssr_component": listing.get("ssr_component"),
                })

                # Pivot course attributes
                attr_dict = defaultdict(list)
                for attr in listing.get("course_attributes", []) or []:
                    key = attr.get("crse_attr_lov_descr")
                    val = attr.get("crse_attr_value_lov_descr")
                    if key and val:
                        attr_dict[key].append(val)
                        attribute_columns.add(key)
                attributes_rows.append({
                    "offering_id": offering_id,
                    **{k: ", ".join(v) for k, v in attr_dict.items()}
                })

                # Class listings
                class_id = f"{offering_id}_{strm}"
                class_rows.append({
                    "class_id": class_id,
                    "crse_id": crse_id,
                    "crse_offer_nbr": offer_nbr
                })

                # Meeting patterns
                mtgs = subj_data.get("classes_meeting_patterns", {}).get("class_meeting_pattern", [])
                if isinstance(mtgs, dict):
                    mtgs = [mtgs]
                for pattern in mtgs or []:
                    meeting_rows.append({
                        "class_id": class_id,
                        "ssr_mtg_loc_long": pattern.get("ssr_mtg_loc_long"),
                        "ssr_mtg_sched_long": pattern.get("ssr_mtg_sched_long"),
                    })

                # Instructors
                instrs = subj_data.get("class_instructors", {}).get("class_instructor", [])
                if isinstance(instrs, dict):
                    instrs = [instrs]
                for instr in instrs or []:
                    instructor_rows.append({
                        "class_id": class_id,
                        "name_display": instr.get("name_display"),
                        "last_name": instr.get("last_name"),
                        "first_name": instr.get("first_name"),
                    })

                # slight pause to avoid API throttling
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

print(f"\n✅ Done: {len(courses_seen)} courses, {len(offering_rows)} offerings, "
      f"{len(class_rows)} listings, {len(attribute_columns)} attribute columns")
