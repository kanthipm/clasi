import requests

API_KEY = "efd0c684b3f184d564010f4c038868a7"
BASE_URL = "https://streamer.oit.duke.edu/curriculum"
endpoint = f"{BASE_URL}/list_of_values/fieldname/SUBJECT"

response = requests.get(endpoint, params={"access_token": API_KEY})
data = response.json()  # This should include a list of subjects
