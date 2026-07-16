from dotenv import load_dotenv
import os
from google import genai

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

print("Available Gemini Models:")
print("-" * 50)

for model in client.models.list():
    print(model.name)
