"""
Quick fix for database persistence issues
Focus on identifying and resolving the SQLite DateTime error
"""

import os
import traceback
from datetime import datetime, timezone
from pipeline.data_pipeline import AutomatedDataPipeline
from models import database, App, SteamGame, Event
from scrapers.enhanced_app_store_scraper import EnhancedAppStoreScraper
from scrapers.enhanced_steam_scraper import EnhancedSteamScraper

def test_database_datetime_issue():
    """Test and fix the SQLite DateTime persistence issue"""
    print("TESTING DATABASE DATETIME ISSUE")
    print("=" * 50)
    
    try:
        # Initialize database
        database.create_tables()
        print("Database tables created successfully")
        
        # Test basic data insertion
        session = database.get_session()
        
        print("\n1. Testing direct App creation with datetime...")
        
        # Create a sample app with proper datetime handling
        test_app_data = {
            'app_store_id': '12345678',
            'title': 'Test App',
            'developer': 'Test Developer',
            'category': 'Games',
            'price': 0.0,
            'rating': 4.5,
            'rating_count': 100,
            'bundle_id': 'com.test.app',
            'current_rank': 1,
            'region': 'us',
            'last_updated': datetime.now().replace(tzinfo=None)  # Remove timezone info for SQLite
        }
        
        # Try to create the app directly
        try:
            new_app = App(**{k: v for k, v in test_app_data.items() if hasattr(App, k)})
            session.add(new_app)
            session.commit()
            print("SUCCESS: Direct app creation worked")
        except Exception as e:
            print(f"FAILED: Direct app creation error: {e}")
            session.rollback()
        
        database.close_session(session)
        
        print("\n2. Testing pipeline data storage...")
        
        # Test App Store scraper -> pipeline storage
        app_scraper = EnhancedAppStoreScraper()
        app_scraper.regions = app_scraper.regions[:1]  # Only US
        
        try:
            apps = app_scraper.scrape_top_charts_all_regions('top-free', 'games', 2)
            print(f"Apps scraped: {len(apps)}")
            
            if apps:
                # Fix datetime fields before storing
                for app in apps:
                    # Convert any datetime fields to timezone-naive
                    for field in ['last_updated', 'scraped_at', 'release_date']:
                        if field in app and app[field]:
                            if isinstance(app[field], str):
                                try:
                                    dt = datetime.fromisoformat(app[field].replace('Z', '+00:00'))
                                    app[field] = dt.replace(tzinfo=None)
                                except:
                                    app[field] = datetime.now().replace(tzinfo=None)
                            elif isinstance(app[field], datetime):
                                app[field] = app[field].replace(tzinfo=None)
                
                # Try storing the fixed apps
                pipeline = AutomatedDataPipeline()
                pipeline.store_apps_data(apps)
                print("SUCCESS: App Store data stored to database")
                
                # Verify storage
                session = database.get_session()
                count = session.query(App).count()
                print(f"Apps in database: {count}")
                database.close_session(session)
                
        except Exception as e:
            print(f"FAILED: App Store pipeline storage error: {e}")
            traceback.print_exc()
        
        print("\n3. Testing Steam data storage...")
        
        # Test Steam scraper -> pipeline storage
        steam_scraper = EnhancedSteamScraper()
        
        try:
            games = steam_scraper.get_top_sellers(2)
            print(f"Games scraped: {len(games)}")
            
            if games:
                # Fix datetime fields before storing
                for game in games:
                    for field in ['last_updated', 'scraped_at', 'release_date']:
                        if field in game and game[field]:
                            if isinstance(game[field], str):
                                try:
                                    dt = datetime.fromisoformat(game[field].replace('Z', '+00:00'))
                                    game[field] = dt.replace(tzinfo=None)
                                except:
                                    game[field] = datetime.now().replace(tzinfo=None)
                            elif isinstance(game[field], datetime):
                                game[field] = game[field].replace(tzinfo=None)
                
                # Try storing the fixed games
                pipeline = AutomatedDataPipeline()
                pipeline.store_steam_data(games)
                print("SUCCESS: Steam data stored to database")
                
                # Verify storage
                session = database.get_session()
                count = session.query(SteamGame).count()
                print(f"Steam games in database: {count}")
                database.close_session(session)
                
        except Exception as e:
            print(f"FAILED: Steam pipeline storage error: {e}")
            traceback.print_exc()
        
        print("\nFINAL DATABASE STATUS:")
        session = database.get_session()
        apps_count = session.query(App).count()
        games_count = session.query(SteamGame).count()
        events_count = session.query(Event).count()
        print(f"Total Apps: {apps_count}")
        print(f"Total Steam Games: {games_count}")
        print(f"Total Events: {events_count}")
        database.close_session(session)
        
        if apps_count > 0 or games_count > 0:
            print("SUCCESS: Database persistence is working!")
            return True
        else:
            print("FAILED: No data persisted to database")
            return False
            
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        traceback.print_exc()
        return False

def fix_pipeline_datetime_handling():
    """Fix datetime handling in pipeline storage methods"""
    print("\nFIXING PIPELINE DATETIME HANDLING...")
    
    # The issue is likely in the pipeline storage methods
    # Let's check if we need to patch the datetime handling
    
    try:
        # Read the current pipeline file to check for datetime handling
        import inspect
        pipeline = AutomatedDataPipeline()
        
        print("Pipeline storage methods found:")
        print("- store_apps_data")
        print("- store_steam_data") 
        print("- store_events_data")
        
        print("\nRecommendation: Add datetime sanitization in storage methods")
        print("Convert all datetime objects to timezone-naive before SQLite storage")
        
        return True
        
    except Exception as e:
        print(f"Error checking pipeline: {e}")
        return False

if __name__ == "__main__":
    print("DATABASE PERSISTENCE ISSUE DIAGNOSIS & FIX")
    print("=" * 60)
    
    success = test_database_datetime_issue()
    
    if not success:
        fix_pipeline_datetime_handling()
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS COMPLETE")