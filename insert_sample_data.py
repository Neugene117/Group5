import sqlite3
import os
from datetime import datetime, timedelta
import random

DB_PATH = os.path.join(os.path.dirname(__file__), 'malaria.db')

def insert_sample_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Sample symptoms combinations
        symptom_combinations = [
            ['fever', 'headache', 'chills'],
            ['fever', 'sweating', 'nausea'],
            ['headache', 'fatigue', 'muscle_pain'],
            ['fever', 'vomiting', 'chills', 'headache'],
            ['fatigue', 'muscle_pain', 'sweating']
        ]
        
        # Sample patient data
        patients = [
            ('John Doe', 35, 'Male', True, True),
            ('Jane Smith', 28, 'Female', False, True),
            ('Bob Wilson', 45, 'Male', True, False),
            ('Alice Brown', 22, 'Female', False, False),
            ('Charlie Davis', 50, 'Male', True, True)
        ]
        
        # Insert patient records
        for i, (name, age, gender, high_risk, needs_test) in enumerate(patients):
            symptoms = ','.join(symptom_combinations[i])
            treatment = "Immediate medical attention required." if high_risk else "Monitor symptoms"
            
            # Calculate a random timestamp within the last 30 days
            days_ago = random.randint(0, 30)
            timestamp = datetime.now() - timedelta(days=days_ago)
            
            cursor.execute("""
                INSERT INTO patients (
                    name, age, gender, symptoms, 
                    suggested_treatment, test_needed, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                name, age, gender, symptoms,
                treatment, needs_test, timestamp.strftime('%Y-%m-%d %H:%M:%S')
            ))

        # Insert additional medications
        medications = [
            ('malaria', 'Chloroquine', '1000mg followed by 500mg at 6, 24, and 48 hours'),
            ('severe_fever', 'Artemether', '3.2mg/kg on first day, then 1.6mg/kg daily'),
            ('dehydration', 'ORS Solution', '1-2 liters per day'),
            ('pain', 'Ibuprofen', '400mg every 6 hours as needed'),
            ('nausea', 'Metoclopramide', '10mg three times daily')
        ]
        
        cursor.executemany("""
            INSERT INTO medications (symptom, medicine, dosage)
            VALUES (?, ?, ?)
        """, medications)

        conn.commit()
        print("Sample data inserted successfully!")
        
        # Verify data insertion
        cursor.execute("SELECT COUNT(*) FROM patients")
        patient_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM medications")
        medication_count = cursor.fetchone()[0]
        
        print(f"Total patients inserted: {patient_count}")
        print(f"Total medications inserted: {medication_count}")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    insert_sample_data()
