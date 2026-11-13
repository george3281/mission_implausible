from pathlib import Path
import os

# try:
#     from dotenv import load_dotenv
# except ImportError:
#     def load_dotenv(*args, **kwargs):
#         return False

from google import genai

load_dotenv(Path(__file__).with_name(".env"))

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

prompt = "Explain how AI works in a few words"
response = client.interactions.create(
    model="gemini-3.8-flash",
    input=prompt,
)

print(response.output_text)