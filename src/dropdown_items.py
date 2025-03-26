# src/dropdown_items.py

from .api_client import get_all_subjects, get_all_terms, get_all_acad_car

#Returns full term list for drop down
def term_list(): 
    terms_data = get_all_terms()

    if "error" in terms_data:
        print("Error:", terms_data)
        return

    items = terms_data.get('scc_lov_resp', {}).get('lovs', {}).get('lov', {}).get('values', {}).get('value', [])

    full_term_list = []

    for item in items:
        desc = item.get("desc")

        if desc:
            full_term_list.append(desc)

    print(f"Returning full term list of {len(full_term_list)} items.")
    return(full_term_list)

#Returns full subject list for drop down
def subj_list():
    subjects_data = get_all_subjects()

    if "error" in subjects_data:
        print("Error:", subjects_data)
        return

    items = subjects_data.get('scc_lov_resp', {}).get('lovs', {}).get('lov', {}).get('values', {}).get('value', [])

    full_subj_list = []

    for item in items:
        desc = item.get("desc")
        code = item.get("code")

        if code and desc:
            full_subj_list.append(f"{code} - {desc}")

    print(f"Returning full subject list of {len(full_subj_list)} items.")
    return(full_subj_list)

#Returns full academic career list for drop down
def acad_car_list():
    acad_car_data = get_all_acad_car()

    if "error" in acad_car_data:
        print("Error:", acad_car_data)
        return

    items = acad_car_data.get('scc_lov_resp', {}).get('lovs', {}).get('lov', {}).get('values', {}).get('value', [])

    full_subj_list = []

    for item in items:
        desc = item.get("desc")
        code = item.get("code")

        if code and desc:
            full_subj_list.append(f"{code} - {desc}")

    print(f"Returning full subject list of {len(full_subj_list)} items.")
    return(full_subj_list)