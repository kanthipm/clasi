from .api_client import get_all_acad_car, get_all_subjects, get_all_terms, get_course_listings

def parse_departments(): 
    departments_data = get_all_subjects()
    if "error" in departments_data:
        print("Error:", departments_data)
        return

    # Extract the LIST of department objects
    items = (
        departments_data
        .get('scc_lov_resp', {})
        .get('lovs', {})
        .get('lov', {})
        .get('values', {})
        .get('value', [])
    )

    # Convert each dict → (code, desc) tuple
    department_values = [
        (d.get('code'), d.get('desc')) 
        for d in items 
        if d.get('code') and d.get('desc')
    ]

    return(department_values)

def parse_terms(): 
    terms_data = get_all_terms()
    if "error" in terms_data:
        print("Error:", terms_data)
        return

    # Extract the LIST of department objects
    items = (
        terms_data
        .get('scc_lov_resp', {})
        .get('lovs', {})
        .get('lov', {})
        .get('values', {})
        .get('value', [])
    )

    # Convert each dict → (code, desc) tuple
    term_values = [
        (d.get('code'), d.get('desc')) 
        for d in items 
        if d.get('code') and d.get('desc')
    ]

    return(term_values)

def parse_course_listings():
    listings_data = get_course_listings()
    if "error" in listings_data:
        print("Error:", listings_data)
        return []

    raw = (
        listings_data
        .get("ssr_get_courses_resp", {})
        .get("course_search_result", {})
        .get("subjects", {})
        .get("subject", {})
        .get("course_summaries", {})
        .get("course_summary", [])
    )

    # Normalize to list if it’s a single dict
    courses = raw if isinstance(raw, list) else [raw]

    # Build tuples: (subject, catalog_nbr, course_title_long, ssr_crse_typoff_cd)
    course_values = [
        (
            c.get("subject"),
            c.get("catalog_nbr", "").strip(),
            c.get("course_title_long", "").strip(),
            c.get("ssr_crse_typoff_cd") or ""
        )
        for c in courses
        if c.get("subject") and c.get("catalog_nbr")
    ]

    return course_values