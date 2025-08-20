#!/usr/bin/env python3
"""
Script to populate the database with sample data for testing
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import random

def populate_sample_apps():
    """Add sample apps to the database"""
    db_path = Path('hunter_app.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    sample_apps = [
        ('1234567890', 'Super Puzzle Game', 'GameDev Studio', 'Games', 'us', 'https://example.com/icon1.png', 'Amazing puzzle game', datetime.now(), 15, 25, -10, 4.5, 1250, 0.0),
        ('2345678901', 'Fitness Tracker Pro', 'Health Apps Inc', 'Health & Fitness', 'us', 'https://example.com/icon2.png', 'Track your fitness goals', datetime.now(), 8, 12, -4, 4.2, 850, 2.99),
        ('3456789012', 'Photo Editor Max', 'Creative Solutions', 'Photo & Video', 'us', 'https://example.com/icon3.png', 'Professional photo editing', datetime.now(), 3, 1, 2, 4.7, 2100, 4.99),
        ('4567890123', 'Language Learning', 'EduTech Co', 'Education', 'us', 'https://example.com/icon4.png', 'Learn languages fast', datetime.now(), 22, 30, -8, 4.3, 920, 0.0),
        ('5678901234', 'Music Streaming Plus', 'Audio Innovations', 'Music', 'us', 'https://example.com/icon5.png', 'Stream music unlimited', datetime.now(), 5, 7, -2, 4.1, 5200, 9.99),
        ('6789012345', 'Weather Forecast Pro', 'Climate Apps', 'Weather', 'us', 'https://example.com/icon6.png', 'Accurate weather forecasts', datetime.now(), 11, 15, -4, 4.4, 780, 1.99),
        ('7890123456', 'Social Connect', 'Social Media Corp', 'Social Networking', 'us', 'https://example.com/icon7.png', 'Connect with friends', datetime.now(), 2, 3, -1, 3.9, 12500, 0.0),
        ('8901234567', 'Task Manager Elite', 'Productivity Plus', 'Productivity', 'us', 'https://example.com/icon8.png', 'Manage your tasks efficiently', datetime.now(), 18, 22, -4, 4.6, 430, 3.99),
        ('9012345678', 'Recipe Collection', 'Food Network Apps', 'Food & Drink', 'us', 'https://example.com/icon9.png', 'Thousands of recipes', datetime.now(), 31, 45, -14, 4.0, 650, 0.0),
        ('0123456789', 'Travel Planner', 'Journey Apps', 'Travel', 'us', 'https://example.com/icon10.png', 'Plan your perfect trip', datetime.now(), 14, 18, -4, 4.2, 320, 2.49)
    ]
    
    for app in sample_apps:
        cursor.execute('''
            INSERT OR REPLACE INTO apps 
            (app_store_id, title, developer, category, country, icon_url, description, release_date, 
             current_rank, previous_rank, rank_velocity, rating, review_count, price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', app)
    
    conn.commit()
    conn.close()
    print(f"Added {len(sample_apps)} sample apps to database")

def populate_sample_steam_games():
    """Add sample Steam games to the database"""
    db_path = Path('hunter_app.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    sample_games = [
        ('123456', 'Epic Adventure RPG', 'Fantasy Studios', 'Fantasy Games', datetime.now(), 'RPG', '{"tags": ["adventure", "rpg", "fantasy"]}', 29.99, 10.0, 8.5, 1250, 85.5, 5200),
        ('234567', 'Space Shooter Extreme', 'Action Devs', 'Action Games', datetime.now(), 'Action', '{"tags": ["action", "shooter", "space"]}', 19.99, 0.0, 7.8, 890, 78.2, 3400),
        ('345678', 'Racing Championship', 'Speed Studios', 'Racing Games', datetime.now(), 'Racing', '{"tags": ["racing", "cars", "simulation"]}', 39.99, 15.0, 9.1, 2100, 91.5, 8900),
        ('456789', 'Puzzle Master Pro', 'Brain Games Inc', 'Puzzle Games', datetime.now(), 'Puzzle', '{"tags": ["puzzle", "brain", "logic"]}', 9.99, 0.0, 8.2, 650, 82.8, 1200),
        ('567890', 'Survival Island', 'Wilderness Devs', 'Survival Games', datetime.now(), 'Survival', '{"tags": ["survival", "crafting", "island"]}', 24.99, 20.0, 8.7, 1800, 87.3, 4500)
    ]
    
    for game in sample_games:
        cursor.execute('''
            INSERT OR REPLACE INTO steam_games 
            (steam_id, title, developer, publisher, release_date, genre, tags, 
             price, discount_percent, review_score, review_count, hype_score, player_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', game)
    
    conn.commit()
    conn.close()
    print(f"Added {len(sample_games)} sample Steam games to database")

def populate_sample_events():
    """Add more relevant sample events"""
    db_path = Path('hunter_app.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Add some future events
    future_events = [
        ('Black Friday 2025', 'shopping', datetime(2025, 11, 29), datetime(2025, 11, 29), 'Major shopping event', 'manual_entry', 'global', '["shopping", "deals", "retail", "commerce"]'),
        ('Christmas 2025', 'holiday', datetime(2025, 12, 25), datetime(2025, 12, 25), 'Christmas holiday', 'manual_entry', 'global', '["christmas", "holiday", "seasonal", "family"]'),
        ('New Year 2026', 'holiday', datetime(2026, 1, 1), datetime(2026, 1, 1), 'New Year celebration', 'manual_entry', 'global', '["new year", "celebration", "resolution", "party"]'),
        ('Valentine Day 2026', 'holiday', datetime(2026, 2, 14), datetime(2026, 2, 14), 'Valentine\'s Day', 'manual_entry', 'global', '["valentine", "love", "romance", "gifts"]'),
        ('Summer Olympics 2028', 'sports', datetime(2028, 7, 21), datetime(2028, 8, 6), 'Summer Olympic Games', 'manual_entry', 'global', '["olympics", "sports", "competition", "international"]')
    ]
    
    for event in future_events:
        cursor.execute('''
            INSERT OR REPLACE INTO events 
            (name, event_type, start_date, end_date, description, source, region, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', event)
    
    conn.commit()
    conn.close()
    print(f"Added {len(future_events)} sample future events to database")

def show_database_summary():
    """Show summary of database contents"""
    db_path = Path('hunter_app.db')
    if not db_path.exists():
        print("Database not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Count all tables
    tables = ['apps', 'steam_games', 'events', 'users', 'reviews', 'alerts']
    
    print("\n=== Database Summary ===")
    for table in tables:
        try:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            print(f"{table.capitalize()}: {count} records")
        except:
            print(f"{table.capitalize()}: Table not found")
    
    conn.close()

def main():
    print("Populating Hunter database with sample data...")
    
    # Make sure database exists
    try:
        from models import database
        database.create_tables()
        print("Database tables initialized")
    except Exception as e:
        print(f"Error initializing database: {e}")
        return
    
    # Add sample data
    populate_sample_apps()
    populate_sample_steam_games()
    populate_sample_events()
    
    # Show summary
    show_database_summary()
    
    print("\n✅ Sample data populated successfully!")
    print("Now restart the app to see real data instead of mock data.")

if __name__ == "__main__":
    main()