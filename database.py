import mysql.connector
from mysql.connector import Error

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="malaria_system"
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL Database: {e}")
        return None

def init_db():
    """Initialize database tables if they don't exist"""
    conn = get_db_connection()
    if conn is None:
        return
    
    cursor = conn.cursor()
    
    try:
        # Create patients table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                age INT NOT NULL,
                gender ENUM('Male', 'Female') NOT NULL,
                symptoms TEXT NOT NULL,
                suggested_treatment TEXT NOT NULL,
                test_needed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create medications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS medications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                symptom VARCHAR(255) NOT NULL,
                medicine VARCHAR(255) NOT NULL,
                dosage VARCHAR(255) NOT NULL
            )
        """)
        
        # Insert default medications if they don't exist
        cursor.execute("SELECT COUNT(*) FROM medications")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("""
                INSERT INTO medications (symptom, medicine, dosage) VALUES (%s, %s, %s)
            """, [
                ('fever', 'Artemether-Lumefantrine (Coartem)', '4 tablets every 12 hours for 3 days'),
                ('headache', 'Paracetamol', '500mg every 8 hours as needed'),
                ('vomiting', 'Ondansetron', '4mg every 8 hours if needed'),
                ('fatigue', 'Oral Rehydration Solution (ORS)', 'Drink 1 sachet in 1 liter of water'),
                ('severe_case', 'Artesunate IV', '2.4 mg/kg every 12 hours, then every 24 hours')
            ])
        
        conn.commit()
    except Error as e:
        print(f"Error initializing database: {e}")
    finally:
        cursor.close()
        conn.close()
