# OLD_db.py
#Department-table specific functions before becoming generalizable

from .api_client import get_all_subjects
import sqlite3

def connect_db():
    conn = sqlite3.connect('courses.db')  # The database file will be 'courses.db'
    return conn

def create_departments_table(): 
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute('''
                CREATE TABLE IF NOT EXISTS departments (
                    code TEXT PRIMARY KEY,
                    desc TEXT
                )
            ''')
        
        conn.commit()
        return "Departments table created (or already exists)."  # Return a success message
    except sqlite3.OperationalError as e:
        return f"Error creating departments table: {e}"
    finally:
        conn.close()

def insert_departments():
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

    conn = connect_db()
    cursor = conn.cursor()
    cursor.executemany(
        '''
        INSERT OR REPLACE INTO departments (code, desc)
        VALUES (?, ?)
        ''',
        department_values
    )
    conn.commit()
    conn.close()
    print(f"Inserted {len(department_values)} departments.")

def query_departments():
    conn = connect_db()
    cursor = conn.cursor()

    # Query all rows from the departments table
    cursor.execute("SELECT * FROM departments")
    rows = cursor.fetchall()

    # Print the rows retrieved from the table
    if rows:
        print("Departments table contents:")
        for row in rows:
            print(row)  # Each row is a tuple
    else:
        print("No data found in the departments table.")

    conn.close()


def create_courses_table():
    conn = connect_db()
    cursor = conn.cursor()
    
    # Create the courses table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY,
            department TEXT,
            course_id TEXT,
            course_name TEXT,
            attributes TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def insert_courses(courses):
    conn = connect_db()
    cursor = conn.cursor()
    
    # Insert the courses data into the SQLite table
    for course in courses:
        cursor.execute('''
            INSERT INTO courses (department, course_id, course_name, attributes)
            VALUES (?, ?, ?, ?)
        ''', 
        (course['department'], course['course_id'], course['course_name'], str(course.get('attributes', ''))))
    
    conn.commit()
    conn.close()

def query_courses(department=None, course_id=None, attributes=None):
    conn = connect_db()
    cursor = conn.cursor()

    # Build the dynamic SQL query based on user input
    query = "SELECT * FROM courses WHERE 1=1"
    params = []
    
    if department:
        query += " AND department = ?"
        params.append(department)
    
    if course_id:
        query += " AND course_id = ?"
        params.append(course_id)
    
    if attributes:
        query += " AND attributes LIKE ?"
        params.append(f"%{attributes}%")
    
    cursor.execute(query, params)
    courses = cursor.fetchall()
    conn.close()
    
    return courses
