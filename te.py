from dotenv import load_dotenv
import os

load_dotenv()  # MUST be called before os.getenv

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GITHUB_TOKEN:
    print("❌ GITHUB_TOKEN is NOT LOADED")
else:
    print(f"✅ GITHUB_TOKEN loaded: {GITHUB_TOKEN[:10]}...")  # Print partial token
