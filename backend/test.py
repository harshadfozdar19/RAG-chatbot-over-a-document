import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Use a model that your account actually has:
model = genai.GenerativeModel("models/gemini-flash-latest")

response = model.generate_content("Hello! What is 2 + 2?")
print(response.text)
