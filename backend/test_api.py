import requests
from dotenv import load_dotenv
import os

load_dotenv()
key = os.getenv("SERPAPI_KEY")

# Simple test to check if the key is active
url = f"https://serpapi.com/search.json?engine=google&q=coffee&api_key={key}"
response = requests.get(url)

if response.status_code == 200:
    print("✅ Success! Your SerpApi key is working.")
else:
    print(f"❌ Failed! Error {response.status_code}: {response.text}")