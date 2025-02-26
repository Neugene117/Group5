import os

# Database Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'malaria.db')

# Flask Configuration
SECRET_KEY = 'your-secret-key-here'
DEBUG = True
