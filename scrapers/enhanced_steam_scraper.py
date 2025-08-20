import requests
import time
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import random
from dataclasses import dataclass
from bs4 import BeautifulSoup
import re
from config import config
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.robust_logger import get_logger, log_method_calls

# Optional async imports
try:
    import asyncio
    import aiohttp
    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False

# Initialize robust logger
logger = get_logger("steam_scraper")

@dataclass
class SteamCategory:
    name: str
    tag_id: int
    description: str

class EnhancedSteamScraper:
    def __init__(self):
        # Initialize robust logging
        self.logger = get_logger("steam_scraper")
        self.logger.info("EnhancedSteamScraper initialized")
        self.base_url = "https://store.steampowered.com"
        self.api_url = "https://api.steampowered.com"
        self.steamspy_url = "https://steamspy.com/api.php"
        self.steamcharts_url = "https://steamcharts.com"
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # Steam categories and tags for comprehensive scraping
        self.categories = [
            SteamCategory("Action", 19, "Fast-paced games with combat"),
            SteamCategory("Adventure", 21, "Story-driven exploration games"),
            SteamCategory("Casual", 597, "Easy to play games"),
            SteamCategory("Indie", 492, "Independent developer games"),
            SteamCategory("Massively Multiplayer", 128, "MMO games"),
            SteamCategory("Racing", 699, "Vehicle racing games"),
            SteamCategory("RPG", 122, "Role-playing games"),
            SteamCategory("Simulation", 599, "Life and world simulation"),
            SteamCategory("Sports", 701, "Sports simulation games"),
            SteamCategory("Strategy", 9, "Strategic thinking games"),
            SteamCategory("Early Access", 493, "Games in development"),
            SteamCategory("Free to Play", 113, "Free games"),
            SteamCategory("VR Supported", 21978, "Virtual Reality games"),
            SteamCategory("Multiplayer", 3859, "Multiplayer games"),
            SteamCategory("Single-player", 4182, "Single player games"),
            SteamCategory("Co-op", 1685, "Cooperative multiplayer"),
            SteamCategory("Online Co-Op", 3843, "Online cooperative play"),
            SteamCategory("Local Co-Op", 3841, "Local cooperative play"),
            SteamCategory("PvP", 1775, "Player vs Player"),
            SteamCategory("Competitive", 3878, "Competitive gaming")
        ]
        
        # Different data sources for comprehensive coverage
        self.data_sources = {
            'steam_store': 'Official Steam Store',
            'steam_api': 'Steam Web API',
            'steamspy': 'SteamSpy Analytics',
            'steamcharts': 'SteamCharts Player Data',
            'steam_rss': 'Steam RSS Feeds'
        }
        
        # Rate limiting
        self.last_request_time = 0
        self.request_count = 0
        self.rate_limit_reset_time = time.time() + 3600
    
    def rate_limit(self, delay: float = None):
        """Implement rate limiting for Steam requests"""
        current_time = time.time()
        
        if current_time > self.rate_limit_reset_time:
            self.request_count = 0
            self.rate_limit_reset_time = current_time + 3600
        
        # Steam is more restrictive, max 200 requests per hour
        if self.request_count >= 200:
            sleep_time = self.rate_limit_reset_time - current_time
            if sleep_time > 0:
                logger.info(f"Steam rate limit reached, sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                self.request_count = 0
                self.rate_limit_reset_time = time.time() + 3600
        
        # Default delay
        if delay is None:
            delay = config.SCRAPER_DELAY * 2  # Steam needs more delay
        
        time_since_last = current_time - self.last_request_time
        if time_since_last < delay:
            time.sleep(delay - time_since_last)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def make_request(self, url: str, params: Dict[str, Any] = None, retries: int = 3) -> Optional[requests.Response]:
        """Make request with retry logic"""
        for attempt in range(retries):
            try:
                self.rate_limit()
                
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Steam request failed (attempt {attempt + 1}/{retries}): {e}")
                if attempt == retries - 1:
                    logger.error(f"All retry attempts failed for Steam URL: {url}")
                    return None
                
                wait_time = (2 ** attempt) + random.uniform(1, 3)
                time.sleep(wait_time)
        
        return None
    
    def scrape_comprehensive_trending(self) -> Dict[str, Any]:
        """Comprehensive trending analysis from multiple sources"""
        logger.info("Starting comprehensive Steam trending analysis")
        
        trending_data = {
            'top_sellers': [],
            'new_releases': [],
            'trending_games': [],
            'most_played': [],
            'upcoming_releases': [],
            'vr_trending': [],
            'free_games': [],
            'early_access': [],
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        try:
            # Get top sellers
            trending_data['top_sellers'] = self.get_top_sellers()
            
            # Get new and trending
            trending_data['new_releases'] = self.get_new_releases()
            trending_data['trending_games'] = self.get_trending_games()
            
            # Get most played (from SteamSpy)
            trending_data['most_played'] = self.get_most_played_games()
            
            # Get upcoming releases
            trending_data['upcoming_releases'] = self.get_upcoming_releases()
            
            # Get VR games
            trending_data['vr_trending'] = self.get_vr_trending()
            
            # Get free games
            trending_data['free_games'] = self.get_free_to_play_trending()
            
            # Get early access
            trending_data['early_access'] = self.get_early_access_trending()
            
            # Calculate comprehensive hype scores
            all_games = self.aggregate_and_score_games(trending_data)
            trending_data['comprehensive_ranking'] = all_games
            
            logger.info(f"Comprehensive trending analysis complete: {len(all_games)} games analyzed")
            
        except Exception as e:
            logger.error(f"Error in comprehensive trending analysis: {e}")
        
        return trending_data
    
    def get_top_sellers(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get Steam top sellers using SteamSpy API with robust validation"""
        self.logger.info("Starting Steam top sellers scraping", limit=limit)
        
        try:
            # Use SteamSpy API for reliable data
            params = {
                'request': 'top100in2weeks',
                'format': 'json'
            }
            
            self.logger.log_scraping_attempt("SteamSpy_API", self.steamspy_url, params)
            start_time = time.time()
            
            response = self.make_request(self.steamspy_url, params)
            if not response:
                self.logger.warning("Failed to get SteamSpy response")
                return []
            
            data = response.json()
            games = []
            
            count = 0
            for app_id, game_data in data.items():
                if count >= limit:
                    break
                
                # Parse and validate each game
                game_info = self._parse_steamspy_game(app_id, game_data, 'top_seller')
                if game_info and self._validate_steam_game(game_info):
                    games.append(game_info)
                    count += 1
            
            response_time = time.time() - start_time
            self.logger.log_scraping_success(
                "SteamSpy_API",
                self.steamspy_url,
                len(games),
                response_time,
                games[0] if games else None
            )
            
            return games
            
        except Exception as e:
            self.logger.log_scraping_failure("SteamSpy_API", self.steamspy_url, e)
            return []
    
    def get_new_releases(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get new Steam releases"""
        try:
            url = f"{self.base_url}/search/results/"
            params = {
                'query': '',
                'start': 0,
                'count': limit,
                'dynamic_data': '',
                'sort_by': 'Released_DESC',
                'category1': '998',
                'infinite': '1'
            }
            
            response = self.make_request(url, params)
            if not response:
                return []
            
            games = self.parse_search_results(response.text, "new_release")
            logger.info(f"Retrieved {len(games)} new releases from Steam")
            return games
            
        except Exception as e:
            logger.error(f"Error getting Steam new releases: {e}")
            return []
    
    def get_trending_games(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get currently trending games using sample data"""
        try:
            # Sample trending games data
            trending_games = [
                {
                    'steam_id': '1938090',
                    'title': 'Call of Duty: Modern Warfare II',
                    'price': 69.99,
                    'is_free': False,
                    'review_score': 7,
                    'review_summary': 'Mixed',
                    'total_reviews': 45000,
                    'positive_percentage': 68,
                    'tags': ['FPS', 'Multiplayer', 'Action'],
                    'source': 'trending',
                    'scraped_at': datetime.now().isoformat(),
                    'store_url': f'{self.base_url}/app/1938090/'
                },
                {
                    'steam_id': '1966720',
                    'title': 'Spider-Man: Miles Morales',
                    'price': 49.99,
                    'is_free': False,
                    'review_score': 9,
                    'review_summary': 'Very Positive',
                    'total_reviews': 25000,
                    'positive_percentage': 95,
                    'tags': ['Action', 'Adventure', 'Superhero'],
                    'source': 'trending',
                    'scraped_at': datetime.now().isoformat(),
                    'store_url': f'{self.base_url}/app/1966720/'
                },
                {
                    'steam_id': '1817070',
                    'title': 'Marvels Spider-Man Remastered',
                    'price': 59.99,
                    'is_free': False,
                    'review_score': 9,
                    'review_summary': 'Very Positive',
                    'total_reviews': 78000,
                    'positive_percentage': 96,
                    'tags': ['Action', 'Adventure', 'Open World'],
                    'source': 'trending',
                    'scraped_at': datetime.now().isoformat(),
                    'store_url': f'{self.base_url}/app/1817070/'
                }
            ]
            
            games = trending_games[:min(limit, len(trending_games))]
            logger.info(f"Retrieved {len(games)} trending games from Steam (sample data)")
            return games
            
        except Exception as e:
            logger.error(f"Error getting Steam trending games: {e}")
            return []
    
    def get_most_played_games(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get most played games from SteamSpy"""
        try:
            params = {
                'request': 'top100in2weeks',
                'format': 'json'
            }
            
            response = self.make_request(self.steamspy_url, params)
            if not response:
                return []
            
            data = response.json()
            games = []
            
            count = 0
            for app_id, game_data in data.items():
                if count >= limit:
                    break
                
                game_info = self.parse_steamspy_data(app_id, game_data)
                if game_info:
                    game_info['source'] = 'most_played'
                    games.append(game_info)
                    count += 1
            
            logger.info(f"Retrieved {len(games)} most played games from SteamSpy")
            return games
            
        except Exception as e:
            logger.error(f"Error getting most played games: {e}")
            return []
    
    def get_upcoming_releases(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """Get upcoming Steam releases"""
        try:
            url = f"{self.base_url}/search/results/"
            params = {
                'query': '',
                'start': 0,
                'count': 100,
                'dynamic_data': '',
                'sort_by': 'Released_DESC',
                'category1': '998',
                'category2': '10',  # Upcoming
                'infinite': '1'
            }
            
            response = self.make_request(url, params)
            if not response:
                return []
            
            games = self.parse_search_results(response.text, "upcoming")
            
            # Filter to only include games releasing in the next X days
            filtered_games = []
            cutoff_date = datetime.now() + timedelta(days=days_ahead)
            
            for game in games:
                release_date = game.get('release_date')
                if release_date and isinstance(release_date, datetime):
                    if release_date <= cutoff_date:
                        filtered_games.append(game)
            
            logger.info(f"Retrieved {len(filtered_games)} upcoming releases from Steam")
            return filtered_games
            
        except Exception as e:
            logger.error(f"Error getting upcoming releases: {e}")
            return []
    
    def get_vr_trending(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get trending VR games"""
        try:
            url = f"{self.base_url}/search/results/"
            params = {
                'query': '',
                'start': 0,
                'count': limit,
                'dynamic_data': '',
                'sort_by': 'Trending_DESC',
                'category1': '998',
                'vrsupport': '401',  # VR Supported
                'infinite': '1'
            }
            
            response = self.make_request(url, params)
            if not response:
                return []
            
            games = self.parse_search_results(response.text, "vr_trending")
            logger.info(f"Retrieved {len(games)} VR trending games from Steam")
            return games
            
        except Exception as e:
            logger.error(f"Error getting VR trending games: {e}")
            return []
    
    def get_free_to_play_trending(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get trending free-to-play games"""
        try:
            url = f"{self.base_url}/search/results/"
            params = {
                'query': '',
                'start': 0,
                'count': limit,
                'dynamic_data': '',
                'sort_by': 'Trending_DESC',
                'category1': '998',
                'genre': '113',  # Free to Play
                'infinite': '1'
            }
            
            response = self.make_request(url, params)
            if not response:
                return []
            
            games = self.parse_search_results(response.text, "free_to_play")
            logger.info(f"Retrieved {len(games)} F2P trending games from Steam")
            return games
            
        except Exception as e:
            logger.error(f"Error getting F2P trending games: {e}")
            return []
    
    def get_early_access_trending(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get trending early access games"""
        try:
            url = f"{self.base_url}/search/results/"
            params = {
                'query': '',
                'start': 0,
                'count': limit,
                'dynamic_data': '',
                'sort_by': 'Trending_DESC',
                'category1': '998',
                'category2': '29',  # Early Access
                'infinite': '1'
            }
            
            response = self.make_request(url, params)
            if not response:
                return []
            
            games = self.parse_search_results(response.text, "early_access")
            logger.info(f"Retrieved {len(games)} Early Access trending games from Steam")
            return games
            
        except Exception as e:
            logger.error(f"Error getting Early Access trending games: {e}")
            return []
    
    def parse_search_results(self, html_content: str, source: str) -> List[Dict[str, Any]]:
        """Parse Steam search results HTML"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            games = []
            
            # Find all game result rows
            game_rows = soup.find_all('a', {'class': 'search_result_row'})
            
            for row in game_rows:
                game_data = self.parse_game_row(row, source)
                if game_data:
                    games.append(game_data)
            
            return games
            
        except Exception as e:
            logger.error(f"Error parsing search results: {e}")
            return []
    
    def parse_game_row(self, row, source: str) -> Optional[Dict[str, Any]]:
        """Parse individual game row from search results"""
        try:
            # Extract app ID from data-ds-appid
            app_id = row.get('data-ds-appid')
            if not app_id:
                return None
            
            # Game title
            title_elem = row.find('span', {'class': 'title'})
            title = title_elem.text.strip() if title_elem else "Unknown"
            
            # Release date
            release_elem = row.find('div', {'class': 'col search_released responsive_secondrow'})
            release_date = self.parse_release_date(release_elem.text.strip()) if release_elem else None
            
            # Price info
            price_elem = row.find('div', {'class': 'col search_price_discount_combined responsive_secondrow'})
            price_info = self.parse_price_info(price_elem) if price_elem else {}
            
            # Review score
            review_elem = row.find('span', {'class': 'search_review_summary'})
            review_summary = review_elem.get('data-tooltip-html', '') if review_elem else ''
            review_data = self.parse_review_summary(review_summary)
            
            # Tags
            tags = []
            tag_elems = row.find_all('span', {'class': 'app_tag'})
            for tag in tag_elems:
                if tag.text:
                    tags.append(tag.text.strip())
            
            # Screenshots
            img_elem = row.find('div', {'class': 'col search_capsule'})
            screenshot_url = ""
            if img_elem:
                img_tag = img_elem.find('img')
                if img_tag and img_tag.get('src'):
                    screenshot_url = img_tag['src']
            
            game_data = {
                'steam_id': app_id,
                'title': title,
                'release_date': release_date,
                'price': price_info.get('current_price', 0.0),
                'original_price': price_info.get('original_price', 0.0),
                'discount_percent': price_info.get('discount_percent', 0),
                'is_free': price_info.get('is_free', False),
                'review_score': review_data.get('score', 0),
                'review_summary': review_data.get('summary', 'Unknown'),
                'total_reviews': review_data.get('total_reviews', 0),
                'positive_percentage': review_data.get('positive_percentage', 0),
                'tags': tags,
                'screenshot_url': screenshot_url,
                'source': source,
                'scraped_at': datetime.now().isoformat(),
                'store_url': f"{self.base_url}/app/{app_id}/"
            }
            
            return game_data
            
        except Exception as e:
            logger.error(f"Error parsing game row: {e}")
            return None
    
    def parse_price_info(self, price_elem) -> Dict[str, Any]:
        """Parse price information from price element"""
        try:
            price_info = {
                'current_price': 0.0,
                'original_price': 0.0,
                'discount_percent': 0,
                'is_free': False
            }
            
            # Check if free
            if 'Free' in price_elem.text or 'Free to Play' in price_elem.text:
                price_info['is_free'] = True
                return price_info
            
            # Look for discount
            discount_elem = price_elem.find('div', {'class': 'col search_discount responsive_secondrow'})
            if discount_elem:
                discount_text = discount_elem.text.strip()
                if discount_text and discount_text.startswith('-'):
                    price_info['discount_percent'] = int(discount_text.replace('-', '').replace('%', ''))
            
            # Current price
            current_price_elem = price_elem.find('div', {'class': 'col search_price discounted responsive_secondrow'})
            if not current_price_elem:
                current_price_elem = price_elem.find('div', {'class': 'col search_price responsive_secondrow'})
            
            if current_price_elem:
                price_text = current_price_elem.text.strip()
                price_match = re.search(r'\$?(\d+\.?\d*)', price_text)
                if price_match:
                    price_info['current_price'] = float(price_match.group(1))
            
            # Original price (if discounted)
            if price_info['discount_percent'] > 0:
                original_price = price_info['current_price'] / (1 - price_info['discount_percent'] / 100)
                price_info['original_price'] = round(original_price, 2)
            else:
                price_info['original_price'] = price_info['current_price']
            
            return price_info
            
        except Exception as e:
            logger.error(f"Error parsing price info: {e}")
            return {'current_price': 0.0, 'original_price': 0.0, 'discount_percent': 0, 'is_free': False}
    
    def parse_review_summary(self, review_html: str) -> Dict[str, Any]:
        """Parse review summary from tooltip HTML"""
        try:
            if not review_html:
                return {'score': 0, 'summary': 'No reviews', 'total_reviews': 0, 'positive_percentage': 0}
            
            # Extract review percentage and count using regex
            percentage_match = re.search(r'(\d+)%', review_html)
            count_match = re.search(r'([\d,]+)\s+user\s+reviews', review_html)
            
            positive_percentage = int(percentage_match.group(1)) if percentage_match else 0
            total_reviews = int(count_match.group(1).replace(',', '')) if count_match else 0
            
            # Determine review summary
            if positive_percentage >= 95:
                summary = "Overwhelmingly Positive"
                score = 10
            elif positive_percentage >= 85:
                summary = "Very Positive"
                score = 9
            elif positive_percentage >= 80:
                summary = "Positive"
                score = 8
            elif positive_percentage >= 70:
                summary = "Mostly Positive"
                score = 7
            elif positive_percentage >= 40:
                summary = "Mixed"
                score = 5
            elif positive_percentage >= 20:
                summary = "Mostly Negative"
                score = 3
            else:
                summary = "Negative"
                score = 2
            
            return {
                'score': score,
                'summary': summary,
                'total_reviews': total_reviews,
                'positive_percentage': positive_percentage
            }
            
        except Exception as e:
            logger.error(f"Error parsing review summary: {e}")
            return {'score': 0, 'summary': 'Unknown', 'total_reviews': 0, 'positive_percentage': 0}
    
    def parse_release_date(self, date_str: str) -> Optional[datetime]:
        """Parse release date string"""
        try:
            if not date_str or date_str.strip() in ['', 'Coming Soon', 'TBA']:
                return None
            
            # Handle various date formats
            date_str = date_str.strip()
            
            # Remove common prefixes
            date_str = date_str.replace('Released ', '').replace('Coming ', '')
            
            # Try different date formats
            formats = [
                "%b %d, %Y",      # Jan 1, 2024
                "%B %d, %Y",      # January 1, 2024
                "%d %b %Y",       # 1 Jan 2024
                "%d %B %Y",       # 1 January 2024
                "%Y-%m-%d",       # 2024-01-01
                "%m/%d/%Y",       # 01/01/2024
                "%b %Y",          # Jan 2024
                "%B %Y",          # January 2024
                "%Y"              # 2024
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # If all parsing fails, return None
            return None
            
        except Exception as e:
            logger.error(f"Error parsing release date '{date_str}': {e}")
            return None
    
    def parse_steamspy_data(self, app_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse game data from SteamSpy API"""
        try:
            return {
                'steam_id': app_id,
                'title': data.get('name', 'Unknown'),
                'developer': data.get('developer', 'Unknown'),
                'publisher': data.get('publisher', 'Unknown'),
                'genre': data.get('genre', ''),
                'tags': data.get('tags', {}),
                'owners': data.get('owners', '0-20,000'),
                'owners_variance': data.get('owners_variance', 0),
                'players_forever': data.get('players_forever', 0),
                'players_2weeks': data.get('players_2weeks', 0),
                'average_forever': data.get('average_forever', 0),
                'average_2weeks': data.get('average_2weeks', 0),
                'median_forever': data.get('median_forever', 0),
                'median_2weeks': data.get('median_2weeks', 0),
                'price': data.get('price', 0),
                'initial_price': data.get('initialprice', 0),
                'discount': data.get('discount', 0),
                'languages': data.get('languages', ''),
                'ccu': data.get('ccu', 0),  # Concurrent users
                'score_rank': data.get('score_rank', 0),
                'positive': data.get('positive', 0),
                'negative': data.get('negative', 0),
                'estimated_owners': self.parse_owners_range(data.get('owners', '0-20,000')),
                'hype_score': self.calculate_steamspy_hype_score(data),
                'source': 'steamspy',
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error parsing SteamSpy data: {e}")
            return None
    
    def parse_owners_range(self, owners_str: str) -> int:
        """Parse owners range string to estimated number"""
        try:
            if not owners_str:
                return 0
            
            # Extract numbers from ranges like "200,000 .. 500,000"
            numbers = re.findall(r'[\d,]+', owners_str.replace('..', '-'))
            if len(numbers) >= 2:
                # Take the average of the range
                min_owners = int(numbers[0].replace(',', ''))
                max_owners = int(numbers[1].replace(',', ''))
                return (min_owners + max_owners) // 2
            elif len(numbers) == 1:
                return int(numbers[0].replace(',', ''))
            
            return 0
            
        except Exception:
            return 0
    
    def calculate_steamspy_hype_score(self, data: Dict[str, Any]) -> float:
        """Calculate hype score from SteamSpy data"""
        try:
            score = 0.0
            
            # Player count factor (0-40 points)
            players_2weeks = data.get('players_2weeks', 0)
            if players_2weeks > 100000:
                score += 40
            elif players_2weeks > 50000:
                score += 30
            elif players_2weeks > 10000:
                score += 20
            elif players_2weeks > 1000:
                score += 10
            
            # Ownership factor (0-30 points)
            owners_str = data.get('owners', '0-20,000')
            estimated_owners = self.parse_owners_range(owners_str)
            if estimated_owners > 1000000:
                score += 30
            elif estimated_owners > 500000:
                score += 25
            elif estimated_owners > 100000:
                score += 20
            elif estimated_owners > 50000:
                score += 15
            elif estimated_owners > 10000:
                score += 10
            
            # Review score factor (0-20 points)
            positive = data.get('positive', 0)
            negative = data.get('negative', 0)
            total_reviews = positive + negative
            if total_reviews > 0:
                positive_ratio = positive / total_reviews
                score += positive_ratio * 20
            
            # Concurrent users factor (0-10 points)
            ccu = data.get('ccu', 0)
            if ccu > 50000:
                score += 10
            elif ccu > 10000:
                score += 7
            elif ccu > 1000:
                score += 5
            elif ccu > 100:
                score += 3
            
            return min(score, 100)
            
        except Exception as e:
            logger.error(f"Error calculating hype score: {e}")
            return 0.0
    
    def aggregate_and_score_games(self, trending_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Aggregate games from all sources and calculate comprehensive scores"""
        try:
            all_games = {}
            
            # Combine all game sources
            for source_key, games_list in trending_data.items():
                if source_key == 'analysis_timestamp' or source_key == 'comprehensive_ranking':
                    continue
                
                for game in games_list:
                    steam_id = game.get('steam_id')
                    if not steam_id:
                        continue
                    
                    if steam_id not in all_games:
                        all_games[steam_id] = game.copy()
                        all_games[steam_id]['sources'] = []
                        all_games[steam_id]['comprehensive_score'] = 0
                    
                    all_games[steam_id]['sources'].append(source_key)
            
            # Calculate comprehensive scores
            scored_games = []
            for steam_id, game in all_games.items():
                comprehensive_score = self.calculate_comprehensive_score(game)
                game['comprehensive_score'] = comprehensive_score
                scored_games.append(game)
            
            # Sort by comprehensive score
            scored_games.sort(key=lambda x: x['comprehensive_score'], reverse=True)
            
            return scored_games[:100]  # Return top 100
            
        except Exception as e:
            logger.error(f"Error aggregating and scoring games: {e}")
            return []
    
    def calculate_comprehensive_score(self, game: Dict[str, Any]) -> float:
        """Calculate comprehensive hype/trending score"""
        try:
            score = 0.0
            
            # Source diversity bonus (games appearing in multiple lists)
            sources = game.get('sources', [])
            source_bonus = min(len(sources) * 15, 45)  # Max 45 points for appearing in 3+ sources
            score += source_bonus
            
            # Review score factor
            review_score = game.get('review_score', 0)
            score += review_score * 2  # Max 20 points
            
            # Price/discount factor
            discount = game.get('discount_percent', 0)
            if discount > 50:
                score += 15
            elif discount > 25:
                score += 10
            elif discount > 0:
                score += 5
            
            # Free games get a small boost
            if game.get('is_free', False):
                score += 10
            
            # Recent release bonus
            release_date = game.get('release_date')
            if release_date and isinstance(release_date, datetime):
                days_since_release = (datetime.now() - release_date).days
                if days_since_release < 7:
                    score += 20
                elif days_since_release < 30:
                    score += 15
                elif days_since_release < 90:
                    score += 10
            
            # SteamSpy specific data
            if 'players_2weeks' in game:
                players_2weeks = game.get('players_2weeks', 0)
                if players_2weeks > 10000:
                    score += 10
                elif players_2weeks > 1000:
                    score += 5
            
            return min(score, 100)
            
        except Exception as e:
            logger.error(f"Error calculating comprehensive score: {e}")
            return 0.0
    
    def _parse_steamspy_game(self, app_id: str, game_data: Dict[str, Any], source: str) -> Optional[Dict[str, Any]]:
        """Parse SteamSpy game data with validation"""
        try:
            # Expected fields for validation
            expected_fields = [
                'steam_id', 'title', 'owners_estimate', 'players_2weeks', 
                'positive_reviews', 'negative_reviews', 'source'
            ]
            
            # Calculate review metrics
            positive = game_data.get('positive', 0)
            negative = game_data.get('negative', 0)
            total_reviews = positive + negative
            positive_percentage = (positive / total_reviews * 100) if total_reviews > 0 else 0
            
            # Calculate review score (0-10 scale)
            if positive_percentage >= 95:
                review_score = 10
                review_summary = "Overwhelmingly Positive"
            elif positive_percentage >= 80:
                review_score = 8
                review_summary = "Very Positive"
            elif positive_percentage >= 70:
                review_score = 7
                review_summary = "Mostly Positive"
            elif positive_percentage >= 40:
                review_score = 5
                review_summary = "Mixed"
            else:
                review_score = 3
                review_summary = "Mostly Negative"
            
            game_info = {
                'steam_id': str(app_id),
                'title': game_data.get('name', 'Unknown').strip(),
                'developer': game_data.get('developer', 'Unknown').strip(),
                'publisher': game_data.get('publisher', 'Unknown').strip(),
                'genre': game_data.get('genre', 'Unknown').strip(),
                'owners_estimate': self.parse_owners_range(game_data.get('owners', '0-20,000')),
                'players_2weeks': game_data.get('players_2weeks', 0),
                'players_forever': game_data.get('players_forever', 0),
                'average_playtime_2weeks': game_data.get('average_2weeks', 0),
                'average_playtime_forever': game_data.get('average_forever', 0),
                'positive_reviews': positive,
                'negative_reviews': negative,
                'total_reviews': total_reviews,
                'positive_percentage': round(positive_percentage, 2),
                'review_score': review_score,
                'review_summary': review_summary,
                'price': game_data.get('price', 0),
                'initial_price': game_data.get('initialprice', 0),
                'discount': game_data.get('discount', 0),
                'ccu': game_data.get('ccu', 0),  # Concurrent users
                'languages': game_data.get('languages', ''),
                'tags': game_data.get('tags', {}),
                'source': source,
                'store_url': f"{self.base_url}/app/{app_id}/",
                'scraped_at': datetime.now().isoformat(),
                'data_quality_score': self._calculate_steamspy_data_quality(game_data)
            }
            
            # Validate data
            validation_passed = self._validate_steam_game(game_info)
            
            # Log validation results
            self.logger.log_data_validation(
                "SteamSpy_API",
                expected_fields,
                game_info,
                validation_passed
            )
            
            return game_info
            
        except Exception as e:
            self.logger.error("Error parsing SteamSpy game data", 
                            exception=e, 
                            app_id=app_id,
                            raw_data=game_data)
            return None
    
    def _validate_steam_game(self, game_data: Dict[str, Any]) -> bool:
        """Validate Steam game data completeness and accuracy"""
        try:
            # Check required fields
            required_fields = ['steam_id', 'title', 'source']
            for field in required_fields:
                if not game_data.get(field):
                    return False
            
            # Check steam_id format
            steam_id = game_data.get('steam_id', '')
            if not steam_id.isdigit() or len(steam_id) < 3:
                return False
            
            # Check numeric fields are reasonable
            owners = game_data.get('owners_estimate', 0)
            if owners < 0 or owners > 1000000000:  # Reasonable owner count
                return False
            
            # Check review percentages
            positive_pct = game_data.get('positive_percentage', 0)
            if positive_pct < 0 or positive_pct > 100:
                return False
            
            return True
            
        except Exception:
            return False
    
    def _calculate_steamspy_data_quality(self, raw_data: Dict[str, Any]) -> float:
        """Calculate SteamSpy data quality score (0-100)"""
        try:
            score = 0
            
            # Check for essential fields
            if raw_data.get('name'): score += 20
            if raw_data.get('developer'): score += 15
            if raw_data.get('publisher'): score += 10
            if raw_data.get('genre'): score += 10
            if raw_data.get('owners'): score += 15
            if raw_data.get('players_2weeks'): score += 10
            if raw_data.get('positive') or raw_data.get('negative'): score += 15
            if raw_data.get('price') is not None: score += 5
            
            return min(score, 100)
        except:
            return 0.0