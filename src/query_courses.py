from .db import query

def main():
    print("📚 All ECON courses:")

    results = query("courses", {"subject": "STA"})

    for row in results:
        print(row)

if __name__ == "__main__":
    main()
