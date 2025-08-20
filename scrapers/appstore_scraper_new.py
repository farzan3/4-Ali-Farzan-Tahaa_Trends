"""
Enhanced App Store Scraper using app-store-scraper library
This implementation provides better reliability and more comprehensive data extraction.
"""

import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

try:
    from app_store_scraper import AppStore
    from utils.robust_logger import RobustLogger
except ImportError:
    print("Warning: app-store-scraper not installed. Install with: pip install app-store-scraper")
    AppStore = None
    
    # Fallback logger
    class RobustLogger:
        def __init__(self, name):
            self.logger = logging.getLogger(name)
        def info(self, msg): self.logger.info(msg)
        def error(self, msg): self.logger.error(msg)
        def warning(self, msg): self.logger.warning(msg)

class AppStoreScraperNew:
    """Enhanced App Store scraper using the app-store-scraper library"""
    
    def __init__(self):
        self.logger = RobustLogger("appstore_scraper_new")
        
        if not AppStore:
            self.logger.error("app-store-scraper library not available")
            return
            
        # Initialize AppStore with different countries
        self.countries = {
            'us': 'United States',
            'gb': 'United Kingdom', 
            'de': 'Germany',
            'fr': 'France',
            'jp': 'Japan',
            'kr': 'South Korea',
            'cn': 'China',
            'in': 'India',
            'ca': 'Canada',
            'au': 'Australia'
        }
        
        # App Store categories
        self.categories = {
            'games': 'Games',
            'entertainment': 'Entertainment',
            'photo_and_video': 'Photo & Video',
            'social_networking': 'Social Networking',
            'music': 'Music',
            'lifestyle': 'Lifestyle',
            'health_and_fitness': 'Health & Fitness',
            'productivity': 'Productivity',
            'utilities': 'Utilities',
            'business': 'Business',
            'education': 'Education',
            'finance': 'Finance',
            'food_and_drink': 'Food & Drink',
            'sports': 'Sports'
        }
        
        # Rate limiting
        self.request_delay = 1.0
        self.last_request_time = 0
        
        self.logger.info("AppStoreScraperNew initialized with app-store-scraper library")
    
    def _rate_limit(self):
        """Implement rate limiting to avoid being blocked"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _add_random_delay(self):
        """Add random delay to make scraping more human-like"""
        delay = random.uniform(0.5, 2.0)
        time.sleep(delay)
    
    def get_top_charts(self, country: str = 'us', category: str = 'games', 
                      chart_type: str = 'top_free', limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get top charts from App Store
        
        Args:
            country: Country code (us, gb, de, etc.)
            category: App category 
            chart_type: Type of chart (top_free, top_paid, top_grossing)
            limit: Number of apps to retrieve
        """
        if not AppStore:
            self.logger.error("app-store-scraper library not available")
            return []
        
        try:
            self._rate_limit()
            
            # Map chart types
            chart_mapping = {
                'top_free': 'top_free',
                'top_paid': 'top_paid', 
                'top_grossing': 'top_grossing'
            }
            
            chart = chart_mapping.get(chart_type, 'top_free')
            
            self.logger.info(f"Fetching {chart} apps for {country}/{category} (limit: {limit})")
            
            # Create AppStore instance for specific country
            app_store = AppStore(country=country, lang='en')
            
            # Get the chart data
            if chart == 'top_free':
                apps = app_store.top_free(category=category, limit=limit)
            elif chart == 'top_paid':
                apps = app_store.top_paid(category=category, limit=limit)
            elif chart == 'top_grossing':
                apps = app_store.top_grossing(category=category, limit=limit)
            else:
                apps = app_store.top_free(category=category, limit=limit)
            
            # Process and enhance the data
            processed_apps = []
            
            for rank, app_id in enumerate(apps, 1):
                try:
                    self._add_random_delay()
                    
                    # Get detailed app information
                    app_details = self._get_app_details(app_id, country)
                    
                    if app_details:
                        app_details.update({
                            'current_rank': rank,
                            'chart_type': chart_type,
                            'country': country,
                            'category': category,
                            'scraped_at': datetime.now().isoformat(),
                            'app_store_id': app_id
                        })
                        processed_apps.append(app_details)
                        
                        if rank % 10 == 0:
                            self.logger.info(f"Processed {rank}/{len(apps)} apps...")
                
                except Exception as e:
                    self.logger.error(f"Error processing app {app_id}: {e}")
                    continue
            
            self.logger.info(f"Successfully retrieved {len(processed_apps)} apps from {chart}")
            return processed_apps
            
        except Exception as e:
            self.logger.error(f"Error fetching top charts: {e}")
            return []
    
    def _get_app_details(self, app_id: str, country: str = 'us') -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific app"""
        try:
            app_store = AppStore(country=country, lang='en')
            
            # Get app details
            app_data = app_store.app_details(app_id)
            
            if not app_data:
                return None
            
            # Extract and structure the data
            details = {
                'app_store_id': app_id,
                'title': app_data.get('trackName', ''),
                'developer': app_data.get('artistName', ''),
                'category': app_data.get('primaryGenreName', ''),
                'price': app_data.get('price', 0),
                'currency': app_data.get('currency', 'USD'),
                'description': app_data.get('description', ''),
                'rating': app_data.get('averageUserRating', 0),
                'review_count': app_data.get('userRatingCount', 0),
                'version': app_data.get('version', ''),
                'size': app_data.get('fileSizeBytes', 0),
                'content_rating': app_data.get('contentAdvisoryRating', ''),
                'bundle_id': app_data.get('bundleId', ''),
                'release_date': app_data.get('releaseDate', ''),
                'current_version_release_date': app_data.get('currentVersionReleaseDate', ''),
                'icon_url': app_data.get('artworkUrl512', ''),
                'screenshot_urls': app_data.get('screenshotUrls', []),
                'languages': app_data.get('languageCodesISO2A', []),
                'features': app_data.get('features', []),
                'supported_devices': app_data.get('supportedDevices', []),
                'genres': app_data.get('genres', []),
                'genre_ids': app_data.get('genreIds', []),
                'is_game_center_enabled': app_data.get('isGameCenterEnabled', False),
                'seller_name': app_data.get('sellerName', ''),
                'minimum_os_version': app_data.get('minimumOsVersion', ''),
                'advisory_rating': app_data.get('trackContentRating', ''),
                'wrapper_type': app_data.get('wrapperType', ''),
                'last_updated': datetime.now().isoformat()
            }
            
            return details
            
        except Exception as e:
            self.logger.error(f"Error getting app details for {app_id}: {e}")
            return None
    
    def search_apps(self, query: str, country: str = 'us', limit: int = 50) -> List[Dict[str, Any]]:
        """Search for apps by query term"""
        if not AppStore:
            self.logger.error("app-store-scraper library not available")
            return []
        
        try:
            self._rate_limit()
            
            self.logger.info(f"Searching for apps: '{query}' in {country} (limit: {limit})")
            
            app_store = AppStore(country=country, lang='en')
            search_results = app_store.search(query, limit=limit)
            
            processed_results = []
            
            for result in search_results:
                try:
                    # Get detailed information for each search result
                    app_id = result.get('trackId')
                    if app_id:
                        app_details = self._get_app_details(str(app_id), country)
                        if app_details:
                            app_details.update({
                                'search_query': query,
                                'search_country': country,
                                'found_via': 'search'
                            })
                            processed_results.append(app_details)
                
                except Exception as e:
                    self.logger.error(f"Error processing search result: {e}")
                    continue
            
            self.logger.info(f"Found {len(processed_results)} apps for query '{query}'")
            return processed_results
            
        except Exception as e:
            self.logger.error(f"Error searching apps: {e}")
            return []
    
    def get_app_reviews(self, app_id: str, country: str = 'us', limit: int = 100) -> List[Dict[str, Any]]:
        """Get reviews for a specific app"""
        if not AppStore:
            self.logger.error("app-store-scraper library not available")
            return []
        
        try:
            self._rate_limit()
            
            self.logger.info(f"Fetching reviews for app {app_id} in {country}")
            
            app_store = AppStore(country=country, lang='en')
            reviews = app_store.reviews(app_id, limit=limit)
            
            processed_reviews = []
            
            for review in reviews:
                try:
                    review_data = {
                        'app_id': app_id,
                        'review_id': review.get('id', ''),
                        'title': review.get('title', ''),
                        'content': review.get('review', ''),
                        'rating': review.get('rating', 0),
                        'author': review.get('userName', ''),
                        'date': review.get('date', ''),
                        'version': review.get('version', ''),
                        'country': country,
                        'scraped_at': datetime.now().isoformat()
                    }
                    processed_reviews.append(review_data)
                
                except Exception as e:
                    self.logger.error(f"Error processing review: {e}")
                    continue
            
            self.logger.info(f"Retrieved {len(processed_reviews)} reviews for app {app_id}")
            return processed_reviews
            
        except Exception as e:
            self.logger.error(f"Error fetching reviews: {e}")
            return []
    
    def scrape_multiple_countries(self, category: str = 'games', chart_type: str = 'top_free', 
                                 limit: int = 50, countries: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Scrape top charts from multiple countries"""
        if countries is None:
            countries = ['us', 'gb', 'de', 'jp', 'fr']
        
        results = {}
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit tasks for each country
            future_to_country = {
                executor.submit(self.get_top_charts, country, category, chart_type, limit): country
                for country in countries
            }
            
            # Collect results
            for future in as_completed(future_to_country):
                country = future_to_country[future]
                try:
                    apps = future.result()
                    results[country] = apps
                    self.logger.info(f"Completed scraping {country}: {len(apps)} apps")
                except Exception as e:
                    self.logger.error(f"Error scraping {country}: {e}")
                    results[country] = []
        
        return results
    
    def get_trending_analysis(self, countries: Optional[List[str]] = None, 
                            categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """Perform comprehensive trending analysis across multiple markets"""
        if countries is None:
            countries = ['us', 'gb', 'de', 'jp']
        
        if categories is None:
            categories = ['games', 'entertainment', 'productivity', 'social_networking']
        
        self.logger.info("Starting comprehensive trending analysis...")
        
        all_data = {}
        trending_apps = []
        
        # Scrape data from multiple countries and categories
        for country in countries:
            all_data[country] = {}
            
            for category in categories:
                try:
                    # Get top free apps
                    free_apps = self.get_top_charts(country, category, 'top_free', 20)
                    # Get top grossing apps  
                    grossing_apps = self.get_top_charts(country, category, 'top_grossing', 20)
                    
                    all_data[country][category] = {
                        'top_free': free_apps,
                        'top_grossing': grossing_apps
                    }
                    
                    # Identify trending apps (apps appearing in both charts)
                    free_ids = {app['app_store_id'] for app in free_apps}
                    grossing_ids = {app['app_store_id'] for app in grossing_apps}
                    trending_ids = free_ids.intersection(grossing_ids)
                    
                    for app in free_apps:
                        if app['app_store_id'] in trending_ids:
                            app['trending_score'] = self._calculate_trending_score(app)
                            app['is_trending'] = True
                            trending_apps.append(app)
                
                except Exception as e:
                    self.logger.error(f"Error analyzing {country}/{category}: {e}")
                    continue
        
        # Sort trending apps by score
        trending_apps.sort(key=lambda x: x.get('trending_score', 0), reverse=True)
        
        analysis_result = {
            'analysis_timestamp': datetime.now().isoformat(),
            'countries_analyzed': countries,
            'categories_analyzed': categories,
            'trending_apps': trending_apps[:50],  # Top 50 trending
            'total_apps_analyzed': sum(
                len(country_data.get(cat, {}).get('top_free', [])) + 
                len(country_data.get(cat, {}).get('top_grossing', []))
                for country_data in all_data.values()
                for cat in categories
            ),
            'regions_covered': len(countries),
            'raw_data': all_data
        }
        
        self.logger.info(f"Trending analysis complete: {len(trending_apps)} trending apps found")
        return analysis_result
    
    def _calculate_trending_score(self, app: Dict[str, Any]) -> float:
        """Calculate a trending score for an app based on various factors"""
        score = 0.0
        
        # Rating factor (0-25 points)
        rating = app.get('rating', 0)
        score += (rating / 5.0) * 25
        
        # Review count factor (0-25 points)
        review_count = app.get('review_count', 0)
        review_score = min(review_count / 10000, 1.0) * 25
        score += review_score
        
        # Rank factor (0-30 points) - lower rank is better
        rank = app.get('current_rank', 999)
        rank_score = max(0, (100 - rank) / 100 * 30)
        score += rank_score
        
        # Recency factor (0-20 points)
        try:
            release_date = app.get('current_version_release_date', app.get('release_date', ''))
            if release_date:
                release_dt = datetime.fromisoformat(release_date.replace('Z', '+00:00'))
                days_old = (datetime.now() - release_dt).days
                recency_score = max(0, (365 - days_old) / 365 * 20)
                score += recency_score
        except:
            pass
        
        return round(score, 2)
    
    def save_data_to_file(self, data: List[Dict[str, Any]], filename: str):
        """Save scraped data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Data saved to {filename} ({len(data)} items)")
            
        except Exception as e:
            self.logger.error(f"Error saving data to {filename}: {e}")

# Example usage
if __name__ == "__main__":
    scraper = AppStoreScraperNew()
    
    # Test basic functionality
    print("Testing App Store Scraper with app-store-scraper library...")
    
    # Get top free games in US
    top_games = scraper.get_top_charts('us', 'games', 'top_free', 10)
    print(f"Found {len(top_games)} top free games")
    
    # Search for apps
    search_results = scraper.search_apps('fitness', 'us', 5)
    print(f"Found {len(search_results)} fitness apps")
    
    # Get trending analysis
    trending = scraper.get_trending_analysis(['us'], ['games'])
    print(f"Trending analysis found {len(trending['trending_apps'])} trending apps")