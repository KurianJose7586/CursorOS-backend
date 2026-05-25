import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    OMNIPARSER_PATH = os.getenv("OMNIPARSER_PATH")
    
    HOTKEY = "ctrl+shift+space"
    
    # Primary Model (Gemini)
    PRIMARY_MODEL = "gemini-2.0-flash" 
    
    # Fallback Model (Groq)
    FALLBACK_MODEL = "llama-3.3-70b-versatile"
    
    MAX_TOKENS = 4096

settings = Settings()

if not settings.GOOGLE_API_KEY and not settings.GROQ_API_KEY:
    raise ValueError("Both GOOGLE_API_KEY and GROQ_API_KEY are missing from environment variables.")
