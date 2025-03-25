# src/main.py

from .api_client import get_all_subjects

def main():
    print("Starting main...")
    subjects_data = get_all_subjects()
    print("Subjects data:", subjects_data)

    if "error" in subjects_data:
        print("Error:", subjects_data)
        return

    items = subjects_data.get("items", [])
    print(f"Found {len(items)} subject(s).")

    for item in items:
        code = item.get("code")
        desc = item.get("desc")
        print(f"{code} - {desc}")

if __name__ == "__main__":
    main()  
