
import requests

try:
    response = requests.get("http://localhost:8000/photos/")
    print(f"Status Code: {response.status_code}")
    print(f"JSON: {response.json()}")
except Exception as e:
    print(f"Error connecting to backend: {e}")
