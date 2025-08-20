"""
Dashboard utilities for getting real database statistics
"""

import sqlite3
from pathlib import Path
from typing import Dict, Any

def get_database_stats() -> Dict[str, Any]:
    """Get real statistics from the database"""
    stats = {
        'apps_count': 0,
        'steam_games_count': 0,
        'events_count': 0,
        'users_count': 0,
        'alerts_count': 0,
        'reviews_count': 0
    }
    
    try:
        # Main database stats
        db_path = Path('hunter_app.db')
        if db_path.exists():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Count apps
            cursor.execute('SELECT COUNT(*) FROM apps')
            stats['apps_count'] = cursor.fetchone()[0]
            
            # Count steam games
            cursor.execute('SELECT COUNT(*) FROM steam_games')
            stats['steam_games_count'] = cursor.fetchone()[0]
            
            # Count events
            cursor.execute('SELECT COUNT(*) FROM events')
            stats['events_count'] = cursor.fetchone()[0]
            
            # Count alerts
            cursor.execute('SELECT COUNT(*) FROM alerts')
            stats['alerts_count'] = cursor.fetchone()[0]
            
            # Count reviews
            cursor.execute('SELECT COUNT(*) FROM reviews')
            stats['reviews_count'] = cursor.fetchone()[0]
            
            conn.close()
        
        # Users database stats
        users_db_path = Path('users.db')
        if users_db_path.exists():
            conn = sqlite3.connect(users_db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM users')
            stats['users_count'] = cursor.fetchone()[0]
            
            conn.close()
            
    except Exception as e:
        print(f"Error getting database stats: {e}")
    
    return stats

def get_recent_apps(limit: int = 10) -> list:
    """Get recent apps from database"""
    apps = []
    
    try:
        db_path = Path('hunter_app.db')
        if db_path.exists():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT title, developer, category, current_rank, rating, review_count, last_updated
                FROM apps 
                ORDER BY last_updated DESC 
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            for row in rows:
                apps.append({
                    'title': row[0],
                    'developer': row[1],
                    'category': row[2],
                    'current_rank': row[3],
                    'rating': row[4],
                    'review_count': row[5],
                    'last_updated': row[6]
                })
            
            conn.close()
            
    except Exception as e:
        print(f"Error getting recent apps: {e}")
    
    return apps

def get_recent_steam_games(limit: int = 10) -> list:
    """Get recent steam games from database"""
    games = []
    
    try:
        db_path = Path('hunter_app.db')
        if db_path.exists():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT title, developer, genre, current_price, peak_players
                FROM steam_games 
                ORDER BY last_updated DESC 
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            for row in rows:
                games.append({
                    'title': row[0],
                    'developer': row[1],
                    'genre': row[2],
                    'current_price': row[3],
                    'peak_players': row[4]
                })
            
            conn.close()
            
    except Exception as e:
        print(f"Error getting recent steam games: {e}")
    
    return games

def get_upcoming_events(limit: int = 5) -> list:
    """Get upcoming events from database"""
    events = []
    
    try:
        db_path = Path('hunter_app.db')
        if db_path.exists():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT name, event_type, start_date, description, region
                FROM events 
                WHERE start_date >= datetime('now')
                ORDER BY start_date ASC 
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            for row in rows:
                events.append({
                    'name': row[0],
                    'event_type': row[1],
                    'start_date': row[2],
                    'description': row[3],
                    'region': row[4]
                })
            
            conn.close()
            
    except Exception as e:
        print(f"Error getting upcoming events: {e}")
    
    return events