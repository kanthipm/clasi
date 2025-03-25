# src/api_client.py

import requests
from config.settings import BASE_URL, API_KEY

def get_all_subjects():
    url = f"{BASE_URL}/list_of_values/fieldname/SUBJECT"
    params = {"access_token": API_KEY}
    response = requests.get(url, params=params)
    
    print("Status code:", response.status_code)   # Debug line
    print("Raw response text:", response.text)    # Debug line
    
    if response.ok:
        return response.json()
    else:
        return {"error": response.status_code, "message": response.text}
