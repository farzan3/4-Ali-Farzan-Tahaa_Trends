#!/usr/bin/env python3
"""
Practical Data Scraping Script for Hunter Platform

This script uses the actual available scraper methods to collect tons of real data.
"""

import sys
import os
import time
import sqlite3
from datetime import datetime
from pathlib import Path

def save_apps_to_db(apps_data):
    """Save apps data to database"""
    if not apps_data:
        return 0
    
    db_path = Path('hunter_app.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    saved_count = 0
    
    for app in apps_data:
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO apps 
                (app_store_id, title, developer, category, country, icon_url, description, 
                 current_rank, rating, review_count, price, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                app.get('id', ''),
                app.get('title', ''),
                app.get('developer', ''),
                app.get('category', ''),
                app.get('region', ''),
                app.get('icon_url', ''),
                app.get('description', ''),
                app.get('rank', 0),
                app.get('rating', 0.0),
                app.get('review_count', 0),
                app.get('price', 0.0),
                datetime.now().isoformat()
            ))
            saved_count += 1
        except Exception as e:
            print(f"Error saving app {app.get('title', 'Unknown')}: {e}")
    
    conn.commit()
    conn.close()
    
    return saved_count

def save_steam_games_to_db(games_data):
    """Save Steam games to database"""
    if not games_data:
        return 0
    
    db_path = Path('hunter_app.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    saved_count = 0
    
    for game in games_data:
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO steam_games 
                (steam_id, title, developer, publisher, genre, price, review_score, 
                 review_count, player_count, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                game.get('steam_id', ''),
                game.get('title', ''),
                game.get('developer', ''),
                game.get('publisher', ''),
                game.get('genre', ''),
                game.get('price', 0.0),
                game.get('review_score', 0.0),
                game.get('review_count', 0),
                game.get('player_count', 0),
                datetime.now().isoformat()
            ))
            saved_count += 1
        except Exception as e:
            print(f"Error saving game {game.get('title', 'Unknown')}: {e}")
    
    conn.commit()
    conn.close()
    
    return saved_count

def scrape_app_store_data():
    """Scrape App Store data using available methods"""
    print("🍎 Starting App Store data collection...")
    
    try:
        from scrapers.enhanced_app_store_scraper import EnhancedAppStoreScraper
        scraper = EnhancedAppStoreScraper()
        
        total_apps = 0
        
        # Chart types to scrape
        chart_types = ["top-free", "top-paid", "top-grossing"]
        
        # Categories to scrape
        categories = ["all", "games", "entertainment", "business", "productivity"]
        
        for chart_type in chart_types:
            print(f"  📊 Scraping {chart_type} charts...")
            
            for category in categories:
                print(f"    📂 Category: {category}")
                
                try:
                    # Use the actual available method
                    apps = scraper.scrape_top_charts_all_regions(
                        feed_type=chart_type,
                        category=category,
                        limit=100  # 100 apps per region
                    )
                    
                    if apps:
                        saved = save_apps_to_db(apps)
                        total_apps += saved
                        print(f"      ✅ Saved {saved} apps (Total: {total_apps})")
                    else:
                        print(f"      ⚠️ No apps found")
                    
                    # Small delay
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"      ❌ Error: {e}")
                    continue
        
        print(f"🎉 App Store scraping complete! Total: {total_apps} apps")
        return total_apps
        
    except Exception as e:
        print(f"❌ App Store scraping failed: {e}")
        return 0

def scrape_steam_data():
    """Scrape Steam data"""
    print("🎮 Starting Steam data collection...")
    
    try:
        from scrapers.enhanced_steam_scraper import EnhancedSteamScraper
        scraper = EnhancedSteamScraper()
        
        total_games = 0
        
        # Check what methods are available
        available_methods = [method for method in dir(scraper) if method.startswith('scrape') and not method.startswith('_')]
        print(f"  Available Steam scraper methods: {available_methods}")
        
        # Try to scrape using available methods
        try:
            # This is a common pattern - try to get trending/popular games
            if hasattr(scraper, 'get_trending_games'):
                games = scraper.get_trending_games(limit=500)
            elif hasattr(scraper, 'scrape_trending'):
                games = scraper.scrape_trending(limit=500)
            elif hasattr(scraper, 'get_popular_games'):
                games = scraper.get_popular_games(limit=500)
            else:
                print("  ⚠️ No recognized Steam scraping method found")
                return 0
            
            if games:
                saved = save_steam_games_to_db(games)
                total_games += saved
                print(f"  ✅ Saved {saved} Steam games")
            
        except Exception as e:
            print(f"  ❌ Steam scraping error: {e}")
        
        print(f"🎉 Steam scraping complete! Total: {total_games} games")
        return total_games
        
    except Exception as e:
        print(f"❌ Steam scraping failed: {e}")
        return 0

def scrape_events_data():
    """Scrape events data"""
    print("📅 Starting Events data collection...")
    
    try:
        from scrapers.comprehensive_events_scraper import ComprehensiveEventsScraper
        scraper = ComprehensiveEventsScraper()
        
        # Check available methods
        available_methods = [method for method in dir(scraper) if method.startswith('scrape') and not method.startswith('_')]
        print(f"  Available Events scraper methods: {available_methods}")
        
        total_events = 0
        
        # Try common event scraping patterns
        try:
            if hasattr(scraper, 'scrape_all_events'):
                events = scraper.scrape_all_events()
            elif hasattr(scraper, 'get_upcoming_events'):
                events = scraper.get_upcoming_events()
            elif hasattr(scraper, 'scrape_events'):
                events = scraper.scrape_events()
            else:
                print("  ⚠️ No recognized Events scraping method found")
                return 0
            
            if events:
                # Save events to database
                db_path = Path('hunter_app.db')
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                for event in events:
                    try:
                        cursor.execute('''
                            INSERT OR REPLACE INTO events 
                            (name, event_type, start_date, description, source, region)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            event.get('name', ''),
                            event.get('event_type', ''),
                            event.get('start_date', ''),
                            event.get('description', ''),
                            event.get('source', 'scraper'),
                            event.get('region', 'global')
                        ))
                        total_events += 1
                    except Exception as e:
                        print(f"Error saving event: {e}")
                
                conn.commit()
                conn.close()
                
                print(f"  ✅ Saved {total_events} events")
            
        except Exception as e:
            print(f"  ❌ Events scraping error: {e}")
        
        print(f"🎉 Events scraping complete! Total: {total_events} events")
        return total_events
        
    except Exception as e:
        print(f"❌ Events scraping failed: {e}")
        return 0

def show_current_database_stats():
    """Show current database statistics"""
    print("\n📊 Current Database Statistics:")
    print("=" * 40)
    
    db_path = Path('hunter_app.db')
    if not db_path.exists():
        print("❌ Database not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    tables = ['apps', 'steam_games', 'events', 'users']
    
    for table in tables:
        try:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            print(f"  {table.replace('_', ' ').title()}: {count:,} records")
        except:
            print(f"  {table.replace('_', ' ').title()}: Table not found")
    
    conn.close()

def main():
    print("🎯 HUNTER DATA SCRAPER")
    print("=" * 50)
    print("This will collect real data from multiple sources.")
    print("Expected results:")
    print("• App Store: ~10,000-50,000 apps (depends on regions)")
    print("• Steam: ~500-1,000 games")
    print("• Events: ~100-500 events")
    print("=" * 50)
    
    # Show current stats
    show_current_database_stats()
    
    # Initialize database
    try:
        from models import database
        database.create_tables()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return
    
    start_time = datetime.now()
    
    # Run scrapers
    apps_count = scrape_app_store_data()
    steam_count = scrape_steam_data()
    events_count = scrape_events_data()
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    # Final results
    print("\n" + "=" * 50)
    print("🎉 SCRAPING COMPLETED!")
    print("=" * 50)
    print(f"⏱️ Total time: {duration}")
    print(f"📱 Apps collected: {apps_count:,}")
    print(f"🎮 Steam games collected: {steam_count:,}")
    print(f"📅 Events collected: {events_count:,}")
    
    total_items = apps_count + steam_count + events_count
    print(f"📊 TOTAL NEW ITEMS: {total_items:,}")
    
    # Show final database stats
    show_current_database_stats()
    
    print("\n🎉 Scraping complete! Restart your Hunter app to see the new data.")
    print("💡 Tip: The more you run this, the more data you'll collect!")

if __name__ == "__main__":
    main()