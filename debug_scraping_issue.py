"""
Debug Scraping and Database Persistence Issues
Comprehensive test to identify why pipeline scraping fails
"""

import os
import sys
import sqlite3
from datetime import datetime
from pipeline.data_pipeline import AutomatedDataPipeline
from models import database
import traceback

def check_database_setup():
    """Check if database exists and has correct tables"""
    print("=" * 60)
    print("CHECKING DATABASE SETUP")
    print("=" * 60)
    
    # Check if database file exists
    db_path = "hunter.db"
    if os.path.exists(db_path):
        print(f"Database file exists: {db_path}")
        
        # Check tables
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"Database tables ({len(tables)}):")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count} rows")
        
        conn.close()
        return True
    else:
        print(f"Database file missing: {db_path}")
        return False

def test_database_creation():
    """Test database creation and table setup"""
    print("\n" + "=" * 60)
    print("TESTING DATABASE CREATION")
    print("=" * 60)
    
    try:
        # Initialize database
        database.create_tables()
        print("Database tables created successfully")
        
        # Test basic database operations
        session = database.get_session()
        print("Database session created successfully")
        
        # Import models to test
        from models import App, SteamGame, Event
        
        # Count existing data
        app_count = session.query(App).count()
        game_count = session.query(SteamGame).count()
        event_count = session.query(Event).count()
        
        print(f"Current data in database:")
        print(f"  Apps: {app_count}")
        print(f"  Steam Games: {game_count}")
        print(f"  Events: {event_count}")
        
        database.close_session(session)
        return True
        
    except Exception as e:
        print(f"Database creation failed: {e}")
        traceback.print_exc()
        return False

def test_direct_scraper_methods():
    """Test scrapers directly (not through pipeline)"""
    print("\n" + "=" * 60)
    print("TESTING DIRECT SCRAPER METHODS")
    print("=" * 60)
    
    results = {}
    
    # Test App Store Scraper
    print("\n1. Testing App Store Scraper...")
    try:
        from scrapers.enhanced_app_store_scraper import EnhancedAppStoreScraper
        
        scraper = EnhancedAppStoreScraper()
        scraper.regions = [scraper.regions[0]]  # Only US
        
        print(f"   - Regions configured: {len(scraper.regions)}")
        print(f"   - Base URL: {scraper.base_url}")
        print(f"   - RSS Base URL: {getattr(scraper, 'rss_base', 'None')}")
        
        apps = scraper.scrape_top_charts_all_regions('top-free', 'all', 3)
        
        if apps and len(apps) > 0:
            print(f"   SUCCESS: {len(apps)} apps scraped")
            print(f"   Sample: {apps[0].get('title', 'N/A')}")
            results['app_store'] = {'success': True, 'count': len(apps)}
        else:
            print(f"   FAILED: No apps returned")
            results['app_store'] = {'success': False, 'count': 0}
            
    except Exception as e:
        print(f"   ERROR: {e}")
        traceback.print_exc()
        results['app_store'] = {'success': False, 'error': str(e)}
    
    # Test Steam Scraper
    print("\n2. Testing Steam Scraper...")
    try:
        from scrapers.enhanced_steam_scraper import EnhancedSteamScraper
        
        scraper = EnhancedSteamScraper()
        games = scraper.get_top_sellers(3)
        
        if games and len(games) > 0:
            print(f"   SUCCESS SUCCESS: {len(games)} games scraped")
            print(f"   Sample: {games[0].get('title', 'N/A')}")
            results['steam'] = {'success': True, 'count': len(games)}
        else:
            print(f"   FAILED FAILED: No games returned")
            results['steam'] = {'success': False, 'count': 0}
            
    except Exception as e:
        print(f"   FAILED ERROR: {e}")
        results['steam'] = {'success': False, 'error': str(e)}
    
    # Test Events Scraper  
    print("\n3. Testing Events Scraper...")
    try:
        from scrapers.comprehensive_events_scraper import ComprehensiveEventsScraper
        from datetime import timedelta
        
        scraper = ComprehensiveEventsScraper()
        end_date = datetime.now() + timedelta(days=30)
        events = scraper.scrape_major_holidays(end_date)
        
        if events and len(events) > 0:
            print(f"   SUCCESS SUCCESS: {len(events)} events scraped")
            print(f"   Sample: {events[0].get('name', 'N/A')}")
            results['events'] = {'success': True, 'count': len(events)}
        else:
            print(f"   FAILED FAILED: No events returned")
            results['events'] = {'success': False, 'count': 0}
            
    except Exception as e:
        print(f"   FAILED ERROR: {e}")
        results['events'] = {'success': False, 'error': str(e)}
    
    return results

def test_pipeline_methods():
    """Test pipeline scraping methods"""
    print("\n" + "=" * 60) 
    print("TESTING PIPELINE SCRAPING METHODS")
    print("=" * 60)
    
    try:
        pipeline = AutomatedDataPipeline()
        
        # Test quick scrape methods (which should work)
        print("\n1. Testing App Store Quick Scrape...")
        try:
            result = pipeline.app_store_quick_scrape()
            print(f"   Result keys: {list(result.keys())}")
            print(f"   Trending apps: {result.get('trending_apps_count', 0)}")
            
            if result.get('trending_apps_count', 0) > 0:
                print("   SUCCESS App Store quick scrape working")
            else:
                print("   FAILED App Store quick scrape failed")
                
        except Exception as e:
            print(f"   FAILED App Store quick scrape error: {e}")
            traceback.print_exc()
        
        print("\n2. Testing Steam Quick Scrape...")
        try:
            result = pipeline.steam_quick_scrape()
            print(f"   Result keys: {list(result.keys())}")
            print(f"   Total games: {result.get('total_games', 0)}")
            
            if result.get('total_games', 0) > 0:
                print("   SUCCESS Steam quick scrape working")
            else:
                print("   FAILED Steam quick scrape failed")
                
        except Exception as e:
            print(f"   FAILED Steam quick scrape error: {e}")
        
        print("\n3. Testing Events Daily Scrape...")
        try:
            result = pipeline.events_daily_scrape()
            print(f"   Result keys: {list(result.keys())}")
            print(f"   Total events: {result.get('total_events', 0)}")
            
            if result.get('total_events', 0) > 0:
                print("   SUCCESS Events daily scrape working")
            else:
                print("   FAILED Events daily scrape failed")
                
        except Exception as e:
            print(f"   FAILED Events daily scrape error: {e}")
            
    except Exception as e:
        print(f"Pipeline initialization failed: {e}")
        traceback.print_exc()

def test_database_persistence():
    """Test if data is actually being saved to database"""
    print("\n" + "=" * 60)
    print("TESTING DATABASE PERSISTENCE")
    print("=" * 60)
    
    try:
        from models import App, SteamGame, Event
        from models import database
        
        # Get counts before
        session = database.get_session()
        
        apps_before = session.query(App).count()
        games_before = session.query(SteamGame).count()  
        events_before = session.query(Event).count()
        
        print(f"Before scraping:")
        print(f"  Apps: {apps_before}")
        print(f"  Steam Games: {games_before}")
        print(f"  Events: {events_before}")
        
        database.close_session(session)
        
        # Run pipeline quick scrape
        pipeline = AutomatedDataPipeline()
        
        print(f"\nRunning pipeline scrapers...")
        pipeline.app_store_quick_scrape()
        pipeline.steam_quick_scrape()
        pipeline.events_daily_scrape()
        
        # Get counts after
        session = database.get_session()
        
        apps_after = session.query(App).count()
        games_after = session.query(SteamGame).count()
        events_after = session.query(Event).count()
        
        print(f"\nAfter scraping:")
        print(f"  Apps: {apps_after} (change: +{apps_after - apps_before})")
        print(f"  Steam Games: {games_after} (change: +{games_after - games_before})")
        print(f"  Events: {events_after} (change: +{events_after - events_before})")
        
        database.close_session(session)
        
        # Check if any data was persisted
        total_change = (apps_after - apps_before) + (games_after - games_before) + (events_after - events_before)
        
        if total_change > 0:
            print(f"\nSUCCESS SUCCESS: {total_change} total records persisted to database")
            return True
        else:
            print(f"\nFAILED FAILED: No new data persisted to database")
            return False
            
    except Exception as e:
        print(f"FAILED Database persistence test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run comprehensive debugging"""
    print("HUNTER PLATFORM - COMPREHENSIVE SCRAPING DEBUG")
    print("=" * 80)
    print(f"Debug started at: {datetime.now()}")
    
    # Check database setup
    db_exists = check_database_setup()
    if not db_exists:
        test_database_creation()
    
    # Test direct scrapers
    scraper_results = test_direct_scraper_methods()
    
    # Test pipeline methods
    test_pipeline_methods()
    
    # Test database persistence
    persistence_working = test_database_persistence()
    
    # Final summary
    print("\n" + "=" * 80)
    print("FINAL DEBUG SUMMARY")
    print("=" * 80)
    
    print("Direct Scraper Results:")
    for platform, result in scraper_results.items():
        status = "SUCCESS PASS" if result.get('success') else "FAILED FAIL"
        count = result.get('count', 0)
        print(f"  {platform:12} | {status:8} | {count:3} items")
    
    print(f"\nDatabase Persistence: {'SUCCESS WORKING' if persistence_working else 'FAILED NOT WORKING'}")
    
    successful_scrapers = len([r for r in scraper_results.values() if r.get('success')])
    total_scrapers = len(scraper_results)
    
    print(f"\nOverall Status:")
    print(f"  Scrapers Working: {successful_scrapers}/{total_scrapers}")
    print(f"  Database Working: {persistence_working}")
    
    if successful_scrapers == total_scrapers and persistence_working:
        print(f"\n ALL SYSTEMS WORKING CORRECTLY!")
    else:
        print(f"\nWARNING  ISSUES DETECTED - CHECK LOGS ABOVE")
    
    print(f"\nDebug completed at: {datetime.now()}")

if __name__ == "__main__":
    main()