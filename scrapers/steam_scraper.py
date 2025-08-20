import requests
import time
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SteamScraper:
    def __init__(self):
        self.base_url = "https://store.steampowered.com/api"
        self.steam_spy_url = "https://steamspy.com/api.php"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_trending_games(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get trending games from Steam"""
        try:
            # Get top games from SteamSpy (public API)
            params = {
                'request': 'top100in2weeks',
                'format': 'json'
            }
            
            response = self.session.get(self.steam_spy_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            games = []
            
            for app_id, game_data in list(data.items())[:limit]:
                game_info = self._parse_steamspy_data(app_id, game_data)
                if game_info:
                    # Get additional details from Steam Store API
                    store_details = self.get_game_details(app_id)
                    if store_details:
                        game_info.update(store_details)
                    games.append(game_info)
                    time.sleep(0.5)  # Rate limiting
            
            logger.info(f"Scraped {len(games)} trending Steam games")
            return games
            
        except Exception as e:
            logger.error(f"Error scraping trending Steam games: {e}")
            return []
    
    def get_upcoming_games(self) -> List[Dict[str, Any]]:
        """Get upcoming games from Steam"""
        try:
            # Use Steam's featured categories API
            url = "https://store.steampowered.com/api/featuredcategories"
            
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            games = []
            
            # Get games from "coming soon" category
            coming_soon = data.get('coming_soon', {}).get('items', [])
            
            for item in coming_soon:
                game_info = self._parse_steam_featured_item(item)
                if game_info:
                    games.append(game_info)
            
            logger.info(f"Scraped {len(games)} upcoming Steam games")
            return games
            
        except Exception as e:
            logger.error(f"Error scraping upcoming Steam games: {e}")
            return []
    
    def get_game_details(self, steam_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific Steam game"""
        try:
            url = f"https://store.steampowered.com/api/appdetails"
            params = {
                'appids': steam_id,
                'format': 'json'
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            game_data = data.get(steam_id)
            
            if game_data and game_data.get('success') and game_data.get('data'):
                return self._parse_steam_app_details(game_data['data'])
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting Steam game details for {steam_id}: {e}")
            return None
    
    def _parse_steamspy_data(self, app_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse game data from SteamSpy API"""
        try:
            return {
                'steam_id': app_id,
                'title': data.get('name', ''),
                'developer': data.get('developer', ''),
                'publisher': data.get('publisher', ''),
                'genre': ', '.join(data.get('genre', '').split(',')[:3]),  # First 3 genres
                'tags': data.get('tags', {}),
                'player_count': data.get('owners', 0),
                'review_score': data.get('score_rank', 0),
                'price': data.get('price', 0) / 100 if data.get('price') else 0,  # Convert cents to dollars
                'last_updated': datetime.now()
            }
        except Exception as e:
            logger.error(f"Error parsing SteamSpy data: {e}")
            return {}
    
    def _parse_steam_featured_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse featured item from Steam API"""
        try:
            return {
                'steam_id': str(item.get('id', '')),
                'title': item.get('name', ''),
                'price': item.get('final_price', 0) / 100,  # Convert cents to dollars
                'discount_percent': item.get('discount_percent', 0),
                'header_image': item.get('header_image', ''),
                'last_updated': datetime.now()
            }
        except Exception as e:
            logger.error(f"Error parsing Steam featured item: {e}")
            return None
    
    def _parse_steam_app_details(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse detailed app data from Steam Store API"""
        try:
            release_date_info = data.get('release_date', {})
            release_date = None
            if release_date_info.get('date'):
                try:
                    release_date = datetime.strptime(release_date_info['date'], '%b %d, %Y')
                except:
                    pass
            
            # Parse genres
            genres = []
            for genre in data.get('genres', []):
                genres.append(genre.get('description', ''))
            
            # Parse categories (tags)
            categories = []
            for category in data.get('categories', []):
                categories.append(category.get('description', ''))
            
            return {
                'title': data.get('name', ''),
                'developer': ', '.join(data.get('developers', [])),
                'publisher': ', '.join(data.get('publishers', [])),
                'release_date': release_date,
                'genre': ', '.join(genres[:3]),  # First 3 genres
                'tags': categories,
                'description': data.get('short_description', ''),
                'header_image': data.get('header_image', ''),
                'price': data.get('price_overview', {}).get('final', 0) / 100 if data.get('price_overview') else 0,
                'discount_percent': data.get('price_overview', {}).get('discount_percent', 0),
                'metacritic_score': data.get('metacritic', {}).get('score', 0),
                'content_rating': data.get('content_descriptors', {}).get('notes', ''),
                'last_updated': datetime.now()
            }
        except Exception as e:
            logger.error(f"Error parsing Steam app details: {e}")
            return {}
    
    def get_steam_reviews(self, steam_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get reviews for a Steam game"""
        try:
            url = f"https://store.steampowered.com/appreviews/{steam_id}"
            params = {
                'json': 1,
                'language': 'english',
                'review_type': 'all',
                'purchase_type': 'all',
                'num_per_page': min(limit, 100),
                'cursor': '*'
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            reviews = []
            
            for review_data in data.get('reviews', []):
                review = self._parse_steam_review(review_data)
                if review:
                    reviews.append(review)
            
            logger.info(f"Scraped {len(reviews)} reviews for Steam game {steam_id}")
            return reviews
            
        except Exception as e:
            logger.error(f"Error getting Steam reviews for {steam_id}: {e}")
            return []
    
    def _parse_steam_review(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse Steam review data"""
        try:
            # Convert Steam recommendation to rating (1-5 scale)
            rating = 5 if data.get('voted_up') else 1
            
            return {
                'rating': rating,
                'review_text': data.get('review', ''),
                'helpful_votes': data.get('votes_up', 0),
                'total_votes': data.get('votes_up', 0) + data.get('votes_funny', 0),
                'playtime': data.get('author', {}).get('playtime_forever', 0),
                'timestamp': datetime.fromtimestamp(data.get('timestamp_created', 0)),
                'recommended': data.get('voted_up', False)
            }
        except Exception as e:
            logger.error(f"Error parsing Steam review: {e}")
            return None
    
    def calculate_hype_score(self, game_data: Dict[str, Any]) -> float:
        """Calculate hype score based on various metrics"""
        try:
            score = 0.0
            
            # Player count factor
            player_count = game_data.get('player_count', 0)
            if player_count > 1000000:
                score += 30
            elif player_count > 100000:
                score += 20
            elif player_count > 10000:
                score += 10
            
            # Review score factor
            review_score = game_data.get('review_score', 0)
            score += min(review_score / 100 * 25, 25)
            
            # Discount factor (higher discount might indicate promotion)
            discount = game_data.get('discount_percent', 0)
            if discount > 50:
                score += 15
            elif discount > 25:
                score += 10
            elif discount > 0:
                score += 5
            
            # Recent release bonus
            release_date = game_data.get('release_date')
            if release_date:
                days_since_release = (datetime.now() - release_date).days
                if days_since_release < 30:
                    score += 20
                elif days_since_release < 90:
                    score += 10
            
            return min(score, 100.0)
            
        except Exception as e:
            logger.error(f"Error calculating hype score: {e}")
            return 0.0