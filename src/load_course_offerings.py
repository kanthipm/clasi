# src/load_course_offerings.py

from src.api_client       import get_all_subjects, get_course_listings, get_course_offering_metadata
from src.db               import create_table, insert_many

# ─── 1. Define your tables ─────────────────────────────────────────────────────
def create_all_tables():
    # Courses
    create_table("courses", {
        "id":           "TEXT PRIMARY KEY",
        "department":   "TEXT",
        "catalog_nbr":  "TEXT",
        "title":        "TEXT",
        "topic_id":     "TEXT",
        "aok":          "TEXT",
        "moi":          "TEXT"
    })
    # Offerings
    create_table("course_offerings", {
        "crse_id":            "TEXT",
        "strm":               "TEXT",
        "catalog_nbr":        "TEXT",
        "title":              "TEXT",
        "description":        "TEXT",
        "grading_basis":      "TEXT",
        "acad_career":        "TEXT",
        "acad_group":         "TEXT",
        "drop_consent":       "TEXT",
        "rqrmnt_group":       "TEXT",
        "components":         "TEXT",
        "curriculum_codes":   "TEXT",
        "PRIMARY KEY (crse_id, strm)": ""
    })
    # Sections
    create_table("sections", {
        "crse_id":   "TEXT",
        "strm":      "TEXT",
        "section":   "TEXT",
        "professor": "TEXT",
        "days":      "TEXT",
        "start_time":"TEXT",
        "end_time":  "TEXT",
        "location":  "TEXT",
        "component": "TEXT",
        "PRIMARY KEY (crse_id, strm, section)": ""
    })

# ─── 2. Parse course‐list response ───────────────────────────────────────────────
def parse_course_list(data, dept_code):
    """
    Turn the JSON from get_course_listings(dept_code)
    into a list of dicts matching the 'courses' table schema.
    """
    rows = []
    for c in data.get("courses", []):
        rows.append({
            "id":          c["id"],
            "department":  dept_code,
            "catalog_nbr": c.get("catalog_nbr", ""),
            "title":       c.get("title_long", ""),
            "topic_id":    c.get("topic_id", ""),
            "aok":         ",".join(c.get("aok", [])),
            "moi":         ",".join(c.get("moi", [])),
        })
    return rows

# ─── 3. Parse offerings + sections ─────────────────────────────────────────────
def parse_offering_and_sections(raw, strm_code):
    """
    Returns a tuple (offering_row, [section_rows...])
    using your existing parse logic plus section extraction.
    """
    # parse the offering itself
    offering = raw \
      .get("ssr_get_course_offering_resp", {}) \
      .get("course_offering_result", {}) \
      .get("course_offering", {})

    # build the offering row
    components = ", ".join(
        c.get("ssr_component","")
        for c in offering.get("course_components",{}) \
                         .get("course_component",[])
    )
    attrs = offering.get("course_attributes",{}) \
                    .get("course_attribute",[])
    codes = ([a.get("crse_attr_value","") for a in attrs]
             if isinstance(attrs,list)
             else [attrs.get("crse_attr_value","")] )

    offering_row = {
        "crse_id":          offering.get("crse_id"),
        "strm":             strm_code,
        "catalog_nbr":      offering.get("catalog_nbr","").strip(),
        "title":            offering.get("course_title_long","").strip(),
        "description":      offering.get("descrlong","").strip(),
        "grading_basis":    offering.get("grading_basis_lov_descr"),
        "acad_career":      offering.get("acad_career_lov_descr"),
        "acad_group":       offering.get("acad_group_lov_descr"),
        "drop_consent":     offering.get("ssr_drop_consent_lov_descr"),
        "rqrmnt_group":     offering.get("rqrmnt_group_descr"),
        "components":       components,
        "curriculum_codes": ",".join(codes),
    }

    # parse sections
    classes = offering.get("classes",{}).get("class",[])
    section_rows = []
    for sec in (classes if isinstance(classes,list) else [classes]):
        section_rows.append({
            "crse_id":   offering.get("crse_id"),
            "strm":      strm_code,
            "section":   sec.get("section",""),
            "professor": sec.get("instructors",[{}])[0].get("instructor",""),
            "days":      sec.get("days",""),
            "start_time":sec.get("start_time",""),
            "end_time":  sec.get("end_time",""),
            "location":  sec.get("location",""),
            "component": sec.get("component","")
        })

    return offering_row, section_rows

# ─── 4. Master loader ──────────────────────────────────────────────────────────
def load_department(dept_code, strm_code="1940"):
    # 4.1 pull & insert courses
    clist = get_course_listings(dept_code)
    courses = parse_course_list(clist, dept_code)
    n1 = insert_many("courses", courses)

    # 4.2 pull & insert offerings + sections
    offs, secs = [], []
    for c in courses:
        raw = get_course_offering_metadata(c["id"], strm_code)
        if not raw: 
            continue
        o, s_rows = parse_offering_and_sections(raw, strm_code)
        offs.append(o)
        secs.extend(s_rows)

    n2 = insert_many("course_offerings", offs)
    n3 = insert_many("sections", secs)

    print(f"✅ {dept_code}: {n1} courses, {n2} offerings, {n3} sections")

# ─── 5. Run it ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    create_all_tables()

    # example: load just CSC to start
    load_department("COMPSCI", strm_code="1940")
    # repeat for other departments as needed
