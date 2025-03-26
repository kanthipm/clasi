import sqlite3

conn = sqlite3.connect('courses.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(departments)")
print(cursor.fetchall())
conn.close()
