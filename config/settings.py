import requests

API_KEY = "YOUR_API_KEY"
BASE_URL = "https://streamer.oit.duke.edu/curriculum"
endpoint = f"{BASE_URL}/list_of_values/fieldname/SUBJECT"

response = requests.get(endpoint, params={"access_token": API_KEY})
data = response.json()  # This should include a list of subjects
