# src/load_course_offerings.py
from .api_client import get_course_offering_metadata
from .db import create_table, insert_many


def create_course_offerings_table():
    create_table("course_offerings", {
        "crse_id": "TEXT",
        "strm": "TEXT",
        "catalog_nbr": "TEXT",
        "title": "TEXT",
        "description": "TEXT",
        "grading_basis": "TEXT",
        "acad_career": "TEXT",
        "acad_group": "TEXT",
        "drop_consent": "TEXT",
        "rqrmnt_group": "TEXT",
        "components": "TEXT",
        "curriculum_codes": "TEXT",
        "PRIMARY KEY (crse_id, strm)": ""
    })


def parse_course_offering(data, strm_code):
    offering = data.get("ssr_get_course_offering_resp", {}).get("course_offering_result", {}).get("course_offering", {})

    components = ", ".join(
        c.get("ssr_component", "") for c in offering.get("course_components", {}).get("course_component", [])
    )

    attributes_raw = offering.get("course_attributes", {}).get("course_attribute")
    if isinstance(attributes_raw, list):
        codes = [a.get("crse_attr_value", "") for a in attributes_raw]
    elif isinstance(attributes_raw, dict):
        codes = [attributes_raw.get("crse_attr_value", "")]
    else:
        codes = []

    return {
        "crse_id": offering.get("crse_id"),
        "strm": strm_code,  # passed in from outer function
        "catalog_nbr": offering.get("catalog_nbr", "").strip(),
        "title": offering.get("course_title_long", "").strip(),
        "description": offering.get("descrlong", "").strip(),
        "grading_basis": offering.get("grading_basis_lov_descr"),
        "acad_career": offering.get("acad_career_lov_descr"),
        "acad_group": offering.get("acad_group_lov_descr"),
        "drop_consent": offering.get("ssr_drop_consent_lov_descr"),
        "rqrmnt_group": offering.get("rqrmnt_group_descr"),
        "components": components,
        "curriculum_codes": ", ".join(codes)
    }


# Example loader
if __name__ == "__main__":
    create_course_offerings_table()

    # Replace with your own crse_id and strm from earlier
    crse_id = "014361"
    strm_code = "1940"  # Fall 2025
    data = get_course_offering_metadata(crse_id, strm_code)

    if data:
        parsed = parse_course_offering(data, strm_code)
        inserted = insert_many("course_offerings", [parsed])
        print(f"✅ Inserted {inserted} course offering for {crse_id} in term {strm_code}")
