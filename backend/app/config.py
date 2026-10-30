
import os
from pathlib import Path
from dotenv import load_dotenv

# Find the backend directory regardless of where
# the terminal command is launched.
BACKEND_DIR = Path(__file__).resolve().parent.parent

# Load backend/.env
load_dotenv(BACKEND_DIR / ".env")

# Read the API key securely from the environment.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
