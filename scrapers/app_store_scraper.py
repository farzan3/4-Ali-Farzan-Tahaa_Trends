import requests
import time
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import logging
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AppStoreScraper:
    def __init__(self):
        self.base_url = "https://itunes.apple.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_top_charts(self, country: str = "us", category: str = "games", 
                      limit: int = 200) -> List[Dict[str, Any]]:
        """Get top charts for a specific country and category"""
        try:
            # Using iTunes Search API for app data
            url = f"{self.base_url}/search"
            params = {
                'country': country,
                'media': 'software',
                'entity': 'software',
                'limit': limit,
                'term': category
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            apps = []
            
            for app_data in data.get('results', []):
                app_info = self._parse_app_data(app_data, country)
                if app_info:
                    apps.append(app_info)
            
            logger.info(f"Scraped {len(apps)} apps from {country}/{category}")
            time.sleep(config.SCRAPER_DELAY)
            
            return apps
            
        except Exception as e:
            logger.error(f"Error scraping App Store {country}/{category}: {e}")
            return []
    
    def _parse_app_data(self, data: Dict[str, Any], country: str) -> Optional[Dict[str, Any]]:
        """Parse app data from iTunes API response"""
        try:
            return {
                'app_store_id': str(data.get('trackId', '')),
                'title': data.get('trackName', ''),
                'developer': data.get('artistName', ''),
                'category': data.get('primaryGenreName', ''),
                'country': country,
                'icon_url': data.get('artworkUrl512', data.get('artworkUrl100', '')),
                'description': data.get('description', ''),
                'release_date': self._parse_date(data.get('releaseDate')),
                'rating': float(data.get('averageUserRating', 0)),
                'review_count': int(data.get('userRatingCount', 0)),
                'price': float(data.get('price', 0)),
                'bundle_id': data.get('bundleId', ''),
                'version': data.get('version', ''),
                'size': data.get('fileSizeBytes', 0),
                'content_rating': data.get('contentAdvisoryRating', ''),
                'genres': data.get('genres', []),
                'last_updated': datetime.now()
            }
        except Exception as e:
            logger.error(f"Error parsing app data: {e}")
            return None
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            return None
    
    def get_app_details(self, app_store_id: str, country: str = "us") -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific app"""
        try:
            url = f"{self.base_url}/lookup"
            params = {
                'id': app_store_id,
                'country': country,
                'entity': 'software'
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data.get('resultCount', 0) > 0:
                return self._parse_app_data(data['results'][0], country)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting app details for {app_store_id}: {e}")
            return None
    
    def get_app_reviews(self, app_store_id: str, country: str = "us", 
                       page: int = 1) -> List[Dict[str, Any]]:
        """Get reviews for a specific app"""
        try:
            # Using RSS feed for reviews
            url = f"https://itunes.apple.com/{country}/rss/customerreviews/id={app_store_id}/sortBy=mostRecent/page={page}/xml"
            
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'xml')
            reviews = []
            
            for entry in soup.find_all('entry')[1:]:  # Skip first entry (app info)
                review = self._parse_review_data(entry, country)
                if review:
                    reviews.append(review)
            
            logger.info(f"Scraped {len(reviews)} reviews for app {app_store_id}")
            time.sleep(config.SCRAPER_DELAY)
            
            return reviews
            
        except Exception as e:
            logger.error(f"Error getting reviews for {app_store_id}: {e}")
            return []
    
    def _parse_review_data(self, entry, country: str) -> Optional[Dict[str, Any]]:
        """Parse review data from XML entry"""
        try:
            rating_elem = entry.find('im:rating')
            rating = int(rating_elem.text) if rating_elem else 0
            
            content_elem = entry.find('content')
            review_text = content_elem.text if content_elem else ""
            
            updated_elem = entry.find('updated')
            timestamp_str = updated_elem.text if updated_elem else ""
            
            return {
                'rating': rating,
                'review_text': review_text,
                'timestamp': self._parse_date(timestamp_str),
                'country': country
            }
        except Exception as e:
            logger.error(f"Error parsing review data: {e}")
            return None
    
    def scrape_all_countries_categories(self) -> List[Dict[str, Any]]:
        """Scrape all configured countries and categories"""
        all_apps = []
        
        for country in config.APP_STORE_COUNTRIES:
            for category in config.APP_STORE_CATEGORIES:
                apps = self.get_top_charts(country, category)
                all_apps.extend(apps)
                
                # Add small delay between requests
                time.sleep(config.SCRAPER_DELAY)
        
        # Remove duplicates based on app_store_id
        unique_apps = {}
        for app in all_apps:
            app_id = app.get('app_store_id')
            if app_id and app_id not in unique_apps:
                unique_apps[app_id] = app
        
        logger.info(f"Total unique apps scraped: {len(unique_apps)}")
        return list(unique_apps.values())