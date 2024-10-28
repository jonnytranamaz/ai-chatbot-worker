intent_files = {
            'booking': 'data/booking.yml',
            'doctor': 'data/doctor.yml',
            'clinic': 'data/clinic.yml',
            'hospital': 'data/hospital.yml',
            'symptom': 'data/symptom.yml',
            'consultant': 'data/consultant.yml',
            'patient': '/data/patient.yml',
            'health': 'data/health.yml',
            'domain': 'domain.yml',
            'stories': 'data/stories.yml',
        }
#rasa_url = 'http://localhost:5005'
rasa_url = 'http://192.168.1.45:9003'
change_model_url = f'{rasa_url}/model/'

#inference_url = 'http://localhost:8000'
inference_url = 'http://192.168.1.45:9009'
latest_model_url = f'{inference_url}/api/v1/models/get-latest-model/'
