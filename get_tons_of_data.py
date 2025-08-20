#!/usr/bin/env python3
"""
Get Tons of Data - Fast and Focused Scraping

This script will quickly collect thousands of apps from App Store.
It saves data frequently to avoid losing progress.
"""

import sys
import os
import time
import sqlite3
from datetime import datetime
from pathlib import Path

def save_apps_batch(apps_data, batch_name=""):
    """Save a batch of apps to database immediately"""
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
                app.get('id', f"auto_{saved_count}_{int(time.time())}"),
                app.get('title', 'Unknown')[:255],
                app.get('developer', 'Unknown')[:255],
                app.get('category', app.get('category_filter', 'Unknown'))[:100],
                app.get('region', 'unknown')[:10],
                app.get('icon_url', '')[:500],
                app.get('description', '')[:1000],
                app.get('rank', saved_count + 1),
                float(app.get('rating', 0.0)) if app.get('rating') else 0.0,
                int(app.get('review_count', 0)) if app.get('review_count') else 0,
                float(app.get('price', 0.0)) if app.get('price') else 0.0,
                datetime.now().isoformat()
            ))
            saved_count += 1
        except Exception as e:
            print(f"    [ERROR] Saving app {app.get('title', 'Unknown')}: {e}")
    
    conn.commit()
    conn.close()
    
    if batch_name:
        print(f"    [SAVED] {saved_count} apps from {batch_name}")
    else:
        print(f"    [SAVED] {saved_count} apps to database")
    
    return saved_count

def scrape_single_region_category(scraper, region, category, chart_type, limit=200):
    """Scrape a single region/category combination"""
    try:
        print(f"    [SCRAPING] {region} - {category} - {chart_type}")
        
        apps = scraper.scrape_top_charts_all_regions(
            feed_type=chart_type,
            category=category,
            limit=limit
        )
        
        if apps:
            # Filter apps for this specific region if multiple regions returned
            region_apps = [app for app in apps if app.get('region') == region]
            
            if region_apps:
                saved = save_apps_batch(region_apps, f"{region}-{category}-{chart_type}")
                return saved
            else:
                # If no region-specific apps, save all apps
                saved = save_apps_batch(apps, f"{region}-{category}-{chart_type}")
                return saved
        else:
            print(f"      [EMPTY] No apps found")
            return 0
            
    except Exception as e:
        print(f"      [ERROR] Failed: {e}")
        return 0

def mass_app_store_scrape():
    """Mass scrape App Store data with frequent saves"""
    print("[MASS SCRAPE] Starting App Store mass data collection...")
    
    try:
        from scrapers.enhanced_app_store_scraper import EnhancedAppStoreScraper
        scraper = EnhancedAppStoreScraper()
        
        # Focus on major regions first
        priority_regions = ["us", "gb", "de", "fr", "jp", "ca", "au"]
        
        # Focus on major categories
        priority_categories = ["all", "games", "entertainment", "productivity", "business"]
        
        # Chart types
        chart_types = ["top-free", "top-paid", "top-grossing"]
        
        total_apps = 0
        total_batches = len(priority_regions) * len(priority_categories) * len(chart_types)
        current_batch = 0
        
        print(f"[PLAN] Will scrape {total_batches} combinations")
        print(f"[PLAN] Estimated apps: {total_batches * 100:,} (assuming 100 per batch)")
        
        start_time = time.time()
        
        for region in priority_regions:
            print(f"  [REGION] Processing {region}...")
            
            for category in priority_categories:
                print(f"    [CATEGORY] {category}")
                
                for chart_type in chart_types:
                    current_batch += 1
                    progress = (current_batch / total_batches) * 100
                    
                    print(f"      [BATCH {current_batch}/{total_batches}] ({progress:.1f}%) {chart_type}")
                    
                    # Scrape this specific combination
                    batch_apps = scrape_single_region_category(
                        scraper, region, category, chart_type, limit=100
                    )
                    
                    total_apps += batch_apps
                    
                    elapsed = time.time() - start_time
                    rate = total_apps / elapsed if elapsed > 0 else 0
                    eta = (total_batches - current_batch) * (elapsed / current_batch) if current_batch > 0 else 0
                    
                    print(f"        [PROGRESS] Total: {total_apps:,} apps, Rate: {rate:.1f}/sec, ETA: {eta/60:.1f}min")
                    
                    # Small delay to be respectful
                    time.sleep(1)
        
        print(f"[COMPLETE] Mass scraping finished!")
        print(f"[STATS] Total apps collected: {total_apps:,}")
        print(f"[STATS] Total time: {(time.time() - start_time)/60:.1f} minutes")
        
        return total_apps
        
    except Exception as e:
        print(f"[FATAL] Mass scraping failed: {e}")
        return 0

def focused_scrape():
    """Quick focused scrape to get data fast"""
    print("[FOCUSED] Quick data collection...")
    
    try:
        from scrapers.enhanced_app_store_scraper import EnhancedAppStoreScraper
        scraper = EnhancedAppStoreScraper()
        
        total_apps = 0
        
        # Just get top free apps from major regions
        major_regions = ["us", "gb", "de", "jp"]
        
        for region in major_regions:
            print(f"  [REGION] {region} - Getting top 100 free apps...")
            
            try:
                # Create a region-specific scraper call
                apps = scraper.scrape_region_chart(
                    region_code=region,
                    feed_type="top-free-applications", 
                    category_id="",
                    limit=100
                )
                
                if apps:
                    # Add metadata
                    for app in apps:
                        app['region'] = region
                        app['chart_type'] = 'top-free'
                        app['category_filter'] = 'all'
                    
                    saved = save_apps_batch(apps, f"{region}-top-free")
                    total_apps += saved
                else:
                    print(f"    [EMPTY] No apps from {region}")
                
                time.sleep(2)  # Be respectful
                
            except Exception as e:
                print(f"    [ERROR] {region} failed: {e}")
        
        print(f"[FOCUSED COMPLETE] Collected {total_apps:,} apps")
        return total_apps
        
    except Exception as e:
        print(f"[FOCUSED ERROR] {e}")
        return 0

def show_final_stats():
    """Show final database statistics"""
    print("\n[FINAL STATS] Database Contents:")
    print("=" * 40)
    
    db_path = Path('hunter_app.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Count by table
    cursor.execute('SELECT COUNT(*) FROM apps')
    apps_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM steam_games')
    steam_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM events')
    events_count = cursor.fetchone()[0]
    
    print(f"  Apps: {apps_count:,}")
    print(f"  Steam Games: {steam_count:,}")
    print(f"  Events: {events_count:,}")
    print(f"  TOTAL: {apps_count + steam_count + events_count:,}")
    
    # Show apps by region
    cursor.execute('SELECT country, COUNT(*) FROM apps GROUP BY country ORDER BY COUNT(*) DESC')
    regions = cursor.fetchall()
    
    print(f"\n  Apps by Region:")
    for region, count in regions:
        print(f"    {region}: {count:,}")
    
    # Show recent apps
    cursor.execute('SELECT title, developer, country FROM apps ORDER BY last_updated DESC LIMIT 10')
    recent = cursor.fetchall()
    
    print(f"\n  Recent Apps:")
    for i, (title, dev, country) in enumerate(recent, 1):
        print(f"    {i}. {title[:30]} by {dev[:20]} ({country})")
    
    conn.close()

def main():
    print("[SCRAPER] Hunter Tons of Data Collector")
    print("=" * 50)
    
    # Initialize database
    try:
        from models import database
        database.create_tables()
        print("[OK] Database ready")
    except Exception as e:
        print(f"[ERROR] Database failed: {e}")
        return
    
    # Show initial stats
    show_final_stats()
    
    print("\nChoose scraping mode:")
    print("1. FOCUSED - Quick scrape (400-500 apps, ~5 minutes)")
    print("2. MASS - Full scrape (10,000+ apps, 30+ minutes)")
    print("3. SHOW STATS - Just show current database stats")
    
    choice = input("\nEnter choice (1, 2, or 3): ").strip()
    
    if choice == "1":
        print("\n[STARTING] Focused scraping...")
        collected = focused_scrape()
        print(f"\n[SUCCESS] Collected {collected:,} new apps!")
        
    elif choice == "2":
        print("\n[STARTING] Mass scraping...")
        print("[WARNING] This will take 30+ minutes and collect 10,000+ apps")
        confirm = input("Continue? (y/N): ").strip().lower()
        
        if confirm == 'y':
            collected = mass_app_store_scrape()
            print(f"\n[SUCCESS] Collected {collected:,} new apps!")
        else:
            print("[CANCELLED] Mass scraping cancelled")
            
    elif choice == "3":
        print("\n[STATS] Current database statistics:")
        
    else:
        print("\n[ERROR] Invalid choice")
        return
    
    # Show final results
    show_final_stats()
    
    print("\n[COMPLETE] Scraping finished!")
    print("[TIP] Restart your Hunter app to see the new data in the dashboard!")

if __name__ == "__main__":
    main()