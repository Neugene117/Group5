import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'malaria.db')

def setup_database():
    # Connect to SQLite database (or create if it doesn't exist)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create patients table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        gender TEXT NOT NULL,
        symptoms TEXT NOT NULL,
        suggested_treatment TEXT NOT NULL,
        test_needed BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create medications table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS medications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symptom TEXT NOT NULL,
        medicine TEXT NOT NULL,
        dosage TEXT NOT NULL
    )
    ''')

    # Check if medications table is empty before inserting
    cursor.execute("SELECT COUNT(*) FROM medications")
    if cursor.fetchone()[0] == 0:
        # Insert sample medications
        medications = [
            ("fever", "Artemether-Lumefantrine (Coartem)", "4 tablets every 12 hours for 3 days"),
            ("headache", "Paracetamol", "500mg every 8 hours as needed"),
            ("vomiting", "Ondansetron", "4mg every 8 hours if needed"),
            ("fatigue", "Oral Rehydration Solution (ORS)", "Drink 1 sachet in 1 liter of water"),
            ("severe_case", "Artesunate IV", "2.4 mg/kg every 12 hours, then every 24 hours"),
        ]
        
        cursor.executemany(
            "INSERT INTO medications (symptom, medicine, dosage) VALUES (?, ?, ?)", 
            medications
        )

    # Commit and close
    conn.commit()
    conn.close()
    print("Database setup complete!")

if __name__ == "__main__":
    setup_database()
