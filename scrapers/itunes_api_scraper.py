"""
iTunes Search API Scraper - More reliable than library-based scrapers
Uses official iTunes Search API: https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/
"""

import requests
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from utils.robust_logger import RobustLogger
except ImportError:
    # Fallback logger
    class RobustLogger:
        def __init__(self, name):
            self.logger = logging.getLogger(name)
        def info(self, msg): self.logger.info(msg)
        def error(self, msg): self.logger.error(msg)
        def warning(self, msg): self.logger.warning(msg)

class iTunesAPIScaper:
    """App Store scraper using official iTunes Search API"""
    
    def __init__(self):
        self.logger = RobustLogger("itunes_api_scraper")
        
        # iTunes Search API endpoints
        self.search_url = "https://itunes.apple.com/search"
        self.lookup_url = "https://itunes.apple.com/lookup"
        self.rss_url = "https://rss.applemarketingtools.com/api/v2/{country}/apps/{feed_type}/{category}.{format}"
        
        # Country codes
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
        
        # Categories mapping
        self.categories = {
            'games': 6014,
            'business': 6000,
            'developer-tools': 6026,
            'education': 6017,
            'entertainment': 6016,
            'finance': 6015,
            'food-drink': 6023,
            'graphics-design': 6027,
            'health-fitness': 6013,
            'lifestyle': 6012,
            'medical': 6020,
            'music': 6011,
            'news': 6009,
            'photography': 6008,
            'productivity': 6007,
            'reference': 6006,
            'social-networking': 6005,
            'sports': 6004,
            'travel': 6003,
            'utilities': 6002,
            'weather': 6001
        }
        
        # Feed types for RSS
        self.feed_types = [
            'top-free',
            'top-paid',
            'top-grossing',
            'new-apps-we-love',
            'new-games-we-love'
        ]
        
        # Rate limiting
        self.request_delay = 0.5
        self.last_request_time = 0
        
        # Session for connection reuse
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        self.logger.info("iTunesAPIScaper initialized")
    
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        """Make HTTP request with error handling"""
        try:
            self._rate_limit()
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed for {url}: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error for {url}: {e}")
            return None
    
    def search_apps(self, query: str, country: str = 'us', limit: int = 50, 
                   entity: str = 'software') -> List[Dict[str, Any]]:
        """
        Search for apps using iTunes Search API
        
        Args:
            query: Search term
            country: Country code
            limit: Number of results (max 200)
            entity: Type of search (software, iPadSoftware, macSoftware)
        """
        try:
            params = {
                'term': query,
                'country': country.upper(),
                'entity': entity,
                'limit': min(limit, 200),  # API limit
                'media': 'software'
            }
            
            self.logger.info(f"Searching for '{query}' in {country} (limit: {limit})")
            
            data = self._make_request(self.search_url, params)
            
            if not data or 'results' not in data:
                self.logger.warning(f"No results found for query: {query}")
                return []
            
            results = []
            for app in data['results']:
                processed_app = self._process_app_data(app)
                if processed_app:
                    processed_app.update({
                        'search_query': query,
                        'search_country': country,
                        'found_via': 'search'
                    })
                    results.append(processed_app)
            
            self.logger.info(f"Found {len(results)} apps for query '{query}'")
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching apps: {e}")
            return []
    
    def get_app_details(self, app_id: str, country: str = 'us') -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific app"""
        try:
            params = {
                'id': app_id,
                'country': country.upper(),
                'entity': 'software'
            }
            
            data = self._make_request(self.lookup_url, params)
            
            if not data or 'results' not in data or not data['results']:
                self.logger.warning(f"No details found for app ID: {app_id}")
                return None
            
            app_data = data['results'][0]
            return self._process_app_data(app_data)
            
        except Exception as e:
            self.logger.error(f"Error getting app details for {app_id}: {e}")
            return None
    
    def get_top_charts_rss(self, country: str = 'us', feed_type: str = 'top-free', 
                          category: str = 'games', limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get top charts using Apple's RSS feeds
        More reliable for getting current rankings
        """
        try:
            # Build RSS URL
            rss_url = self.rss_url.format(
                country=country,
                feed_type=feed_type,
                category=category,
                format='json'
            )
            
            self.logger.info(f"Fetching {feed_type} {category} apps from {country}")
            
            data = self._make_request(rss_url)
            
            if not data or 'feed' not in data or 'results' not in data['feed']:
                self.logger.warning(f"No RSS data found for {feed_type}/{category}/{country}")
                return []
            
            results = []
            apps = data['feed']['results'][:limit]
            
            for rank, app in enumerate(apps, 1):
                try:
                    # Get detailed app info using the app ID
                    app_id = app.get('id')
                    if app_id:
                        detailed_app = self.get_app_details(app_id, country)
                        if detailed_app:
                            detailed_app.update({
                                'current_rank': rank,
                                'chart_type': feed_type,
                                'rss_category': category,
                                'country': country
                            })
                            results.append(detailed_app)
                    
                    # Add delay every 10 apps to avoid rate limiting
                    if rank % 10 == 0:
                        time.sleep(1)
                        self.logger.info(f"Processed {rank}/{len(apps)} apps...")
                
                except Exception as e:
                    self.logger.error(f"Error processing RSS app {app.get('id', 'unknown')}: {e}")
                    continue
            
            self.logger.info(f"Successfully retrieved {len(results)} apps from RSS feed")
            return results
            
        except Exception as e:
            self.logger.error(f"Error fetching RSS data: {e}")
            return []
    
    def get_top_charts_search(self, category: str = 'games', country: str = 'us', 
                             limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get top apps by searching for popular terms in a category
        Fallback method when RSS doesn't work
        """
        try:
            # Popular search terms by category
            search_terms = {
                'games': ['game', 'puzzle', 'arcade', 'action', 'strategy'],
                'social-networking': ['social', 'chat', 'messenger', 'network'],
                'entertainment': ['video', 'movie', 'tv', 'entertainment'],
                'productivity': ['todo', 'notes', 'office', 'work', 'productivity'],
                'health-fitness': ['fitness', 'health', 'workout', 'diet'],
                'music': ['music', 'player', 'radio', 'podcast'],
                'photo-video': ['photo', 'camera', 'video', 'editor'],
                'utilities': ['utility', 'tool', 'calculator', 'weather']
            }
            
            terms = search_terms.get(category, ['app'])
            all_apps = []
            seen_ids = set()
            
            for term in terms:
                apps = self.search_apps(term, country, limit // len(terms))
                
                for app in apps:
                    app_id = app.get('app_store_id')
                    if app_id and app_id not in seen_ids:
                        seen_ids.add(app_id)
                        app['search_category'] = category
                        all_apps.append(app)
                
                time.sleep(0.5)  # Rate limiting
            
            # Sort by some popularity metric (review count * rating)
            for app in all_apps:
                rating = app.get('rating', 0)
                review_count = app.get('review_count', 0)
                app['popularity_score'] = rating * (review_count ** 0.5)
            
            # Sort and limit results
            all_apps.sort(key=lambda x: x.get('popularity_score', 0), reverse=True)
            top_apps = all_apps[:limit]
            
            # Add rankings
            for rank, app in enumerate(top_apps, 1):
                app['estimated_rank'] = rank
                app['chart_type'] = 'search-based'
            
            self.logger.info(f"Retrieved {len(top_apps)} apps via search method")
            return top_apps
            
        except Exception as e:
            self.logger.error(f"Error in search-based chart retrieval: {e}")
            return []
    
    def _process_app_data(self, app_data: Dict) -> Optional[Dict[str, Any]]:
        """Process and standardize app data from iTunes API"""
        try:
            # Extract and clean data
            processed = {
                'app_store_id': str(app_data.get('trackId', '')),
                'title': app_data.get('trackName', ''),
                'developer': app_data.get('artistName', ''),
                'category': app_data.get('primaryGenreName', ''),
                'price': float(app_data.get('price', 0)),
                'currency': app_data.get('currency', 'USD'),
                'description': app_data.get('description', ''),
                'rating': float(app_data.get('averageUserRating', 0)),
                'review_count': int(app_data.get('userRatingCount', 0)),
                'version': app_data.get('version', ''),
                'size': int(app_data.get('fileSizeBytes', 0)),
                'content_rating': app_data.get('contentAdvisoryRating', ''),
                'bundle_id': app_data.get('bundleId', ''),
                'release_date': app_data.get('releaseDate', ''),
                'current_version_release_date': app_data.get('currentVersionReleaseDate', ''),
                'icon_url': app_data.get('artworkUrl512', app_data.get('artworkUrl100', '')),
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
                'scraped_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
            
            return processed
            
        except Exception as e:
            self.logger.error(f"Error processing app data: {e}")
            return None
    
    def scrape_multiple_countries(self, category: str = 'games', 
                                 chart_type: str = 'top-free', limit: int = 50,
                                 countries: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Scrape top charts from multiple countries"""
        if countries is None:
            countries = ['us', 'gb', 'de', 'jp', 'fr']
        
        results = {}
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit tasks for each country
            future_to_country = {
                executor.submit(self.get_top_charts_rss, country, chart_type, category, limit): country
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
        """Perform trending analysis across multiple markets"""
        if countries is None:
            countries = ['us', 'gb', 'de']
        
        if categories is None:
            categories = ['games', 'entertainment', 'productivity']
        
        self.logger.info("Starting iTunes API trending analysis...")
        
        all_data = {}
        trending_apps = []
        
        for country in countries:
            all_data[country] = {}
            
            for category in categories:
                try:
                    # Get both free and grossing charts
                    free_apps = self.get_top_charts_rss(country, 'top-free', category, 20)
                    grossing_apps = self.get_top_charts_rss(country, 'top-grossing', category, 20)
                    
                    all_data[country][category] = {
                        'top_free': free_apps,
                        'top_grossing': grossing_apps
                    }
                    
                    # Find apps trending in both charts
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
        
        # Sort by trending score
        trending_apps.sort(key=lambda x: x.get('trending_score', 0), reverse=True)
        
        analysis_result = {
            'analysis_timestamp': datetime.now().isoformat(),
            'countries_analyzed': countries,
            'categories_analyzed': categories,
            'trending_apps': trending_apps[:50],
            'total_apps_analyzed': sum(
                len(country_data.get(cat, {}).get('top_free', [])) +
                len(country_data.get(cat, {}).get('top_grossing', []))
                for country_data in all_data.values()
                for cat in categories
            ),
            'regions_covered': len(countries),
            'method': 'iTunes_Search_API'
        }
        
        self.logger.info(f"iTunes API analysis complete: {len(trending_apps)} trending apps")
        return analysis_result
    
    def _calculate_trending_score(self, app: Dict[str, Any]) -> float:
        """Calculate trending score for an app"""
        score = 0.0
        
        # Rating factor (0-25 points)
        rating = app.get('rating', 0)
        score += (rating / 5.0) * 25
        
        # Review count factor (0-25 points)
        review_count = app.get('review_count', 0)
        review_score = min(review_count / 10000, 1.0) * 25
        score += review_score
        
        # Rank factor (0-30 points)
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

# Example usage
if __name__ == "__main__":
    scraper = iTunesAPIScaper()
    
    print("Testing iTunes API scraper...")
    
    # Test search
    results = scraper.search_apps('puzzle', 'us', 5)
    print(f"Search results: {len(results)} apps")
    
    # Test RSS feed
    top_games = scraper.get_top_charts_rss('us', 'top-free', 'games', 5)
    print(f"Top games: {len(top_games)} apps")
    
    if top_games:
        print(f"Top game: {top_games[0].get('title', 'Unknown')}")