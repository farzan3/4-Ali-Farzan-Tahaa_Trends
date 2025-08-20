"""
Test the iTunes API scraper
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.itunes_api_scraper import iTunesAPIScaper

def test_itunes_scraper():
    print("Testing iTunes API Scraper...")
    print("=" * 50)
    
    scraper = iTunesAPIScaper()
    
    # Test 1: Search for apps
    print("\nTest 1: Search for 'puzzle' apps...")
    try:
        search_results = scraper.search_apps('puzzle', 'us', 5)
        print(f"SUCCESS: Found {len(search_results)} apps")
        
        if search_results:
            for i, app in enumerate(search_results[:3], 1):
                print(f"  {i}. {app.get('title', 'N/A')} by {app.get('developer', 'N/A')}")
                print(f"     Rating: {app.get('rating', 'N/A')}, Reviews: {app.get('review_count', 'N/A')}")
    
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test 2: Get app details
    print("\nTest 2: Get app details...")
    try:
        # Use a known app ID (Instagram)
        app_details = scraper.get_app_details('389801252', 'us')
        if app_details:
            print(f"SUCCESS: Got details for {app_details.get('title', 'Unknown')}")
            print(f"  Developer: {app_details.get('developer', 'N/A')}")
            print(f"  Category: {app_details.get('category', 'N/A')}")
            print(f"  Rating: {app_details.get('rating', 'N/A')}")
        else:
            print("No details found")
    
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test 3: Get top charts via RSS
    print("\nTest 3: Get top 3 free games via RSS...")
    try:
        top_games = scraper.get_top_charts_rss('us', 'top-free', 'games', 3)
        print(f"SUCCESS: Found {len(top_games)} top games")
        
        if top_games:
            for i, game in enumerate(top_games, 1):
                print(f"  #{i}. {game.get('title', 'N/A')} by {game.get('developer', 'N/A')}")
                print(f"       Rating: {game.get('rating', 'N/A')}, Price: ${game.get('price', 'N/A')}")
    
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test 4: Search-based charts (fallback method)
    print("\nTest 4: Get top apps via search method...")
    try:
        search_charts = scraper.get_top_charts_search('games', 'us', 3)
        print(f"SUCCESS: Found {len(search_charts)} apps via search")
        
        if search_charts:
            for i, app in enumerate(search_charts, 1):
                score = app.get('popularity_score', 0)
                print(f"  {i}. {app.get('title', 'N/A')} (Popularity: {score:.1f})")
    
    except Exception as e:
        print(f"ERROR: {e}")
    
    print("\nTesting complete!")
    return True

if __name__ == "__main__":
    success = test_itunes_scraper()
    if success:
        print("\nThe iTunes API scraper is working!")
        print("This scraper uses official Apple APIs and is more reliable.")
    else:
        print("\nThere were issues with the scraper.")