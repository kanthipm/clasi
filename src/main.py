# src/main.py

from .api_client import get_courses_by_subject


def main():
    # Change the subject as needed; here we use "AAAS" as an example.
    subject = "AAAS"
    courses = get_courses_by_subject(subject)
    print(courses)

if __name__ == "__main__":
    main()
