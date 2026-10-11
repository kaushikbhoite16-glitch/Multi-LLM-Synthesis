"""
Non-destructive database migration script:
Safely adds authentication columns to `users` and history metadata to `queries`.
Preserves all existing tables, rows, constraints, and data.
"""
import sqlite3
import os

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "multi_llm.db"))

def migrate():
    print(f"Connecting to database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    def add_column_if_not_exists(table: str, column: str, col_type: str):
        columns = [row[1] for row in cursor.execute(f"PRAGMA table_info({table})").fetchall()]
        if column not in columns:
            print(f"Adding column '{column}' to table '{table}'...")
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        else:
            print(f"Column '{column}' already present in '{table}'.")

    # Add columns to users table
    add_column_if_not_exists("users", "email", "VARCHAR(255)")
    add_column_if_not_exists("users", "hashed_password", "VARCHAR(255)")
    add_column_if_not_exists("users", "full_name", "VARCHAR(255)")
    add_column_if_not_exists("users", "google_id", "VARCHAR(255)")
    add_column_if_not_exists("users", "reset_token", "VARCHAR(255)")
    add_column_if_not_exists("users", "reset_token_expiry", "DATETIME")
    add_column_if_not_exists("users", "is_active", "BOOLEAN DEFAULT 1")
    add_column_if_not_exists("users", "updated_at", "DATETIME")

    # Add columns to queries table
    add_column_if_not_exists("queries", "title", "VARCHAR(255)")
    add_column_if_not_exists("queries", "execution_mode", "VARCHAR(50) DEFAULT 'live'")
    add_column_if_not_exists("queries", "updated_at", "DATETIME")

    # Create index on users email if not exists
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users(email) WHERE email IS NOT NULL")

    conn.commit()
    conn.close()
    print("Database migration completed safely and successfully!")

if __name__ == "__main__":
    migrate()
