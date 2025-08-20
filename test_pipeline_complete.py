"""
Test complete end-to-end pipeline functionality
Verify all scrapers are working and data is persisting to database
"""

import time
from datetime import datetime
from pipeline.data_pipeline import AutomatedDataPipeline
from models import database, App, SteamGame, Event

def test_complete_pipeline():
    """Test the complete pipeline end-to-end"""
    print("HUNTER PLATFORM - COMPLETE PIPELINE TEST")
    print("=" * 60)
    print(f"Test started: {datetime.now()}")
    
    # Initialize database
    database.create_tables()
    
    # Get initial counts
    session = database.get_session()
    initial_apps = session.query(App).count()
    initial_games = session.query(SteamGame).count()
    initial_events = session.query(Event).count()
    database.close_session(session)
    
    print(f"\nInitial database state:")
    print(f"  Apps: {initial_apps}")
    print(f"  Steam Games: {initial_games}")
    print(f"  Events: {initial_events}")
    
    # Initialize pipeline
    pipeline = AutomatedDataPipeline()
    
    # Test App Store quick scrape
    print(f"\n1. Testing App Store Quick Scrape...")
    start_time = time.time()
    try:
        result = pipeline.app_store_quick_scrape()
        duration = time.time() - start_time
        
        print(f"   Duration: {duration:.2f}s")
        print(f"   Result: {result}")
        
        if result.get('trending_apps_count', 0) > 0:
            print("   STATUS: SUCCESS")
        else:
            print("   STATUS: WARNING - No trending apps found")
            
    except Exception as e:
        print(f"   STATUS: FAILED - {e}")
    
    # Test Steam quick scrape
    print(f"\n2. Testing Steam Quick Scrape...")
    start_time = time.time()
    try:
        result = pipeline.steam_quick_scrape()
        duration = time.time() - start_time
        
        print(f"   Duration: {duration:.2f}s")
        print(f"   Result: {result}")
        
        if result.get('total_games', 0) > 0:
            print("   STATUS: SUCCESS")
        else:
            print("   STATUS: FAILED - No games scraped")
            
    except Exception as e:
        print(f"   STATUS: FAILED - {e}")
    
    # Test Events daily scrape
    print(f"\n3. Testing Events Daily Scrape...")
    start_time = time.time()
    try:
        result = pipeline.events_daily_scrape()
        duration = time.time() - start_time
        
        print(f"   Duration: {duration:.2f}s")
        print(f"   Result: {result}")
        
        if result.get('total_events', 0) > 0:
            print("   STATUS: SUCCESS")
        else:
            print("   STATUS: WARNING - No events found")
            
    except Exception as e:
        print(f"   STATUS: FAILED - {e}")
    
    # Check final database state
    session = database.get_session()
    final_apps = session.query(App).count()
    final_games = session.query(SteamGame).count()
    final_events = session.query(Event).count()
    database.close_session(session)
    
    print(f"\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    
    print(f"Database changes:")
    print(f"  Apps: {initial_apps} -> {final_apps} (+{final_apps - initial_apps})")
    print(f"  Steam Games: {initial_games} -> {final_games} (+{final_games - initial_games})")
    print(f"  Events: {initial_events} -> {final_events} (+{final_events - initial_events})")
    
    total_new_data = (final_apps - initial_apps) + (final_games - initial_games) + (final_events - initial_events)
    
    print(f"\nOverall Assessment:")
    if total_new_data > 0:
        print(f"  SUCCESS: Pipeline working correctly!")
        print(f"  Total new records: {total_new_data}")
        
        # Show sample data
        if final_apps > initial_apps:
            session = database.get_session()
            latest_app = session.query(App).order_by(App.id.desc()).first()
            if latest_app:
                print(f"  Latest App: {latest_app.title} by {latest_app.developer}")
            database.close_session(session)
            
        if final_games > initial_games:
            session = database.get_session()
            latest_game = session.query(SteamGame).order_by(SteamGame.id.desc()).first()
            if latest_game:
                print(f"  Latest Game: {latest_game.title}")
            database.close_session(session)
            
        return True
    else:
        print(f"  WARNING: No new data was persisted")
        print(f"  Check scraper configurations and network connectivity")
        return False

def test_pipeline_status():
    """Test pipeline status and health check"""
    print(f"\n" + "=" * 60)
    print("PIPELINE STATUS TEST")
    print("=" * 60)
    
    pipeline = AutomatedDataPipeline()
    
    try:
        status = pipeline.get_pipeline_status()
        print(f"Pipeline Status:")
        print(f"  Running: {status['is_running']}")
        print(f"  Cache - Apps: {status['cache_summary']['apps']}")
        print(f"  Cache - Games: {status['cache_summary']['steam_games']}")
        print(f"  Cache - Events: {status['cache_summary']['events']}")
        
        # Test health check
        health = pipeline.health_check()
        print(f"\nHealth Check:")
        print(f"  Pipeline Running: {health['pipeline_running']}")
        print(f"  Apps in Cache: {health['cache_status']['apps_count']}")
        print(f"  Games in Cache: {health['cache_status']['steam_games_count']}")
        print(f"  Events in Cache: {health['cache_status']['events_count']}")
        
        return True
    except Exception as e:
        print(f"Pipeline status test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_complete_pipeline()
    test_pipeline_status()
    
    print(f"\n" + "=" * 60)
    print(f"Test completed: {datetime.now()}")
    
    if success:
        print("RESULT: All systems working correctly!")
    else:
        print("RESULT: Some issues detected - check logs above")
    
    print("=" * 60)