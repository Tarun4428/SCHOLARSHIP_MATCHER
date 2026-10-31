import os
import time

from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY was not found.")
    exit()

client = genai.Client(api_key=api_key)

print("Gemini API key loaded successfully.")
print("Testing Gemini...")

for attempt in range(3):
    try:
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents="Say hello to my hackathon project in one short sentence."
        )

        print("\nGemini response:")
        print(response.text)
        break

    except Exception as e:
        print(f"\nAttempt {attempt + 1} failed:")
        print(e)

        if attempt < 2:
            print("Retrying in 5 seconds...")
            time.sleep(5)
        else:
            print("\nGemini is currently unavailable. Try again later.")