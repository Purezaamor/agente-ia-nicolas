import os
from dotenv import load_dotenv

load_dotenv()

FIELDVIEW_CLIENT_ID = os.getenv("FIELDVIEW_CLIENT_ID")
FIELDVIEW_CLIENT_SECRET = os.getenv("FIELDVIEW_CLIENT_SECRET")
FIELDVIEW_API_KEY = os.getenv("FIELDVIEW_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

FIELDVIEW_AUTH_URL = "https://api.climate.com/api/oauth/authorize"
FIELDVIEW_TOKEN_URL = "https://api.climate.com/api/oauth/token"
FIELDVIEW_API_BASE_URL = "https://api.climate.com/api/v1"