from flask import Flask, render_template, request, jsonify, flash
from datetime import datetime
from database_helper import init_db, save_patient_record, get_medications_for_symptoms, get_patient_history, save_patient_form_data, get_recent_patients
from config import SECRET_KEY, DEBUG

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['DEBUG'] = DEBUG

# Initialize database when app starts
with app.app_context():
    init_db()

SYMPTOM_WEIGHTS = {
    'fever': {'weight': 3, 'critical': True},
    'chills': {'weight': 3, 'critical': True},
    'sweating': {'weight': 2, 'critical': False},
    'headache': {'weight': 1, 'critical': False},
    'fatigue': {'weight': 1, 'critical': False},
    'nausea': {'weight': 1, 'critical': False},
    'vomiting': {'weight': 2, 'critical': False},
    'diarrhea': {'weight': 1, 'critical': False},
    'muscle_pain': {'weight': 1, 'critical': False},
    'abdominal_pain': {'weight': 1, 'critical': False}
}

MEDICINE_RECOMMENDATIONS = {
    'HIGH_RISK': {
        'adult': {
            'primary': 'Artemether-lumefantrine',
            'alternative': 'IV Artesunate',
            'dosage': '80mg/480mg twice daily for 3 days',
            'warning': 'Immediate medical attention required. Hospital treatment may be necessary.'
        },
        'child': {
            'primary': 'Artemether-lumefantrine (pediatric)',
            'alternative': 'IV Artesunate (pediatric dose)',
            'dosage': 'Based on body weight - consult physician',
            'warning': 'Pediatric emergency - immediate medical attention required.'
        },
        'pregnant': {
            'primary': 'Quinine + Clindamycin',
            'alternative': 'Artemether-lumefantrine (pregnancy-safe dose)',
            'dosage': 'As prescribed by healthcare provider',
            'warning': 'Urgent obstetric consultation required.'
        }
    },
    'MODERATE_RISK': {
        'adult': {
            'primary': 'Chloroquine',
            'alternative': 'Artemether-lumefantrine',
            'dosage': '1000mg followed by 500mg at 6, 24, and 48 hours',
            'warning': 'Monitor for symptoms worsening.'
        },
        'child': {
            'primary': 'Chloroquine (pediatric)',
            'dosage': '10mg/kg followed by 5mg/kg at 6, 24, and 48 hours',
            'warning': 'Close pediatric monitoring required.'
        },
        'pregnant': {
            'primary': 'Chloroquine (pregnancy-safe)',
            'dosage': 'As prescribed by healthcare provider',
            'warning': 'Regular obstetric monitoring required.'
        }
    },
    'LOW_RISK': {
        'warning': 'Monitor symptoms. Seek medical attention if condition worsens.',
        'preventive': 'Consider prophylactic medication if in endemic area.'
    }
}

MEDICATIONS = {
    'PRIMARY_TREATMENTS': {
        'uncomplicated': {
            'name': 'Artemether-Lumefantrine (Coartem)',
            'dosage': '4 tablets every 12 hours for 3 days',
            'description': 'First-line treatment for uncomplicated malaria',
            'warnings': ['Take with fatty foods for better absorption', 'Complete full course'],
            'side_effects': ['Headache', 'Nausea', 'Dizziness']
        },
        'severe': {
            'name': 'Artesunate IV',
            'dosage': '2.4 mg/kg at 0, 12, 24 hours, then daily',
            'description': 'Emergency treatment for severe malaria',
            'warnings': ['Hospital administration only', 'Requires medical supervision'],
            'side_effects': ['Dizziness', 'Nausea', 'QT prolongation']
        }
    },
    'SUPPORTIVE_TREATMENTS': {
        'fever': {
            'name': 'Paracetamol',
            'dosage': '500-1000mg every 4-6 hours',
            'max_daily': '4000mg'
        },
        'nausea': {
            'name': 'Ondansetron',
            'dosage': '4-8mg every 8 hours',
            'max_daily': '24mg'
        },
        'dehydration': {
            'name': 'Oral Rehydration Solution',
            'dosage': '1 sachet in 1L water',
            'instructions': 'Drink throughout the day'
        }
    }
}

def calculate_risk_level(symptoms, risk_factors, vital_signs):
    risk_score = 0
    critical_symptoms = 0
    
    # Evaluate symptoms
    for symptom in symptoms:
        if symptom in SYMPTOM_WEIGHTS:
            risk_score += SYMPTOM_WEIGHTS[symptom]['weight']
            if SYMPTOM_WEIGHTS[symptom]['critical']:
                critical_symptoms += 1

    # Evaluate risk factors
    if risk_factors.get('travel_history'):
        risk_score += 3
    if risk_factors.get('endemic_area'):
        risk_score += 4
    if risk_factors.get('mosquito_exposure'):
        risk_score += 2
    if risk_factors.get('previous_malaria'):
        risk_score += 2

    # Evaluate vital signs
    temp = float(vital_signs.get('temperature', 37))
    if temp > 38.5:  # High fever
        risk_score += 3
        critical_symptoms += 1
    
    # Calculate percentages
    max_score = 15
    risk_percentage = (risk_score / max_score) * 100
    symptom_percentage = (len(symptoms) / len(SYMPTOM_WEIGHTS)) * 100
    
    return {
        'score': risk_score,
        'critical_symptoms': critical_symptoms,
        'total_possible_symptoms': len(SYMPTOM_WEIGHTS),
        'risk_percentage': risk_percentage,
        'symptom_percentage': symptom_percentage,
        'recommendation': get_recommendation(risk_score, critical_symptoms, symptoms)
    }

def suggest_medications(symptoms, severity, patient_type='adult'):
    medications = {
        'primary': {},
        'supportive': [],
        'warnings': [],
        'instructions': []
    }
    
    # Determine primary treatment
    if severity == 'HIGH_RISK':
        medications['primary'] = MEDICATIONS['PRIMARY_TREATMENTS']['severe']
        medications['warnings'].append('URGENT: Seek immediate medical attention')
    else:
        medications['primary'] = MEDICATIONS['PRIMARY_TREATMENTS']['uncomplicated']
    
    # Add supportive treatments
    if 'fever' in symptoms:
        medications['supportive'].append(MEDICATIONS['SUPPORTIVE_TREATMENTS']['fever'])
    if 'nausea' in symptoms or 'vomiting' in symptoms:
        medications['supportive'].append(MEDICATIONS['SUPPORTIVE_TREATMENTS']['nausea'])
        medications['supportive'].append(MEDICATIONS['SUPPORTIVE_TREATMENTS']['dehydration'])
    
    # Add general instructions
    medications['instructions'] = [
        'Complete the full course of medication',
        'Take medication with food unless otherwise specified',
        'Return for follow-up in 3 days',
        'Seek immediate medical attention if symptoms worsen'
    ]
    
    return medications

def get_recommendation(risk_score, critical_symptoms, symptoms):
    if risk_score >= 10 or critical_symptoms >= 2:
        recommendation = {
            'level': 'HIGH_RISK',
            'action': 'Immediate malaria testing required.',
            'tests': ['Rapid Diagnostic Test (RDT)', 'Blood Smear Microscopy'],
            'urgency': 'Urgent medical attention recommended'
        }
    elif risk_score >= 6:
        recommendation = {
            'level': 'MODERATE_RISK',
            'action': 'Malaria testing recommended',
            'tests': ['Rapid Diagnostic Test (RDT)'],
            'urgency': 'Schedule testing within 24 hours'
        }
    else:
        recommendation = {
            'level': 'LOW_RISK',
            'action': 'Monitor symptoms',
            'tests': [],
            'urgency': 'No immediate testing required'
        }
    
    # Add medicine recommendations
    recommendation['medicines'] = MEDICINE_RECOMMENDATIONS.get(recommendation['level'], {})
    recommendation['medicines']['disclaimer'] = (
        "⚠️ These are general guidelines only. Always consult a healthcare "
        "professional before starting any medication. Proper diagnosis and "
        "treatment by a qualified physician is essential."
    )
    
    # Add medication suggestions
    recommendation['medications'] = suggest_medications(
        symptoms=symptoms,
        severity=recommendation['level']
    )
    
    return recommendation

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/evaluate', methods=['POST'])
def evaluate():
    data = request.form
    symptoms = request.form.getlist('symptoms')
    
    # Create risk_factors dictionary
    risk_factors = {
        'endemic_area': 'endemic_area' in data,
        'travel_history': 'travel_history' in data,
        'mosquito_exposure': 'mosquito_exposure' in data,
        'previous_malaria': 'previous_malaria' in data
    }
    
    # Calculate assessment
    assessment = calculate_risk_level(
        symptoms,
        risk_factors,
        {
            'temperature': data.get('temperature', '37'),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    )
    
    # Save to database
    patient_id = save_patient_form_data(data, assessment)
    
    if not patient_id:
        # Handle database error
        flash('Error saving patient data', 'error')
    
    # Get medications
    medications = get_medications_for_symptoms(symptoms)
    if medications:
        assessment['medications'] = medications
    
    return render_template(
        'result.html',
        assessment=assessment,
        symptoms=symptoms,
        patient={
            'id': patient_id,
            'name': data.get('name'),
            'age': data.get('age'),
            'gender': data.get('gender')
        },
        risk_factors=risk_factors,
        vital_signs={
            'temperature': data.get('temperature'),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    )

@app.route('/patients', methods=['GET'])
def view_patients():
    """View recent patients"""
    patients = get_recent_patients()
    
    # Add medications for each patient
    for patient in patients:
        symptoms = patient['symptoms'].split(',')
        patient['medications'] = get_medications_for_symptoms(symptoms)
    
    return render_template('patients.html', patients=patients)

if __name__ == '__main__':
    app.run(debug=True)
