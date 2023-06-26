import sqlite3
import os



# Check if the database file exists
if not os.path.exists('vancouver_database.db'):
    # Connect to the SQLite database (or create if it doesn't exist)
    connie = sqlite3.connect('vancouver_database.db')

    # Create a cursor object to interact with the database
    cur = connie.cursor()

    # Create the table 'daily_vancouver'
    cur.execute("""
        CREATE TABLE daily_vancouver (
            date TEXT,
            brl_rate REAL,
            temperature REAL,
            humidity REAL
        )
    """)

    # Commit the changes and close the connection
    connie.commit()
    connie.close()
else:
    print("Database file 'vancouver_database.db' already exists.")
