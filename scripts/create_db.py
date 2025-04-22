
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
from src.db import create_table, insert_many

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
    # columns will be added dynamically based on crse_attr_lov_descr values
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
# Build DB Content
# --------------
subjects = get_all_subjects()["scc_lov_resp"]["lovs"]["lov"]["values"]["value"]
terms = get_all_terms()["scc_lov_resp"]["lovs"]["lov"]["values"]["value"]
# ===== DEBUG MODE: find first real classes payload =====
subject_code = subjects[0]["code"]
course_list = (
    get_course_listings(subject_code)
    ["ssr_get_courses_resp"]["course_search_result"]
    ["subjects"]["subject"]["course_summaries"]["course_summary"]
)

# Try first 5 courses, and for each try the first 5 terms
for course in course_list[:5]:
    crse_id = course["crse_id"]
    for term in terms[:5]:
        strm = term["code"]
        print(f"🔍 Testing {crse_id} @ term {strm}…", end=" ")
        offering_data = get_course_offering_metadata(strm, crse_id)
        sr = offering_data.get("ssr_get_classes_resp", {})\
                          .get("search_result", {})
        subs = sr.get("subjects")
        if subs:
            print("✅ FOUND subjects!")
            print("Raw JSON:\n", offering_data)
            import sys; sys.exit()
        else:
            print("none")
print("🚫 No real sections found in first 5×5 scan")
import sys; sys.exit()


courses_seen = set()
course_rows = []
offering_rows = []
attributes_rows = []
class_rows = []
meeting_rows = []
instructor_rows = []

attribute_columns = set()

for subject in subjects:
    subject_code = subject["code"]
    #print(f"\n📘 Subject: {subject_code}")
    courses = get_course_listings(subject_code)

    try:
        course_list = (
            courses["ssr_get_courses_resp"]
                    ["course_search_result"]
                    ["subjects"]
                    ["subject"]
                    ["course_summaries"]
                    ["course_summary"]          # ← actual list
        )
    except KeyError:
        #print(f"⚠️  Could not find courses array for {subject_code}")
        continue

    #print(f"   ↳ {len(course_list)} courses found")
   
    for course in course_list:
        crse_id = course["crse_id"]
        if not crse_id:
            continue

        if crse_id not in courses_seen:
            course_rows.append({
                "crse_id": crse_id,
                "subject": subject_code,
                "course_title_long": course.get("course_title_long"),
                "catalog_nbr": course.get("catalog_nbr"),
                "ssr_crse_typeoff_cd": course.get("ssr_crse_typeoff_cd")
            })
            courses_seen.add(crse_id)

        for term in terms:
            strm = term["code"]
            # fetch the raw JSON
            offering_data = get_course_offering_metadata(strm, crse_id)

            # drill into the real response path
            result = offering_data.get("ssr_get_classes_resp", {}) \
                                .get("search_result", {})
            subject_data = result.get("subjects", {}) \
                                .get("subject", {})

            # extract the class summaries (could be dict or list)
            summaries = subject_data.get("classes_summary", {}) \
                                    .get("class_summary", [])
            if isinstance(summaries, dict):
                summaries = [summaries]
            if not summaries:
                continue

            for listing in summaries:
                offer_nbr = listing.get("crse_offer_nbr")
                offering_id = f"{crse_id}_{offer_nbr}"

                # build your offering row
                course_offering = {
                    "offering_id":      offering_id,
                    "crse_id":          crse_id,
                    "descrlong":        listing.get("ssr_descrlong"),
                    "consent_lov_descr": listing.get("consent_lov_descr"),
                    "acad_career":      listing.get("acad_career"),
                    "ssr_component":    listing.get("ssr_component")
                }
                offering_rows.append(course_offering)

                # pivot any course_attributes (same as before)
                attr_dict = defaultdict(list)
                for attr in listing.get("course_attributes", []):
                    key = attr.get("crse_attr_lov_descr")
                    val = attr.get("crse_attr_value_lov_descr")
                    if key and val:
                        attr_dict[key].append(val)
                        attribute_columns.add(key)
                attributes_rows.append({
                    "offering_id": offering_id,
                    **{k: ", ".join(v) for k, v in attr_dict.items()}
                })

                # class listing
                class_id = f"{offering_id}_{strm}"
                class_rows.append({
                    "class_id":       class_id,
                    "crse_id":        crse_id,
                    "crse_offer_nbr": offer_nbr
                })

                # meeting patterns
                mtgs = subject_data.get("classes_meeting_patterns", {}) \
                                .get("class_meeting_pattern", [])
                if isinstance(mtgs, dict):
                    mtgs = [mtgs]
                for pattern in mtgs:
                    meeting_rows.append({
                        "class_id":         class_id,
                        "ssr_mtg_loc_long": pattern.get("ssr_mtg_loc_long"),
                        "ssr_mtg_sched_long": pattern.get("ssr_mtg_sched_long")
                    })

                # instructors
                instrs = subject_data.get("class_instructors", {}) \
                                    .get("class_instructor", [])
                if isinstance(instrs, dict):
                    instrs = [instrs]
                for instr in instrs:
                    instructor_rows.append({
                        "class_id":     class_id,
                        "name_display": instr.get("name_display"),
                        "last_name":    instr.get("last_name"),
                        "first_name":   instr.get("first_name")
                    })

                time.sleep(0.1)


# --------------
# Finalize Attribute Table Schema
# --------------
from src.db import add_columns_if_missing

dynamic_attr_schema = {col: "TEXT" for col in attribute_columns}
add_columns_if_missing("course_attributes", dynamic_attr_schema)

# --------------
# Insert All Rows
# --------------
insert_many("courses", course_rows)
insert_many("course_offerings", offering_rows)
insert_many("course_attributes", attributes_rows)
insert_many("class_listings", class_rows)
insert_many("meeting_patterns", meeting_rows)
insert_many("instructors", instructor_rows)

print(f"\n✅ Finished building relational database:")
print(f"→ Courses:            {len(course_rows)}")
print(f"→ Course Offerings:   {len(offering_rows)}")
print(f"→ Attributes (pivot): {len(attributes_rows)}")
print(f"→ Class Listings:     {len(class_rows)}")
print(f"→ Meeting Patterns:   {len(meeting_rows)}")
print(f"→ Instructors:        {len(instructor_rows)}")