import requests
import time
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
from dataclasses import dataclass
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
logger = get_logger("app_store_scraper")

@dataclass
class AppStoreRegion:
    code: str
    name: str
    currency: str
    active: bool = True

class EnhancedAppStoreScraper:
    def __init__(self):
        # Initialize robust logging
        self.logger = get_logger("app_store_scraper")
        self.logger.info("EnhancedAppStoreScraper initialized")
        self.base_url = "https://itunes.apple.com"
        self.rss_base = "https://rss.applemarketingtools.com/api/v2"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
        })
        
        # All App Store regions with proper codes
        self.regions = [
            AppStoreRegion("us", "United States", "USD"),
            AppStoreRegion("gb", "United Kingdom", "GBP"),
            AppStoreRegion("ca", "Canada", "CAD"),
            AppStoreRegion("au", "Australia", "AUD"),
            AppStoreRegion("de", "Germany", "EUR"),
            AppStoreRegion("fr", "France", "EUR"),
            AppStoreRegion("it", "Italy", "EUR"),
            AppStoreRegion("es", "Spain", "EUR"),
            AppStoreRegion("nl", "Netherlands", "EUR"),
            AppStoreRegion("jp", "Japan", "JPY"),
            AppStoreRegion("kr", "South Korea", "KRW"),
            AppStoreRegion("cn", "China", "CNY"),
            AppStoreRegion("in", "India", "INR"),
            AppStoreRegion("br", "Brazil", "BRL"),
            AppStoreRegion("mx", "Mexico", "MXN"),
            AppStoreRegion("ru", "Russia", "RUB"),
            AppStoreRegion("tr", "Turkey", "TRY"),
            AppStoreRegion("ae", "UAE", "AED"),
            AppStoreRegion("sg", "Singapore", "SGD"),
            AppStoreRegion("hk", "Hong Kong", "HKD"),
            AppStoreRegion("tw", "Taiwan", "TWD"),
            AppStoreRegion("th", "Thailand", "THB"),
            AppStoreRegion("id", "Indonesia", "IDR"),
            AppStoreRegion("ph", "Philippines", "PHP"),
            AppStoreRegion("my", "Malaysia", "MYR"),
            AppStoreRegion("vn", "Vietnam", "VND"),
            AppStoreRegion("za", "South Africa", "ZAR"),
            AppStoreRegion("eg", "Egypt", "EGP"),
            AppStoreRegion("il", "Israel", "ILS"),
            AppStoreRegion("sa", "Saudi Arabia", "SAR")
        ]
        
        # App Store categories with IDs
        self.categories = {
            "all": {"name": "All Categories", "id": ""},
            "games": {"name": "Games", "id": "6014"},
            "business": {"name": "Business", "id": "6000"},
            "education": {"name": "Education", "id": "6017"},
            "entertainment": {"name": "Entertainment", "id": "6016"},
            "finance": {"name": "Finance", "id": "6015"},
            "food-drink": {"name": "Food & Drink", "id": "6023"},
            "health-fitness": {"name": "Health & Fitness", "id": "6013"},
            "lifestyle": {"name": "Lifestyle", "id": "6012"},
            "medical": {"name": "Medical", "id": "6020"},
            "music": {"name": "Music", "id": "6011"},
            "news": {"name": "News", "id": "6021"},
            "photo-video": {"name": "Photo & Video", "id": "6008"},
            "productivity": {"name": "Productivity", "id": "6007"},
            "reference": {"name": "Reference", "id": "6006"},
            "shopping": {"name": "Shopping", "id": "6024"},
            "social-networking": {"name": "Social Networking", "id": "6005"},
            "sports": {"name": "Sports", "id": "6004"},
            "travel": {"name": "Travel", "id": "6003"},
            "utilities": {"name": "Utilities", "id": "6002"},
            "weather": {"name": "Weather", "id": "6001"}
        }
        
        # Feed types for different charts
        self.feed_types = {
            "top-free": "top-free-applications",
            "top-paid": "top-paid-applications", 
            "top-grossing": "top-grossing-applications",
            "new-apps": "new-applications",
            "new-free": "new-free-applications",
            "new-paid": "new-paid-applications"
        }
        
        # Proxy rotation
        self.proxies = config.PROXY_LIST if config.USE_PROXY else []
        self.proxy_index = 0
        
        # Rate limiting
        self.last_request_time = 0
        self.request_count = 0
        self.rate_limit_reset_time = time.time() + 3600  # Reset every hour
        
    def get_proxy(self) -> Optional[Dict[str, str]]:
        """Get next proxy in rotation"""
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.proxy_index]
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        
        return {
            'http': f'http://{proxy}',
            'https': f'https://{proxy}'
        }
    
    def rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        
        # Reset counter every hour
        if current_time > self.rate_limit_reset_time:
            self.request_count = 0
            self.rate_limit_reset_time = current_time + 3600
        
        # Enforce rate limiting (max 100 requests per hour per region)
        if self.request_count >= 100:
            sleep_time = self.rate_limit_reset_time - current_time
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                self.request_count = 0
                self.rate_limit_reset_time = time.time() + 3600
        
        # Add delay between requests
        time_since_last = current_time - self.last_request_time
        if time_since_last < config.SCRAPER_DELAY:
            time.sleep(config.SCRAPER_DELAY - time_since_last)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def make_request(self, url: str, params: Dict[str, Any] = None, retries: int = 3) -> Optional[requests.Response]:
        """Make request with retry logic, proxy rotation, and comprehensive logging"""
        # Log the attempt
        self.logger.log_scraping_attempt("iTunes_API", url, params)
        start_time = time.time()
        
        for attempt in range(retries):
            try:
                self.rate_limit()
                
                proxy = self.get_proxy()
                
                # Log attempt details
                self.logger.debug("Making HTTP request",
                                url=url,
                                params=params,
                                attempt=attempt + 1,
                                proxy_used=bool(proxy))
                
                response = self.session.get(
                    url, 
                    params=params, 
                    proxies=proxy,
                    timeout=30,
                    verify=True
                )
                
                response.raise_for_status()
                
                # Log successful request
                response_time = time.time() - start_time
                self.logger.log_scraping_success(
                    "iTunes_API",
                    url,
                    1,  # One successful request
                    response_time,
                    {"status_code": response.status_code, "content_length": len(response.content)}
                )
                
                return response
                
            except requests.exceptions.RequestException as e:
                response_time = time.time() - start_time
                will_retry = attempt < retries - 1
                
                self.logger.log_scraping_failure(
                    "iTunes_API",
                    url,
                    e,
                    retry_count=attempt + 1,
                    will_retry=will_retry
                )
                
                if not will_retry:
                    return None
                
                # Exponential backoff
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                self.logger.debug(f"Retrying in {wait_time:.2f} seconds",
                                retry_attempt=attempt + 1,
                                wait_time=wait_time)
                time.sleep(wait_time)
        
        return None
    
    def scrape_top_charts_all_regions(self, feed_type: str = "top-free", 
                                    category: str = "all", limit: int = 200) -> List[Dict[str, Any]]:
        """Scrape top charts from all regions"""
        logger.info(f"Starting comprehensive scrape: {feed_type} - {category} - {limit} apps per region")
        
        all_apps = []
        successful_regions = 0
        failed_regions = 0
        
        feed_name = self.feed_types.get(feed_type, "top-free-applications")
        category_id = self.categories.get(category, {}).get("id", "")
        
        for region in self.regions:
            if not region.active:
                continue
                
            try:
                logger.info(f"Scraping {region.name} ({region.code})")
                
                apps = self.scrape_region_chart(
                    region.code, 
                    feed_name, 
                    category_id, 
                    limit
                )
                
                if apps:
                    # Add region metadata to each app
                    for app in apps:
                        app['region'] = region.code
                        app['region_name'] = region.name
                        app['currency'] = region.currency
                        app['scrape_timestamp'] = datetime.now().isoformat()
                        app['chart_type'] = feed_type
                        app['category_filter'] = category
                    
                    all_apps.extend(apps)
                    successful_regions += 1
                    self.logger.info(f"SUCCESS {region.name}: {len(apps)} apps scraped")
                else:
                    failed_regions += 1
                    self.logger.warning(f"FAILED {region.name}: No apps retrieved")
                
                # Random delay between regions to be respectful
                time.sleep(random.uniform(2, 5))
                
            except Exception as e:
                failed_regions += 1
                self.logger.error(f"ERROR {region.name}: {e}", exception=e)
        
        # Remove duplicates based on app ID but keep region-specific data
        unique_apps = self.deduplicate_apps(all_apps)
        
        logger.info(f"""
        Scraping Summary:
        ================
        Successful Regions: {successful_regions}
        Failed Regions: {failed_regions}
        Total Apps Scraped: {len(all_apps)}
        Unique Apps: {len(unique_apps)}
        """)
        
        return unique_apps
    
    def scrape_region_chart(self, region_code: str, feed_type: str, 
                          category_id: str, limit: int) -> List[Dict[str, Any]]:
        """Scrape top chart for specific region using iTunes Search API"""
        try:
            # Use iTunes Search API as fallback since RSS feeds are unreliable
            url = f"{self.base_url}/search"
            
            # Map feed types to search terms
            search_terms = {
                'top-free-applications': 'free',
                'top-paid-applications': 'paid',
                'top-grossing-applications': 'grossing'
            }
            
            search_term = search_terms.get(feed_type, 'free')
            
            params = {
                'term': search_term,
                'country': region_code,
                'media': 'software',
                'entity': 'software',
                'limit': min(limit, 200)  # iTunes API limit
            }
            
            if category_id and category_id != '':
                params['genreId'] = category_id
            
            response = self.make_request(url, params)
            if not response:
                return []
            
            data = response.json()
            apps = []
            
            # Parse iTunes Search API format
            if 'results' in data:
                results = data['results']
                
                for i, result in enumerate(results[:limit]):
                    app_info = self.parse_itunes_result(result, i + 1)
                    if app_info:
                        apps.append(app_info)
            
            return apps
            
        except Exception as e:
            logger.error(f"Error scraping region {region_code}: {e}")
            return []
    
    def parse_itunes_result(self, result: Dict[str, Any], rank: int) -> Optional[Dict[str, Any]]:
        """Parse iTunes Search API result with comprehensive validation"""
        try:
            # Expected fields for validation
            expected_fields = [
                'app_store_id', 'title', 'developer', 'bundle_id', 'current_rank',
                'category', 'price', 'rating', 'rating_count', 'version', 'link'
            ]
            
            # Extract and validate required data
            track_id = result.get('trackId')
            if not track_id:
                self.logger.warning("Missing trackId in iTunes result", raw_data=result)
                return None
            
            app_info = {
                'app_store_id': str(track_id),
                'title': result.get('trackName', 'Unknown').strip(),
                'developer': result.get('artistName', 'Unknown').strip(),
                'bundle_id': result.get('bundleId', '').strip(),
                'current_rank': rank,
                'category': result.get('primaryGenreName', 'Unknown').strip(),
                'release_date': self.parse_release_date(result.get('releaseDate')),
                'icon_url': result.get('artworkUrl100', '').strip(),
                'price': self._safe_float(result.get('price', 0)),
                'content_rating': result.get('contentAdvisoryRating', 'Unknown').strip(),
                'summary': result.get('description', '').strip()[:1000],  # Limit summary length
                'link': result.get('trackViewUrl', '').strip(),
                'version': result.get('version', '').strip(),
                'rating': self._safe_float(result.get('averageUserRating', 0)),
                'rating_count': self._safe_int(result.get('userRatingCount', 0)),
                'file_size': self._safe_int(result.get('fileSizeBytes', 0)),
                'genres': result.get('genres', []) if isinstance(result.get('genres'), list) else [],
                'currency': result.get('currency', 'USD').strip(),
                'country': result.get('country', 'US').strip(),
                'last_updated': datetime.now().isoformat(),
                'data_quality_score': self._calculate_data_quality(result),
                'scraped_at': datetime.now().isoformat()
            }
            
            # Validate required fields
            validation_passed = self._validate_app_data(app_info, expected_fields)
            
            # Log validation results
            self.logger.log_data_validation(
                "iTunes_API",
                expected_fields,
                app_info,
                validation_passed
            )
            
            if not validation_passed:
                self.logger.warning("App data failed validation", 
                                  app_id=app_info['app_store_id'],
                                  title=app_info['title'])
            
            return app_info
            
        except Exception as e:
            self.logger.error("Error parsing iTunes result", 
                            exception=e, 
                            raw_data=result)
            return None
    
    def parse_rss_entry(self, entry: Dict[str, Any], rank: int) -> Optional[Dict[str, Any]]:
        """Parse RSS feed entry to extract app information"""
        try:
            # Extract app ID from URL
            app_id = None
            if 'id' in entry and 'attributes' in entry['id']:
                bundle_id = entry['id']['attributes']['im:bundleId']
                # Get numeric ID from link
                link = entry.get('link', {}).get('attributes', {}).get('href', '')
                if '/id' in link:
                    app_id = link.split('/id')[1].split('?')[0]
            
            # Extract basic info
            app_info = {
                'app_store_id': app_id or f"unknown_{rank}",
                'title': entry.get('im:name', {}).get('label', 'Unknown'),
                'developer': entry.get('im:artist', {}).get('label', 'Unknown'),
                'bundle_id': entry.get('id', {}).get('attributes', {}).get('im:bundleId', ''),
                'current_rank': rank,
                'category': entry.get('category', {}).get('attributes', {}).get('label', 'Unknown'),
                'release_date': self.parse_release_date(entry.get('im:releaseDate', {}).get('label')),
                'icon_url': self.get_best_icon_url(entry.get('im:image', [])),
                'price': self.parse_price(entry.get('im:price', {}).get('attributes', {})),
                'content_rating': entry.get('im:contentType', {}).get('attributes', {}).get('label', 'Unknown'),
                'summary': entry.get('summary', {}).get('label', ''),
                'link': entry.get('link', {}).get('attributes', {}).get('href', ''),
                'rights': entry.get('rights', {}).get('label', ''),
                'last_updated': datetime.now().isoformat()
            }
            
            return app_info
            
        except Exception as e:
            logger.error(f"Error parsing RSS entry: {e}")
            return None
    
    def get_best_icon_url(self, images: List[Dict[str, Any]]) -> str:
        """Get the best quality icon URL"""
        if not images:
            return ""
        
        # Sort by size preference (100x100 is typically best for display)
        size_preference = ["100x100", "60x60", "53x53"]
        
        for size in size_preference:
            for img in images:
                if img.get('attributes', {}).get('height') == size:
                    return img.get('label', '')
        
        # Return first available if no preferred size found
        return images[0].get('label', '') if images else ""
    
    def parse_price(self, price_attrs: Dict[str, Any]) -> float:
        """Parse price from price attributes"""
        try:
            amount = price_attrs.get('amount', '0')
            if amount == '0.00000':
                return 0.0
            return float(amount)
        except (ValueError, TypeError):
            return 0.0
    
    def parse_release_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse release date string"""
        if not date_str:
            return None
        
        try:
            # Handle different date formats
            formats = [
                "%Y-%m-%dT%H:%M:%S-07:00",
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%d"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
                    
        except Exception:
            pass
        
        return None
    
    def deduplicate_apps(self, apps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicates while preserving regional ranking data"""
        seen_apps = {}
        
        for app in apps:
            app_id = app.get('app_store_id')
            if not app_id or app_id.startswith('unknown'):
                continue
            
            if app_id not in seen_apps:
                seen_apps[app_id] = app.copy()
                seen_apps[app_id]['regional_rankings'] = []
            
            # Add regional ranking info
            seen_apps[app_id]['regional_rankings'].append({
                'region': app.get('region'),
                'region_name': app.get('region_name'),
                'rank': app.get('current_rank'),
                'chart_type': app.get('chart_type'),
                'currency': app.get('currency')
            })
            
            # Update global rank (average of all regional ranks)
            ranks = [r['rank'] for r in seen_apps[app_id]['regional_rankings'] if r['rank']]
            if ranks:
                seen_apps[app_id]['global_average_rank'] = sum(ranks) / len(ranks)
                seen_apps[app_id]['regions_count'] = len(ranks)
                seen_apps[app_id]['best_rank'] = min(ranks)
                seen_apps[app_id]['worst_rank'] = max(ranks)
        
        return list(seen_apps.values())
    
    def get_app_details_enhanced(self, app_id: str, region: str = "us") -> Optional[Dict[str, Any]]:
        """Get enhanced app details including reviews and ratings"""
        try:
            # Get basic app info
            url = f"{self.base_url}/lookup"
            params = {
                'id': app_id,
                'country': region,
                'entity': 'software'
            }
            
            response = self.make_request(url, params)
            if not response:
                return None
            
            data = response.json()
            if data.get('resultCount', 0) == 0:
                return None
            
            app_data = data['results'][0]
            
            # Get reviews
            reviews = self.get_app_reviews_enhanced(app_id, region)
            
            # Enhanced app details
            enhanced_data = {
                'app_store_id': str(app_data.get('trackId', '')),
                'title': app_data.get('trackName', ''),
                'developer': app_data.get('artistName', ''),
                'developer_id': app_data.get('artistId', ''),
                'bundle_id': app_data.get('bundleId', ''),
                'version': app_data.get('version', ''),
                'description': app_data.get('description', ''),
                'release_notes': app_data.get('releaseNotes', ''),
                'category': app_data.get('primaryGenreName', ''),
                'genres': app_data.get('genres', []),
                'rating': float(app_data.get('averageUserRating', 0)),
                'rating_current_version': float(app_data.get('averageUserRatingForCurrentVersion', 0)),
                'review_count': int(app_data.get('userRatingCount', 0)),
                'review_count_current_version': int(app_data.get('userRatingCountForCurrentVersion', 0)),
                'price': float(app_data.get('price', 0)),
                'formatted_price': app_data.get('formattedPrice', 'Free'),
                'currency': app_data.get('currency', 'USD'),
                'file_size_bytes': app_data.get('fileSizeBytes', 0),
                'content_rating': app_data.get('contentAdvisoryRating', ''),
                'minimum_os_version': app_data.get('minimumOsVersion', ''),
                'supported_devices': app_data.get('supportedDevices', []),
                'features': app_data.get('features', []),
                'advisories': app_data.get('advisories', []),
                'icon_urls': {
                    '60': app_data.get('artworkUrl60', ''),
                    '100': app_data.get('artworkUrl100', ''),
                    '512': app_data.get('artworkUrl512', '')
                },
                'screenshot_urls': app_data.get('screenshotUrls', []),
                'ipad_screenshot_urls': app_data.get('ipadScreenshotUrls', []),
                'release_date': self.parse_date(app_data.get('releaseDate')),
                'current_version_release_date': self.parse_date(app_data.get('currentVersionReleaseDate')),
                'is_game_center_enabled': app_data.get('isGameCenterEnabled', False),
                'track_view_url': app_data.get('trackViewUrl', ''),
                'seller_name': app_data.get('sellerName', ''),
                'language_codes': app_data.get('languageCodesISO2A', []),
                'recent_reviews': reviews,
                'enhanced_metadata': {
                    'scraped_at': datetime.now().isoformat(),
                    'region': region,
                    'has_in_app_purchases': bool(app_data.get('features', [])),
                    'wrapper_type': app_data.get('wrapperType', ''),
                    'kind': app_data.get('kind', '')
                }
            }
            
            return enhanced_data
            
        except Exception as e:
            logger.error(f"Error getting enhanced app details for {app_id}: {e}")
            return None
    
    def get_app_reviews_enhanced(self, app_id: str, region: str = "us", 
                               page: int = 1, sort: str = "mostRecent") -> List[Dict[str, Any]]:
        """Get enhanced app reviews with sentiment indicators"""
        try:
            # Use Customer Reviews RSS feed
            url = f"https://itunes.apple.com/{region}/rss/customerreviews/page={page}/id={app_id}/sortby={sort}/xml"
            
            response = self.make_request(url)
            if not response:
                return []
            
            from xml.etree import ElementTree as ET
            root = ET.fromstring(response.content)
            
            reviews = []
            entries = root.findall('.//{http://www.w3.org/2005/Atom}entry')[1:]  # Skip first entry (app info)
            
            for entry in entries:
                review = self.parse_review_xml(entry)
                if review:
                    reviews.append(review)
            
            return reviews
            
        except Exception as e:
            logger.error(f"Error getting reviews for app {app_id}: {e}")
            return []
    
    def parse_review_xml(self, entry) -> Optional[Dict[str, Any]]:
        """Parse review from XML entry"""
        try:
            ns = {'atom': 'http://www.w3.org/2005/Atom', 'im': 'http://itunes.apple.com/rss'}
            
            rating_elem = entry.find('.//{http://itunes.apple.com/rss}rating')
            rating = int(rating_elem.text) if rating_elem is not None else 0
            
            title_elem = entry.find('.//{http://www.w3.org/2005/Atom}title')
            title = title_elem.text if title_elem is not None else ""
            
            content_elem = entry.find('.//{http://www.w3.org/2005/Atom}content')
            content = content_elem.text if content_elem is not None else ""
            
            author_elem = entry.find('.//{http://www.w3.org/2005/Atom}author/{http://www.w3.org/2005/Atom}name')
            author = author_elem.text if author_elem is not None else "Anonymous"
            
            updated_elem = entry.find('.//{http://www.w3.org/2005/Atom}updated')
            updated = updated_elem.text if updated_elem is not None else ""
            
            version_elem = entry.find('.//{http://itunes.apple.com/rss}version')
            version = version_elem.text if version_elem is not None else ""
            
            review = {
                'rating': rating,
                'title': title,
                'content': content,
                'author': author,
                'version': version,
                'timestamp': self.parse_date(updated),
                'sentiment_indicator': 'positive' if rating >= 4 else 'negative' if rating <= 2 else 'neutral',
                'helpful_score': self.calculate_helpfulness_score(content, rating)
            }
            
            return review
            
        except Exception as e:
            logger.error(f"Error parsing review XML: {e}")
            return None
    
    def calculate_helpfulness_score(self, content: str, rating: int) -> float:
        """Calculate helpfulness score based on content quality"""
        if not content:
            return 0.0
        
        score = 0.0
        
        # Length factor (longer reviews tend to be more helpful)
        length_score = min(len(content.split()) / 50, 1.0)  # Cap at 50 words
        score += length_score * 0.3
        
        # Rating consistency (extreme ratings with detailed content)
        if (rating <= 2 or rating >= 4) and len(content) > 20:
            score += 0.3
        
        # Keyword indicators of helpfulness
        helpful_keywords = ['bug', 'crash', 'update', 'feature', 'improvement', 'issue', 'problem', 'excellent', 'terrible']
        keyword_matches = sum(1 for keyword in helpful_keywords if keyword.lower() in content.lower())
        score += min(keyword_matches / 10, 0.4)  # Cap at 0.4
        
        return min(score, 1.0)
    
    def parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Enhanced date parsing"""
        if not date_str:
            return None
        
        try:
            formats = [
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S-07:00",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%d"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str.replace('Z', '+00:00'), fmt)
                except ValueError:
                    continue
        except Exception:
            pass
        
        return None
    
    def get_trending_analysis(self, time_window: int = 24) -> Dict[str, Any]:
        """Analyze trending apps across all regions"""
        try:
            logger.info(f"Analyzing trends over {time_window} hour window")
            
            # Get current top charts
            current_charts = self.scrape_top_charts_all_regions("top-free", "all", 100)
            
            # Calculate trending metrics
            trending_apps = []
            
            for app in current_charts:
                rankings = app.get('regional_rankings', [])
                if len(rankings) >= 3:  # App must appear in at least 3 regions
                    
                    # Calculate trend score
                    trend_score = self.calculate_trend_score(app)
                    
                    if trend_score > 50:  # Threshold for "trending"
                        trending_apps.append({
                            'app': app,
                            'trend_score': trend_score,
                            'regions_count': len(rankings),
                            'average_rank': app.get('global_average_rank', 999),
                            'best_rank': app.get('best_rank', 999)
                        })
            
            # Sort by trend score
            trending_apps.sort(key=lambda x: x['trend_score'], reverse=True)
            
            analysis = {
                'trending_apps': trending_apps[:50],  # Top 50 trending
                'analysis_timestamp': datetime.now().isoformat(),
                'time_window_hours': time_window,
                'total_apps_analyzed': len(current_charts),
                'regions_covered': len(self.regions)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in trending analysis: {e}")
            return {}
    
    def calculate_trend_score(self, app: Dict[str, Any]) -> float:
        """Calculate trending score for an app"""
        try:
            score = 0.0
            
            # Regional presence (more regions = higher score)
            regions_count = app.get('regions_count', 0)
            score += min(regions_count * 5, 50)  # Max 50 points for regional presence
            
            # Average rank (better rank = higher score)
            avg_rank = app.get('global_average_rank', 999)
            rank_score = max(0, (100 - avg_rank) / 2)  # Max 50 points for rank
            score += rank_score
            
            # Consistency bonus (small variance in ranks across regions)
            rankings = [r['rank'] for r in app.get('regional_rankings', [])]
            if len(rankings) > 1:
                import statistics
                variance = statistics.variance(rankings)
                consistency_bonus = max(0, 20 - variance)  # Lower variance = higher score
                score += min(consistency_bonus, 20)
            
            return min(score, 100)  # Cap at 100
            
        except Exception as e:
            logger.error(f"Error calculating trend score: {e}")
            return 0.0
    
    def _safe_float(self, value: Any) -> float:
        """Safely convert value to float"""
        try:
            return float(value) if value is not None else 0.0
        except (ValueError, TypeError):
            return 0.0
    
    def _safe_int(self, value: Any) -> int:
        """Safely convert value to integer"""
        try:
            return int(value) if value is not None else 0
        except (ValueError, TypeError):
            return 0
    
    def _calculate_data_quality(self, raw_data: Dict[str, Any]) -> float:
        """Calculate data quality score (0-100)"""
        try:
            score = 0
            total_checks = 10
            
            # Check for essential fields
            if raw_data.get('trackId'): score += 15
            if raw_data.get('trackName'): score += 15
            if raw_data.get('artistName'): score += 10
            if raw_data.get('description'): score += 10
            if raw_data.get('averageUserRating'): score += 10
            if raw_data.get('userRatingCount'): score += 10
            if raw_data.get('price') is not None: score += 10
            if raw_data.get('version'): score += 5
            if raw_data.get('artworkUrl100'): score += 10
            if raw_data.get('trackViewUrl'): score += 5
            
            return min(score, 100)
        except:
            return 0.0
    
    def _validate_app_data(self, app_data: Dict[str, Any], expected_fields: List[str]) -> bool:
        """Validate app data completeness and accuracy"""
        try:
            # Check required fields exist and are not empty
            for field in expected_fields:
                value = app_data.get(field)
                if value is None or (isinstance(value, str) and value.strip() == ''):
                    return False
            
            # Additional validation checks
            app_id = app_data.get('app_store_id', '')
            if not app_id.isdigit() or len(app_id) < 6:
                return False
            
            # Check price is reasonable
            price = app_data.get('price', 0)
            if price < 0 or price > 1000:  # Apps shouldn't cost more than $1000
                return False
            
            # Check rating is in valid range
            rating = app_data.get('rating', 0)
            if rating < 0 or rating > 5:
                return False
                
            return True
            
        except Exception:
            return False