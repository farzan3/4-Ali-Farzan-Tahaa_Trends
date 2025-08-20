"""
Test script for the new App Store scraper using app-store-scraper library
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.appstore_scraper_new import AppStoreScraperNew
import json
from datetime import datetime

def test_basic_functionality():
    """Test basic scraper functionality"""
    print("Testing App Store Scraper with app-store-scraper library")
    print("=" * 60)
    
    scraper = AppStoreScraperNew()
    
    # Test 1: Get top free games
    print("\nTest 1: Getting top 5 free games in US...")
    try:
        top_games = scraper.get_top_charts('us', 'games', 'top_free', 5)
        print(f"Success: Found {len(top_games)} top free games")
        
        if top_games:
            print("\nSample app data:")
            sample_app = top_games[0]
            print(f"  • Title: {sample_app.get('title', 'N/A')}")
            print(f"  • Developer: {sample_app.get('developer', 'N/A')}")
            print(f"  • Rating: {sample_app.get('rating', 'N/A')}")
            print(f"  • Reviews: {sample_app.get('review_count', 'N/A'):,}")
            print(f"  • Current Rank: {sample_app.get('current_rank', 'N/A')}")
    
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Search for apps
    print("\nTest 2: Searching for 'fitness' apps...")
    try:
        search_results = scraper.search_apps('fitness', 'us', 3)
        print(f"Success: Found {len(search_results)} fitness apps")
        
        if search_results:
            for i, app in enumerate(search_results[:2], 1):
                print(f"  {i}. {app.get('title', 'N/A')} by {app.get('developer', 'N/A')}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Get top paid apps
    print("\n💰 Test 3: Getting top 3 paid games...")
    try:
        paid_games = scraper.get_top_charts('us', 'games', 'top_paid', 3)
        print(f"✅ Success: Found {len(paid_games)} top paid games")
        
        if paid_games:
            for i, app in enumerate(paid_games, 1):
                price = app.get('price', 0)
                currency = app.get('currency', 'USD')
                print(f"  {i}. {app.get('title', 'N/A')} - {currency} {price}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Multi-country scraping
    print("\n🌍 Test 4: Multi-country scraping (US, UK)...")
    try:
        multi_results = scraper.scrape_multiple_countries('games', 'top_free', 3, ['us', 'gb'])
        print(f"✅ Success: Scraped {len(multi_results)} countries")
        
        for country, apps in multi_results.items():
            print(f"  • {country.upper()}: {len(apps)} apps")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: Get app reviews (if we have an app ID)
    if 'top_games' in locals() and top_games:
        print("\n⭐ Test 5: Getting reviews for top app...")
        try:
            app_id = top_games[0].get('app_store_id')
            if app_id:
                reviews = scraper.get_app_reviews(app_id, 'us', 5)
                print(f"✅ Success: Found {len(reviews)} reviews")
                
                if reviews:
                    sample_review = reviews[0]
                    print(f"  Sample review: {sample_review.get('rating', 'N/A')}/5 stars")
                    content = sample_review.get('content', '')[:100]
                    print(f"  Content: {content}...")
        
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n🎉 Testing complete!")
    return True

def test_trending_analysis():
    """Test the trending analysis feature"""
    print("\n📈 Testing Trending Analysis...")
    print("=" * 40)
    
    scraper = AppStoreScraperNew()
    
    try:
        # Quick trending analysis with minimal data
        trending = scraper.get_trending_analysis(['us'], ['games'])
        
        print(f"✅ Trending analysis complete!")
        print(f"  • Countries analyzed: {len(trending.get('countries_analyzed', []))}")
        print(f"  • Categories analyzed: {len(trending.get('categories_analyzed', []))}")
        print(f"  • Total apps analyzed: {trending.get('total_apps_analyzed', 0)}")
        print(f"  • Trending apps found: {len(trending.get('trending_apps', []))}")
        
        # Show top trending apps
        trending_apps = trending.get('trending_apps', [])
        if trending_apps:
            print("\n🔥 Top trending apps:")
            for i, app in enumerate(trending_apps[:3], 1):
                score = app.get('trending_score', 0)
                print(f"  {i}. {app.get('title', 'N/A')} (Score: {score})")
        
        return trending
        
    except Exception as e:
        print(f"❌ Error in trending analysis: {e}")
        return None

def save_test_results(data, filename):
    """Save test results to file"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_filename = f"test_results_{timestamp}_{filename}"
        
        with open(full_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"💾 Test results saved to: {full_filename}")
        
    except Exception as e:
        print(f"❌ Error saving results: {e}")

if __name__ == "__main__":
    print("🚀 Starting App Store Scraper Tests")
    print("Using app-store-scraper library")
    print("=" * 60)
    
    # Check if library is available
    try:
        from app_store_scraper import AppStore
        print("✅ app-store-scraper library is available")
    except ImportError:
        print("❌ app-store-scraper library not installed")
        print("Install with: pip install app-store-scraper")
        sys.exit(1)
    
    # Run basic tests
    test_basic_functionality()
    
    # Run trending analysis test
    trending_results = test_trending_analysis()
    
    # Save results if we got some data
    if trending_results:
        save_test_results(trending_results, "trending_analysis.json")
    
    print("\n🎯 All tests completed!")
    print("The new scraper is ready to use in your Hunter app.")