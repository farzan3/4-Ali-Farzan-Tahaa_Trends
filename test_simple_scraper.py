"""
Simple test for App Store scraper
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_scraper():
    print("Testing App Store Scraper...")
    
    try:
        from app_store_scraper import AppStore
        print("SUCCESS: app-store-scraper library is installed")
        
        # Test basic functionality
        print("\nTesting basic App Store access...")
        app_store = AppStore(country='us')
        
        # Get top 3 free games
        print("Getting top 3 free games...")
        top_games = app_store.top_free(category='games', limit=3)
        print(f"Found {len(top_games)} games: {top_games}")
        
        # Get details for first game
        if top_games:
            print(f"\nGetting details for game ID: {top_games[0]}")
            details = app_store.app_details(top_games[0])
            if details:
                print(f"Game: {details.get('trackName', 'Unknown')}")
                print(f"Developer: {details.get('artistName', 'Unknown')}")
                print(f"Rating: {details.get('averageUserRating', 'N/A')}")
                print(f"Reviews: {details.get('userRatingCount', 'N/A')}")
        
        print("\nSUCCESS: Basic scraper functionality works!")
        return True
        
    except ImportError as e:
        print(f"ERROR: app-store-scraper not available: {e}")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_scraper()
    if success:
        print("\nThe scraper is ready to use!")
    else:
        print("\nPlease install app-store-scraper: pip install app-store-scraper")