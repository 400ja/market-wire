import os
import requests
from dotenv import load_dotenv

load_dotenv()  # reads your .env file

response = requests.get(
    "https://newsapi.org/v2/top-headlines",
    params={"category": "business", "country": "us"},
    headers={"X-Api-Key": os.getenv("NEWSAPI_KEY")},
    timeout=10,
)

print(response.status_code)
data = response.json()
print(data)