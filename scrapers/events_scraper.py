import requests
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from bs4 import BeautifulSoup
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventsScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_upcoming_events(self) -> List[Dict[str, Any]]:
        """Get upcoming events from multiple sources"""
        all_events = []
        
        # Get different types of events
        holidays = self._get_holidays()
        movies = self._get_upcoming_movies()
        sports = self._get_sports_events()
        
        all_events.extend(holidays)
        all_events.extend(movies)
        all_events.extend(sports)
        
        # Sort by date
        all_events.sort(key=lambda x: x.get('start_date', datetime.now()))
        
        logger.info(f"Scraped {len(all_events)} upcoming events")
        return all_events
    
    def _get_holidays(self) -> List[Dict[str, Any]]:
        """Get major holidays and observances"""
        holidays = []
        
        # Static major holidays for current and next year
        current_year = datetime.now().year
        
        major_holidays = [
            {"name": "New Year's Day", "date": f"{current_year + 1}-01-01", "type": "holiday"},
            {"name": "Valentine's Day", "date": f"{current_year}-02-14", "type": "holiday"},
            {"name": "Easter", "date": f"{current_year}-04-21", "type": "holiday"},  # Approximate
            {"name": "Mother's Day", "date": f"{current_year}-05-12", "type": "holiday"},  # Second Sunday in May
            {"name": "Father's Day", "date": f"{current_year}-06-16", "type": "holiday"},  # Third Sunday in June
            {"name": "Independence Day (US)", "date": f"{current_year}-07-04", "type": "holiday"},
            {"name": "Halloween", "date": f"{current_year}-10-31", "type": "holiday"},
            {"name": "Thanksgiving (US)", "date": f"{current_year}-11-28", "type": "holiday"},  # Fourth Thursday
            {"name": "Black Friday", "date": f"{current_year}-11-29", "type": "shopping"},
            {"name": "Christmas", "date": f"{current_year}-12-25", "type": "holiday"},
            {"name": "Boxing Day", "date": f"{current_year}-12-26", "type": "holiday"},
            {"name": "New Year's Eve", "date": f"{current_year}-12-31", "type": "holiday"},
        ]
        
        for holiday in major_holidays:
            try:
                event_date = datetime.strptime(holiday["date"], "%Y-%m-%d")
                if event_date >= datetime.now():
                    holidays.append({
                        'name': holiday["name"],
                        'event_type': holiday["type"],
                        'start_date': event_date,
                        'end_date': event_date,
                        'description': f"Annual {holiday['type']}: {holiday['name']}",
                        'source': 'static_calendar',
                        'region': 'global',
                        'tags': ['annual', holiday["type"], 'seasonal']
                    })
            except Exception as e:
                logger.error(f"Error processing holiday {holiday}: {e}")
        
        return holidays
    
    def _get_upcoming_movies(self) -> List[Dict[str, Any]]:
        """Get upcoming movie releases"""
        movies = []
        
        try:
            # Using a simple approach - in production you'd use TMDB API
            # This is a mock implementation with some major expected releases
            upcoming_movies = [
                {"title": "Major Blockbuster 1", "date": "2024-06-15", "genre": "action"},
                {"title": "Animated Family Film", "date": "2024-07-20", "genre": "animation"},
                {"title": "Horror Sequel", "date": "2024-10-13", "genre": "horror"},
                {"title": "Holiday Romance", "date": "2024-12-01", "genre": "romance"},
            ]
            
            for movie in upcoming_movies:
                try:
                    release_date = datetime.strptime(movie["date"], "%Y-%m-%d")
                    if release_date >= datetime.now():
                        movies.append({
                            'name': movie["title"],
                            'event_type': 'movie_release',
                            'start_date': release_date,
                            'end_date': release_date + timedelta(days=7),  # Opening week
                            'description': f"Movie release: {movie['title']} ({movie['genre']})",
                            'source': 'movie_calendar',
                            'region': 'global',
                            'tags': ['movie', 'entertainment', movie['genre']]
                        })
                except Exception as e:
                    logger.error(f"Error processing movie {movie}: {e}")
        
        except Exception as e:
            logger.error(f"Error getting upcoming movies: {e}")
        
        return movies
    
    def _get_sports_events(self) -> List[Dict[str, Any]]:
        """Get major sports events"""
        sports_events = []
        
        try:
            # Major recurring sports events
            current_year = datetime.now().year
            
            major_sports = [
                {"name": "Super Bowl", "date": f"{current_year + 1}-02-11", "sport": "football"},
                {"name": "March Madness", "date": f"{current_year + 1}-03-15", "sport": "basketball"},
                {"name": "World Cup Qualifiers", "date": f"{current_year}-06-01", "sport": "soccer"},
                {"name": "Olympics", "date": f"{current_year + 2}-07-23", "sport": "multi"},
                {"name": "NBA Finals", "date": f"{current_year}-06-06", "sport": "basketball"},
                {"name": "World Series", "date": f"{current_year}-10-24", "sport": "baseball"},
            ]
            
            for event in major_sports:
                try:
                    event_date = datetime.strptime(event["date"], "%Y-%m-%d")
                    if event_date >= datetime.now():
                        sports_events.append({
                            'name': event["name"],
                            'event_type': 'sports',
                            'start_date': event_date,
                            'end_date': event_date + timedelta(days=7),
                            'description': f"Major sports event: {event['name']}",
                            'source': 'sports_calendar',
                            'region': 'global',
                            'tags': ['sports', event['sport'], 'competition']
                        })
                except Exception as e:
                    logger.error(f"Error processing sports event {event}: {e}")
        
        except Exception as e:
            logger.error(f"Error getting sports events: {e}")
        
        return sports_events
    
    def get_trending_topics(self) -> List[Dict[str, Any]]:
        """Get trending topics and viral events"""
        trending = []
        
        try:
            # This would typically integrate with social media APIs
            # For now, we'll use a mock implementation
            
            mock_trends = [
                {"name": "Viral Dance Challenge", "type": "social", "popularity": 95},
                {"name": "Tech Product Launch", "type": "technology", "popularity": 87},
                {"name": "Celebrity News", "type": "entertainment", "popularity": 78},
                {"name": "Gaming Tournament", "type": "gaming", "popularity": 82},
            ]
            
            for trend in mock_trends:
                trending.append({
                    'name': trend["name"],
                    'event_type': 'trending',
                    'start_date': datetime.now(),
                    'end_date': datetime.now() + timedelta(days=14),
                    'description': f"Trending topic: {trend['name']}",
                    'source': 'social_media',
                    'region': 'global',
                    'tags': ['trending', trend['type'], 'viral']
                })
        
        except Exception as e:
            logger.error(f"Error getting trending topics: {e}")
        
        return trending
    
    def match_events_to_apps(self, events: List[Dict[str, Any]], 
                           apps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Match events to relevant apps based on keywords and themes"""
        matches = []
        
        try:
            for event in events:
                event_keywords = self._extract_keywords(event)
                
                for app in apps:
                    app_keywords = self._extract_app_keywords(app)
                    
                    similarity_score = self._calculate_keyword_similarity(
                        event_keywords, app_keywords
                    )
                    
                    if similarity_score > 0.3:  # Threshold for relevance
                        matches.append({
                            'event_id': event.get('name', ''),
                            'app_id': app.get('app_store_id', ''),
                            'similarity_score': similarity_score,
                            'match_type': 'keyword',
                            'matched_keywords': list(set(event_keywords) & set(app_keywords))
                        })
        
        except Exception as e:
            logger.error(f"Error matching events to apps: {e}")
        
        return matches
    
    def _extract_keywords(self, event: Dict[str, Any]) -> List[str]:
        """Extract keywords from event data"""
        keywords = []
        
        # Extract from name and description
        text = f"{event.get('name', '')} {event.get('description', '')}"
        
        # Simple keyword extraction (in production, use NLP)
        common_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        words = [word.lower().strip('.,!?()[]{}":;') for word in text.split()]
        keywords = [word for word in words if len(word) > 3 and word not in common_words]
        
        # Add tags
        if event.get('tags'):
            keywords.extend(event['tags'])
        
        return list(set(keywords))
    
    def _extract_app_keywords(self, app: Dict[str, Any]) -> List[str]:
        """Extract keywords from app data"""
        keywords = []
        
        # Extract from title, description, and category
        text = f"{app.get('title', '')} {app.get('description', '')} {app.get('category', '')}"
        
        common_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'app', 'game']
        words = [word.lower().strip('.,!?()[]{}":;') for word in text.split()]
        keywords = [word for word in words if len(word) > 3 and word not in common_words]
        
        # Add category and genre
        if app.get('genres'):
            keywords.extend([genre.lower() for genre in app['genres']])
        
        return list(set(keywords))
    
    def _calculate_keyword_similarity(self, keywords1: List[str], 
                                    keywords2: List[str]) -> float:
        """Calculate similarity between two keyword lists"""
        if not keywords1 or not keywords2:
            return 0.0
        
        set1 = set(keywords1)
        set2 = set(keywords2)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0