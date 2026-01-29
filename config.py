"""
Centralized configuration for the video analysis application
"""
import os
import google.genai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY missing in the .env file")

# Global Gemini Client
GEMINI_CLIENT = genai.Client(api_key=API_KEY)

# Model Configuration - Uses the model with prefix models/
GEMINI_MODEL = "models/gemini-2.5-flash"   # ✅ Stable and fast version for video analysis
print(f"✅ Configuration initialized - Model: {GEMINI_MODEL}")