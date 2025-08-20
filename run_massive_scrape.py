#!/usr/bin/env python3
"""
Massive Data Scraping Script for Hunter Platform

This script will scrape tons of data from multiple sources:
- App Store (all countries, all categories, thousands of apps)
- Steam Games (comprehensive gaming data)
- Events (global events from multiple sources)

Run this to populate your database with massive amounts of real data.
"""

import sys
import os
import time
import threading
from datetime import datetime
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

def massive_app_store_scrape():
    """Scrape massive amounts of App Store data"""
    print("🍎 Starting MASSIVE App Store scraping...")
    
    try:
        from scrapers.enhanced_app_store_scraper import EnhancedAppStoreScraper
        from models import database
        
        scraper = EnhancedAppStoreScraper()
        
        # All major regions
        regions = ["us", "gb", "ca", "au", "de", "fr", "jp", "kr", "cn", "in", "br", "mx", "ru"]
        
        # All major categories  
        categories = ["games", "entertainment", "business", "productivity", "health-fitness", 
                     "social-networking", "photo-video", "music", "lifestyle", "finance",
                     "education", "news", "sports", "travel", "food-drink"]
        
        # Chart types to scrape
        chart_types = ["top-free", "top-paid", "top-grossing", "new-apps"]
        
        total_apps = 0
        
        for region in regions:
            print(f"  📍 Scraping region: {region}")
            
            for category in categories:
                print(f"    📂 Category: {category}")
                
                for chart_type in chart_types:
                    print(f"      📊 Chart: {chart_type}")
                    
                    try:
                        # Scrape top 200 apps per chart
                        apps = scraper.scrape_region_category_comprehensive(
                            region=region,
                            category=category,
                            chart_type=chart_type,
                            limit=200
                        )
                        
                        if apps:
                            total_apps += len(apps)
                            print(f"        ✅ Found {len(apps)} apps (Total: {total_apps})")
                            
                            # Save to database
                            database.save_apps(apps)
                        
                        # Small delay to be respectful
                        time.sleep(1)
                        
                    except Exception as e:
                        print(f"        ❌ Error: {e}")
                        continue
        
        print(f"🎉 App Store scraping complete! Total apps: {total_apps}")
        return total_apps
        
    except Exception as e:
        print(f"❌ App Store scraping failed: {e}")
        return 0

def massive_steam_scrape():
    """Scrape massive amounts of Steam data"""
    print("🎮 Starting MASSIVE Steam scraping...")
    
    try:
        from scrapers.enhanced_steam_scraper import EnhancedSteamScraper
        from models import database
        
        scraper = EnhancedSteamScraper()
        
        # Steam categories to scrape extensively
        categories = [
            "Action", "Adventure", "Casual", "Indie", "Massively Multiplayer",
            "Racing", "RPG", "Simulation", "Sports", "Strategy", "Free to Play",
            "Early Access", "VR Supported", "Co-op", "Multiplayer", "Singleplayer"
        ]
        
        total_games = 0
        
        for category in categories:
            print(f"  🏷️ Scraping Steam category: {category}")
            
            try:
                # Scrape comprehensive data for each category
                games = scraper.scrape_category_comprehensive(
                    category=category,
                    max_games=1000  # Up to 1000 games per category
                )
                
                if games:
                    total_games += len(games)
                    print(f"    ✅ Found {len(games)} games (Total: {total_games})")
                    
                    # Save to database
                    database.save_steam_games(games)
                
                # Delay between categories
                time.sleep(2)
                
            except Exception as e:
                print(f"    ❌ Error in category {category}: {e}")
                continue
        
        # Also scrape trending/popular games
        print("  🔥 Scraping trending Steam games...")
        try:
            trending = scraper.scrape_trending_comprehensive(limit=500)
            if trending:
                total_games += len(trending)
                database.save_steam_games(trending)
                print(f"    ✅ Added {len(trending)} trending games (Total: {total_games})")
        except Exception as e:
            print(f"    ❌ Error scraping trending: {e}")
        
        print(f"🎉 Steam scraping complete! Total games: {total_games}")
        return total_games
        
    except Exception as e:
        print(f"❌ Steam scraping failed: {e}")
        return 0

def massive_events_scrape():
    """Scrape massive amounts of events data"""
    print("📅 Starting MASSIVE Events scraping...")
    
    try:
        from scrapers.comprehensive_events_scraper import ComprehensiveEventsScraper
        from models import database
        
        scraper = ComprehensiveEventsScraper()
        
        total_events = 0
        
        # Scrape different types of events
        event_sources = [
            ("holidays", "Global holidays and observances"),
            ("gaming", "Gaming tournaments and releases"),
            ("tech", "Technology conferences and releases"),
            ("retail", "Shopping events and sales"),
            ("sports", "Major sporting events"),
            ("entertainment", "Movies, TV, music releases"),
            ("seasonal", "Seasonal trends and events")
        ]
        
        for source_type, description in event_sources:
            print(f"  🎭 Scraping {description}...")
            
            try:
                events = scraper.scrape_comprehensive_events(
                    event_type=source_type,
                    months_ahead=24  # Get events for next 2 years
                )
                
                if events:
                    total_events += len(events)
                    print(f"    ✅ Found {len(events)} events (Total: {total_events})")
                    
                    # Save to database
                    database.save_events(events)
                
                time.sleep(1)
                
            except Exception as e:
                print(f"    ❌ Error in {source_type}: {e}")
                continue
        
        print(f"🎉 Events scraping complete! Total events: {total_events}")
        return total_events
        
    except Exception as e:
        print(f"❌ Events scraping failed: {e}")
        return 0

def run_parallel_scraping():
    """Run all scrapers in parallel for maximum speed"""
    print("🚀 Starting PARALLEL MASSIVE SCRAPING...")
    print("=" * 60)
    
    # Initialize database
    try:
        from models import database
        database.create_tables()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return
    
    start_time = datetime.now()
    
    # Create threads for parallel execution
    threads = []
    results = {}
    
    def app_store_thread():
        results['apps'] = massive_app_store_scrape()
    
    def steam_thread():
        results['steam'] = massive_steam_scrape()
    
    def events_thread():
        results['events'] = massive_events_scrape()
    
    # Start all threads
    threads.append(threading.Thread(target=app_store_thread, name="AppStore"))
    threads.append(threading.Thread(target=steam_thread, name="Steam"))
    threads.append(threading.Thread(target=events_thread, name="Events"))
    
    print(f"🔥 Starting {len(threads)} parallel scraping threads...")
    
    for thread in threads:
        thread.start()
        print(f"  ▶️ Started {thread.name} thread")
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
        print(f"  ✅ {thread.name} thread completed")
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    # Print results
    print("\n" + "=" * 60)
    print("🎉 MASSIVE SCRAPING COMPLETED!")
    print("=" * 60)
    print(f"⏱️ Total time: {duration}")
    print(f"📱 Apps scraped: {results.get('apps', 0):,}")
    print(f"🎮 Steam games scraped: {results.get('steam', 0):,}")
    print(f"📅 Events scraped: {results.get('events', 0):,}")
    
    total_items = sum(results.values())
    print(f"📊 TOTAL ITEMS: {total_items:,}")
    
    if total_items > 0:
        rate = total_items / duration.total_seconds() * 60
        print(f"🚀 Scraping rate: {rate:.1f} items/minute")

def run_sequential_scraping():
    """Run scrapers one by one (safer, slower)"""
    print("⚡ Starting SEQUENTIAL MASSIVE SCRAPING...")
    print("=" * 60)
    
    # Initialize database
    try:
        from models import database
        database.create_tables()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return
    
    start_time = datetime.now()
    
    # Run scrapers sequentially
    apps_count = massive_app_store_scrape()
    steam_count = massive_steam_scrape()
    events_count = massive_events_scrape()
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    # Print results
    print("\n" + "=" * 60)
    print("🎉 SEQUENTIAL SCRAPING COMPLETED!")
    print("=" * 60)
    print(f"⏱️ Total time: {duration}")
    print(f"📱 Apps scraped: {apps_count:,}")
    print(f"🎮 Steam games scraped: {steam_count:,}")
    print(f"📅 Events scraped: {events_count:,}")
    
    total_items = apps_count + steam_count + events_count
    print(f"📊 TOTAL ITEMS: {total_items:,}")

def main():
    print("🎯 HUNTER MASSIVE DATA SCRAPER")
    print("=" * 60)
    print("This will scrape TONS of data from multiple sources:")
    print("• App Store: 13 regions × 15 categories × 4 charts × 200 apps = ~156,000 apps")
    print("• Steam: 16 categories × 1000 games + 500 trending = ~16,500 games")  
    print("• Events: 7 sources × 24 months = ~thousands of events")
    print("=" * 60)
    
    mode = input("Choose scraping mode:\n1. Parallel (faster, more intensive)\n2. Sequential (safer, slower)\nEnter 1 or 2: ").strip()
    
    if mode == "1":
        run_parallel_scraping()
    elif mode == "2":
        run_sequential_scraping()
    else:
        print("Invalid choice. Running sequential mode...")
        run_sequential_scraping()
    
    print("\n🎉 Scraping complete! Restart your Hunter app to see the new data.")

if __name__ == "__main__":
    main()