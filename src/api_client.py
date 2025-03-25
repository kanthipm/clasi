# src/api_client.py

import requests
from config.settings import BASE_URL, API_KEY

def get_courses_by_subject(subject):
    """
    Fetch courses for the given subject.
    Example: subject="AAAS" to fetch courses for that subject.
    """
    url = f"{BASE_URL}/courses/subject/{subject}"
    params = {"access_token": API_KEY}
    response = requests.get(url, params=params)
    
    if response.ok:
        return response.json()  # Successfully got the data
    else:
        # Handle errors here as needed
        return {"error": response.status_code, "message": response.text}
