import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("API Key is missing in .env file!")
else:
    client = genai.Client(api_key=api_key)
    print("🔍 Searching for available Flash models...")
    try:
        models = client.models.list()
        for m in models:
            if "flash" in m.name:
                # بيطبع الاسم اللي المفروض نستخدمه بالظبط
                print(f"✅ Found: {m.name}")
    except Exception as e:
        print(f"Error: {e}")