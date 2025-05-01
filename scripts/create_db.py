import os, sys, time, re
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
    get_course_details
)
from src.db import create_table, insert_many, add_columns_if_missing

def sql_safe(name: str) -> str:
    """
    Turn arbitrary text into a valid SQLite column name.
      • replace spaces, hyphens, parens, etc. with underscores
      • lower-case everything
      • if it would start with a digit, prefix with “_”
    """
    col = re.sub(r"\W+", "_", name.strip().lower())
    return f"_{col}" if col and col[0].isdigit() else col


def _is_attr_dict(x):
    """Return True only if *x* looks like a course-attribute dict."""
    return isinstance(x, dict) and "crse_attr_lov_descr" in x

def _as_list(node):
    """Return *node* itself if it is already a list,  
    wrap it in a one-element list if it is a dict,  
    or return an empty list if it is None / missing."""
    if node is None:
        return []
    return node if isinstance(node, list) else [node]

def sql_safe(name: str) -> str:
    col = re.sub(r'\W+', '_', name.strip().lower())        # replace non-word chars
    return f"_{col}" if col and col[0].isdigit() else col

# ───── safe nested lookup ───────────────────────────────────
def _dig(node, *keys):
    """
    Traverse `node` (a dict or None) through the given key path.
    If any level is None/missing, return None instead of raising.
    """
    for k in keys:
        if not isinstance(node, dict):
            return None
        node = node.get(k)
    return node

# --------------------
# Create Tables (fresh)
# --------------------
create_table("courses", {
    "crse_id": "TEXT PRIMARY KEY",
    "subject": "TEXT",
    "course_title_long": "TEXT",
    "catalog_nbr": "TEXT",
    "ssr_crse_typoff_cd": "TEXT"
})
create_table("course_offerings", {
    "offering_id": "TEXT PRIMARY KEY",
    "crse_id": "TEXT",
    "descrlong": "TEXT",
    "consent_lov_descr": "TEXT",
    "acad_career": "TEXT",
    "ssr_component": "TEXT"
})
create_table("course_attributes", {"offering_id": "TEXT PRIMARY KEY", "descrlong":"TEXT", "rqrmnt_group_descr":"TEXT"})
create_table("class_listings", {"class_id": "TEXT PRIMARY KEY", "crse_id": "TEXT", "crse_offer_nbr": "TEXT"})
create_table("meeting_patterns", {"class_id": "TEXT",  "class_section": "TEXT", "ssr_mtg_loc_long": "TEXT", "ssr_mtg_sched_long": "TEXT"})
create_table("instructors", {"class_id": "TEXT",  "class_section": "TEXT", "name_display": "TEXT", "last_name": "TEXT", "first_name": "TEXT"})

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
        if "_" in code:
            continue                 # jump to the next subject
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
        for course in clist:
            cid = course.get("crse_id")
            if not cid or cid in courses_seen:
                continue
            # record course
            buffers["courses"].append({
                "crse_id": cid,
                "subject": code,
                "course_title_long": course.get("course_title_long"),
                "catalog_nbr": course.get("catalog_nbr"),
                "ssr_crse_typoff_cd": course.get("ssr_crse_typoff_cd"),
            })
            courses_seen.add(cid)
            #print(f" ✔ Course: {cid}")

            # fetch offerings for the selected term only
            data = get_course_offering_metadata(term_code, cid) or {}
        
            sr = data.get("ssr_get_classes_resp", {}).get("search_result", {})
            subjects_block = sr.get("subjects") or {}
            items = subjects_block.get("subject")
            if isinstance(items, dict): items = [items]
            entries = items or []
            if entries:
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

            # ──────────────────────────────────────────────────────────────
            # 1) attributes that live in the class-listing (unchanged)
            # 2) attributes that live in the course-details endpoint
            #    → guarantees we pick up *every* crse_attr_lov_descr
            # ──────────────────────────────────────────────────────────────
                amap = defaultdict(list)
                src_attrs = _as_list(
                    _dig(lst, "course_attributes", "course_attribute"))

                src_attrs += _as_list(
                    _dig(data,
                        "ssr_get_course_offering_resp",
                        "course_offering_result",
                        "course_offering",
                        "course_attributes",
                        "course_attribute"))

                try:
                    details = get_course_details(cid, off_nbr) or {}
                except Exception as e:
                    print(f"    ⚠️  details call failed for {cid}/{off_nbr}: {e}")
                    details = {}             # always defined so look-ups below succeed

                # ── merge attributes that appear only in the details payload ─────
                src_attrs += _as_list(
                    _dig(
                        details,
                        "ssr_get_course_offering_resp",
                        "course_offering_result",
                        "course_offering",
                        "course_attributes",
                        "course_attribute"
                    )
)
            # build the pivot dict and remember new column names
                for a in _as_list(src_attrs):
                    if not _is_attr_dict(a):
                        continue                        # skip stray strings / nulls

                    k_raw = a["crse_attr_lov_descr"].strip()
                    v_raw = a["crse_attr_value_lov_descr"].strip()
                    if v_raw.lower() == "foreign languages curriculum course":
                        v_raw = "(FL) Foreign Languages"
                    
                    if not (k_raw and v_raw):
                        continue

                    k = sql_safe(k_raw)                # legal SQLite identifier
                    amap[k].append(v_raw)
                    attribute_columns.add(k)

                course_off = (
                    _dig(details,                       # 1️⃣ preferred – full details call
                        "ssr_get_course_offering_resp",
                        "course_offering_result",
                        "course_offering")
                    or
                    _dig(data,                          # 2️⃣ fallback – metadata call
                        "ssr_get_course_offering_resp",
                        "course_offering_result",
                        "course_offering")
                    or {}
                )

                descr_txt = (
                    lst.get("ssr_descrlong")            # value from class-listing
                    or course_off.get("descrlong")      # fallback to course-offering
                )

                prereq_txt = (
                    lst.get("rqrmnt_group_descr")       # present in some class-listings
                    or course_off.get("rqrmnt_group_descr")
                )

                buffers["attrs"].append({
                    "offering_id":          off_id,
                    "descrlong":            descr_txt,
                    "rqrmnt_group_descr":   prereq_txt,
                    **{k: ", ".join(v) for k, v in amap.items()}
                })

            # class listing
                cls_id = f"{off_id}_{term_code}"
                buffers["classes"].append({"class_id": cls_id, "crse_id": cid, "crse_offer_nbr": off_nbr})
            # ------------- meeting patterns  +  instructors -------------
                class_summaries = _as_list(
                    lst.get("classes_summary", {}).get("class_summary")
                )

                for cs in class_summaries:
                    pats = _as_list(_dig(cs, "classes_meeting_patterns", "class_meeting_pattern"))                    

                    for p in pats:
                        # ── meeting row ───────────────────────────────────────
                        buffers["meetings"].append({
                            "class_id":           cls_id,
                            "class_section":      p.get("class_section"), 
                            "ssr_mtg_loc_long":   p.get("ssr_mtg_loc_long"),
                            "ssr_mtg_sched_long": p.get("ssr_mtg_sched_long"),
                        })

                        # ── instructors inside *this* pattern ────────────────
                        for ins in _as_list(
                                    _dig(p, "class_instructors", "class_instructor")   # safe!
                        ):
                            buffers["instructors"].append({
                                "class_id":     cls_id,
                                "class_section":      p.get("class_section"), 
                                "name_display": ins.get("name_display"),
                                "last_name":    ins.get("last_name"),
                                "first_name":   ins.get("first_name"),
                            })
        flush()

except KeyboardInterrupt:
    print("\nInterrupted! Flushing remaining data...")
    flush()
    sys.exit(0)

# final flush
flush()
print(f"\n✅ Finished scrape: {len(courses_seen)} subjects processed, one each.")
