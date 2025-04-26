# src/api_client.py

import requests
from config.settings import BASE_URL, API_KEY
import time


def get_all_acad_car():
    url = f"{BASE_URL}/list_of_values/fieldname/ACAD_CAREER"
    params = {"access_token": API_KEY}
    response = requests.get(url, params=params)
   
    #print("Status code:", response.status_code)   # Debug line
    #print("Raw response text:", response.text)    # Debug line
   
    if response.ok:
        return response.json()
    else:
        return {"error": response.status_code, "message": response.text}

def get_all_terms():
    url = f"{BASE_URL}/list_of_values/fieldname/STRM"
    params = {"access_token": API_KEY}
    response = requests.get(url, params=params)
   
    #print("Status code:", response.status_code)   # Debug line
    #print("Raw response text:", response.text)    # Debug line
   
    if response.ok:
        return response.json()
    else:
        return {"error": response.status_code, "message": response.text}

def get_all_subjects():
    url = f"{BASE_URL}/list_of_values/fieldname/SUBJECT"
    params = {"access_token": API_KEY}
    response = requests.get(url, params=params)
   
    #print("Status code:", response.status_code)   # Debug line
    #print("Raw response text:", response.text)    # Debug line
   
    if response.ok:
        return response.json()
    else:
        return {"error": response.status_code, "message": response.text}
   
def get_course_listings(subject_name):
    url = f"{BASE_URL}/courses/subject/{subject_name}"
    params = {"access_token": API_KEY}
   
    response = requests.get(url, params=params)

    # Print the full request URL to verify encoding and structure
    #print("Requesting:", response.url)
    #print("Status code:", response.status_code)
   
    try:
        json_data = response.json()
        #print("✅ Parsed JSON successfully")
        return json_data
    except ValueError:
        #print("❌ Failed to parse JSON. Raw response:")
        #print(response.text)
        return {"error": "Invalid JSON", "message": response.text}


def get_course_offering_metadata(strm, crse_id):
    url = f"{BASE_URL}/classes/strm/{strm}/crse_id/{crse_id}"
    params = {"access_token": API_KEY}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"⚠️  metadata error for {crse_id}@{strm}: {e}")
        return {}

def get_section_details(strm: str, crse_id: str, crse_offer_nbr: str, session_code: str, class_section: str):
    url = f"{BASE_URL}/classes/strm/{strm}/crse_id/{crse_id}/crse_offer_nbr/{crse_offer_nbr}/session_code/{session_code}/class_section/{class_section}"
    params = {"access_token": API_KEY}
    response = requests.get(url, params=params)
   
    #print("Requesting:", response.url)
    if response.ok:
        return response.json()
    else:
        return {"error": response.status_code, "message": response.text}

def get_course_synopsis(strm: str, subject: str, catalog_nbr: str, session_code: str, class_section: str):
    url = f"{BASE_URL}/synopsis/strm/{strm}/subject/{subject}/catalog_nbr/{catalog_nbr}/session_code/{session_code}/class_section/{class_section}"
    params = {"access_token": API_KEY}
    response = requests.get(url, params=params)
   
    #print("Requesting:", response.url)
    if response.ok:
        return response.json()
    else:
        return {"error": response.status_code, "message": response.text}
    
def get_course_details(crse_id, crse_offer_nbr):
    url = f"{BASE_URL}/courses/crse_id/{crse_id}/crse_offer_nbr/{crse_offer_nbr}"
    params = {"access_token": API_KEY}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"⚠️  metadata error for {crse_id}@{crse_offer_nbr}: {e}")
        return {}

