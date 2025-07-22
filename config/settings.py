import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DUKE_API_TOKEN")
BASE_URL = "https://streamer.oit.duke.edu/curriculum"
endpoint = f"{BASE_URL}/list_of_values/fieldname/SUBJECT"

response = requests.get(endpoint, params={"access_token": API_KEY})
data = response.json()  # This should include a list of subjects
