import os
from pathlib import Path
from typing import Dict, Any
import streamlit as st

class Config:
    BASE_DIR = Path(__file__).parent.absolute()
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/hunter_app.db")
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    # Scraping
    SCRAPER_DELAY = float(os.getenv("SCRAPER_DELAY", "1.0"))
    USE_PROXY = os.getenv("USE_PROXY", "false").lower() == "true"
    PROXY_LIST = os.getenv("PROXY_LIST", "").split(",") if os.getenv("PROXY_LIST") else []
    
    # ML Models
    SENTIMENT_MODEL = os.getenv("SENTIMENT_MODEL", "cardiffnlp/twitter-roberta-base-sentiment-latest")
    SIMILARITY_MODEL = os.getenv("SIMILARITY_MODEL", "all-MiniLM-L6-v2")
    
    # App Store Countries
    APP_STORE_COUNTRIES = [
        "us", "gb", "ca", "au", "de", "fr", "jp", "kr", "cn", "br", "in", "ru"
    ]
    
    # Categories
    APP_STORE_CATEGORIES = [
        "games", "entertainment", "education", "lifestyle", "utilities", 
        "business", "productivity", "health-fitness", "social-networking"
    ]
    
    # Steam
    STEAM_API_KEY = os.getenv("STEAM_API_KEY", "")
    
    # Authentication
    JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24
    
    # Streamlit
    PAGE_TITLE = "Hunter - App Discovery Platform"
    PAGE_ICON = "🎯"
    LAYOUT = "wide"
    
    @classmethod
    def get_streamlit_config(cls) -> Dict[str, Any]:
        return {
            "page_title": cls.PAGE_TITLE,
            "page_icon": cls.PAGE_ICON,
            "layout": cls.LAYOUT,
            "initial_sidebar_state": "expanded"
        }

config = Config()