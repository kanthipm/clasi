import sqlite3

DB_FILE = "courses.db"

def connect_db() -> sqlite3.Connection:
    """Open (or create) the SQLite database file and return its connection."""
    return sqlite3.connect(DB_FILE)

def create_table(table: str, schema: dict[str, str]) -> None:
    """
    Create a table if it doesn’t exist.

    Args:
      table: Name of the table.
      schema: Mapping of column_name → SQL type/constraints.
                e.g. {"id": "INTEGER PRIMARY KEY", "name": "TEXT NOT NULL"}
    """
    columns_sql = ", ".join(f"{col} {typ}" for col, typ in schema.items())
    sql = f"CREATE TABLE IF NOT EXISTS {table} ({columns_sql})"
    conn = connect_db()
    conn.execute(sql)
    conn.commit()
    conn.close()

def insert_many(table: str, rows: list[dict[str, any]]) -> int:
    """
    Bulk-insert (or replace) a list of dictionaries into the given table.

    Args:
      table: Table name.
      rows: Each dict’s keys must exactly match table column names.

    Returns:
      Number of rows inserted.
    """
    if not rows:
        return 0

    cols = list(rows[0].keys())
    placeholders = ", ".join("?" for _ in cols)
    sql = f"INSERT OR REPLACE INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"
    values = [tuple(row[col] for col in cols) for row in rows]

    conn = connect_db()
    conn.executemany(sql, values)
    conn.commit()
    conn.close()
    return len(values)

def query(table: str, filters: dict[str, any] | None = None) -> list[tuple]:
    """
    SELECT * FROM table with optional equality filters.

    Args:
      table: Table name.
      filters: Optional dict of {column: value} for WHERE clauses.

    Returns:
      List of result tuples.
    """
    sql = f"SELECT * FROM {table}"
    params = []

    if filters:
        clauses = [f"{col} = ?" for col in filters]
        sql += " WHERE " + " AND ".join(clauses)
        params = list(filters.values())

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    return rows
