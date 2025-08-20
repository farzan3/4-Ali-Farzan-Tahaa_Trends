"""
Quick Pipeline Test - Tests core functionality without heavy processing
"""

from datetime import datetime
from pipeline.data_pipeline import AutomatedDataPipeline
from models import database, App, SteamGame, Event

def test_quick_pipeline():
    """Test core pipeline components quickly"""
    print("QUICK PIPELINE TEST")
    print("=" * 40)
    
    # Initialize database
    database.create_tables()
    
    # Get initial counts
    session = database.get_session()
    initial_apps = session.query(App).count()
    initial_games = session.query(SteamGame).count()
    initial_events = session.query(Event).count()
    database.close_session(session)
    
    print(f"Initial: Apps={initial_apps}, Games={initial_games}, Events={initial_events}")
    
    # Initialize pipeline
    pipeline = AutomatedDataPipeline()
    
    # Test Steam quick scrape (this should work fast)
    print("\nTesting Steam Quick Scrape...")
    try:
        result = pipeline.steam_quick_scrape()
        print(f"Steam Result: {result}")
        steam_success = result.get('total_games', 0) > 0
        print(f"Steam Status: {'SUCCESS' if steam_success else 'FAILED'}")
    except Exception as e:
        print(f"Steam Error: {e}")
        steam_success = False
    
    # Test Events daily scrape
    print("\nTesting Events Daily Scrape...")
    try:
        result = pipeline.events_daily_scrape()
        print(f"Events Result: {result}")
        events_success = result.get('total_events', 0) > 0
        print(f"Events Status: {'SUCCESS' if events_success else 'FAILED'}")
    except Exception as e:
        print(f"Events Error: {e}")
        events_success = False
    
    # Check final database state
    session = database.get_session()
    final_apps = session.query(App).count()
    final_games = session.query(SteamGame).count()
    final_events = session.query(Event).count()
    database.close_session(session)
    
    print(f"\nFinal: Apps={final_apps}, Games={final_games}, Events={final_events}")
    print(f"Changes: Apps=+{final_apps-initial_apps}, Games=+{final_games-initial_games}, Events=+{final_events-initial_events}")
    
    # Overall assessment
    total_new = (final_apps - initial_apps) + (final_games - initial_games) + (final_events - initial_events)
    
    if total_new > 0:
        print(f"\nSUCCESS: Pipeline working! {total_new} new records")
        return True
    else:
        print(f"\nWARNING: No new data persisted")
        return False

if __name__ == "__main__":
    success = test_quick_pipeline()
    print(f"\nOverall Result: {'PASS' if success else 'NEEDS ATTENTION'}")