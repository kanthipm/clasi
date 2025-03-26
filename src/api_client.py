# src/api_client.py

import requests
from config.settings import BASE_URL, API_KEY

def get_all_acad_car():
    url = f"{BASE_URL}/list_of_values/fieldname/ACAD_CAREER"
    params = {"access_token": API_KEY}
    response = requests.get(url, params=params)
    
    print("Status code:", response.status_code)   # Debug line
    print("Raw response text:", response.text)    # Debug line
    
    if response.ok:
        return response.json()
    else:
        return {"error": response.status_code, "message": response.text}

def get_all_terms():
    url = f"{BASE_URL}/list_of_values/fieldname/STRM"
    params = {"access_token": API_KEY}
    response = requests.get(url, params=params)
    
    print("Status code:", response.status_code)   # Debug line
    print("Raw response text:", response.text)    # Debug line
    
    if response.ok:
        return response.json()
    else:
        return {"error": response.status_code, "message": response.text}

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
    
def get_course_listings(subject_name): 
    url = f"{BASE_URL}/courses/subject/{subject_name}"
    params = {"access_token": API_KEY}
    
    response = requests.get(url, params=params)

    # Print the full request URL to verify encoding and structure
    print("Requesting:", response.url)
    print("Status code:", response.status_code)
    
    try:
        json_data = response.json()
        print("✅ Parsed JSON successfully")
        return json_data
    except ValueError:
        print("❌ Failed to parse JSON. Raw response:")
        print(response.text)
        return {"error": "Invalid JSON", "message": response.text}


