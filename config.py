import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
    MAPBOX_TOKEN = os.getenv("MAPBOX_ACCESS_TOKEN")