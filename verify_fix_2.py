import urllib.request
import json

def verify_weeks():
    try:
        url = "http://localhost:8000/api/v1/test-weeks/"
        with urllib.request.urlopen(url) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                weeks = data.get("weeks", [])
                print(f"Found {len(weeks)} weeks.")
                for week in weeks:
                    print(f"Week: {week['name']}, Word Count: {week['word_count']}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    verify_weeks()
