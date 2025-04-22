# src/main.py
from .dropdown_items import term_list, subj_list, acad_car_list
from .api_client import get_all_subjects
from .db import create_table, insert_many, query

def main():
    ###EXAMPLE FOR HOW GENERALIZABLE FUNCTIONS WORK: creating department table 
    create_table("departments", {
        "code": "TEXT PRIMARY KEY",
        "desc": "TEXT"
    })

    # 2️⃣ Fetch data from your API
    departments_data = get_all_subjects()
    if "error" in departments_data:
        print("API error:", departments_data)
        return

    # 3️⃣ Extract & normalize into list of dicts
    items = (
        departments_data
        .get("scc_lov_resp", {})
        .get("lovs", {})
        .get("lov", {})
        .get("values", {})
        .get("value", [])
    )
    rows = [
        {"code": d["code"], "name": d["desc"]}
        for d in items
        if d.get("code") and d.get("desc")
    ]

    # 4️⃣ Bulk-insert into SQLite
    inserted = insert_many("departments", rows)
    print(f"✅ Inserted {inserted} departments")

    # 5️⃣ Verify by querying and printing all rows
    for code, desc in query("departments"):
        print(f"{code}: {desc}")

if __name__ == "__main__":
    main()  
