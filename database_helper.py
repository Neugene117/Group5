import sqlite3
from datetime import datetime
from config import DATABASE

def get_db_connection():
    """Create a database connection"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def init_db():
    """Initialize the database"""
    conn = get_db_connection()
    if conn is None:
        return False
    
    try:
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

        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database initialization error: {e}")
        return False
    finally:
        conn.close()

def save_patient_record(patient_data, symptoms, treatment):
    """Save patient record to database"""
    conn = get_db_connection()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO patients (name, age, gender, symptoms, suggested_treatment, test_needed)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            patient_data['name'],
            patient_data['age'],
            patient_data['gender'],
            ','.join(symptoms),
            treatment['recommendation']['action'],
            treatment['score'] >= 6
        ))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error saving patient record: {e}")
        return False
    finally:
        conn.close()

def save_patient_form_data(form_data, assessment_result):
    """Save patient form data to database"""
    conn = get_db_connection()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Insert patient data
        cursor.execute("""
            INSERT INTO patients (
                name, 
                age, 
                gender, 
                symptoms, 
                suggested_treatment, 
                test_needed,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            form_data.get('name'),
            form_data.get('age'),
            form_data.get('gender'),
            ','.join(form_data.getlist('symptoms')),
            assessment_result['recommendation']['action'],
            assessment_result['score'] >= 6
        ))
        
        patient_id = cursor.lastrowid
        conn.commit()
        return patient_id
        
    except sqlite3.Error as e:
        print(f"Error saving patient data: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_recent_patients(limit=10):
    """Get most recent patient records"""
    conn = get_db_connection()
    if conn is None:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM patients 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error fetching recent patients: {e}")
        return []
    finally:
        conn.close()

def get_medications_for_symptoms(symptoms):
    """Get medications for symptoms"""
    conn = get_db_connection()
    if conn is None:
        return []
    
    try:
        cursor = conn.cursor()
        medications = []
        for symptom in symptoms:
            cursor.execute("""
                SELECT symptom, medicine, dosage, 
                       CASE 
                           WHEN symptom IN ('fever', 'chills') THEN 'High priority - Start immediately'
                           WHEN symptom IN ('vomiting', 'sweating') THEN 'Medium priority - Monitor closely'
                           ELSE 'Supportive treatment'
                       END as treatment_recommendation
                FROM medications 
                WHERE LOWER(symptom) = LOWER(?)
            """, (symptom,))
            result = cursor.fetchone()
            if result:
                medications.append({
                    "symptom": result[0],
                    "medicine": result[1],
                    "dosage": result[2],
                    "recommendation": result[3]
                })
        return medications
    except sqlite3.Error as e:
        print(f"Error fetching medications: {e}")
        return []
    finally:
        conn.close()

def get_patient_history(patient_name):
    """Fetch patient's diagnosis history"""
    conn = get_db_connection()
    if conn is None:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM patients 
            WHERE name = ? 
            ORDER BY created_at DESC
        """, (patient_name,))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error fetching patient history: {e}")
        return []
    finally:
        conn.close()
