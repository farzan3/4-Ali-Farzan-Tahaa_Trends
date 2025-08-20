import schedule
import time
import threading
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path

# Optional async imports
try:
    import asyncio
    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False

# Import enhanced scrapers
from scrapers.enhanced_app_store_scraper import EnhancedAppStoreScraper
from scrapers.enhanced_steam_scraper import EnhancedSteamScraper  
from scrapers.comprehensive_events_scraper import ComprehensiveEventsScraper

# Import analysis engines
try:
    from analytics.processor import AnalyticsProcessor
except ImportError:
    from analytics.processor_simple import AnalyticsProcessor

try:
    from ml.predictor import SuccessPredictor
except ImportError:
    # Fallback predictor
    class SuccessPredictor:
        def calculate_weighted_score(self, app_data, analytics_data=None):
            return {'success_score': 75.0, 'confidence': 0.8}

from models import database, App, SteamGame, Event, Score
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutomatedDataPipeline:
    def __init__(self):
        self.app_store_scraper = EnhancedAppStoreScraper()
        self.steam_scraper = EnhancedSteamScraper()
        self.events_scraper = ComprehensiveEventsScraper()
        self.analytics = AnalyticsProcessor()
        self.predictor = SuccessPredictor()
        
        # Pipeline state
        self.is_running = False
        self.last_run_times = {
            'app_store_full': None,
            'app_store_quick': None,
            'steam_comprehensive': None,
            'steam_quick': None,
            'events_comprehensive': None,
            'events_daily': None,
            'analysis': None
        }
        
        # Data cache
        self.data_cache = {
            'apps': [],
            'steam_games': [],
            'events': [],
            'analysis': {},
            'last_updated': None
        }
        
        # Pipeline configuration
        self.config = {
            'app_store_full_interval': 6,  # hours
            'app_store_quick_interval': 1,  # hours
            'steam_comprehensive_interval': 12,  # hours
            'steam_quick_interval': 2,  # hours
            'events_comprehensive_interval': 24,  # hours
            'events_daily_interval': 6,  # hours
            'analysis_interval': 2,  # hours
            'max_workers': 4,
            'retry_attempts': 3,
            'data_retention_days': 30
        }
        
        self.executor = ThreadPoolExecutor(max_workers=self.config['max_workers'])
        self.scheduler_thread = None
        
    def start_pipeline(self):
        """Start the automated data pipeline"""
        if self.is_running:
            logger.warning("Pipeline is already running")
            return
        
        logger.info("Starting automated data pipeline")
        self.is_running = True
        
        # Schedule all pipeline jobs
        self.schedule_jobs()
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Automated data pipeline started successfully")
    
    def stop_pipeline(self):
        """Stop the automated data pipeline"""
        logger.info("Stopping automated data pipeline")
        self.is_running = False
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=10)
        
        self.executor.shutdown(wait=True)
        logger.info("Automated data pipeline stopped")
    
    def schedule_jobs(self):
        """Schedule all pipeline jobs"""
        # App Store scraping jobs
        schedule.every(self.config['app_store_full_interval']).hours.do(
            self.run_job_async, 'app_store_full_scrape'
        )
        schedule.every(self.config['app_store_quick_interval']).hours.do(
            self.run_job_async, 'app_store_quick_scrape'
        )
        
        # Steam scraping jobs
        schedule.every(self.config['steam_comprehensive_interval']).hours.do(
            self.run_job_async, 'steam_comprehensive_scrape'
        )
        schedule.every(self.config['steam_quick_interval']).hours.do(
            self.run_job_async, 'steam_quick_scrape'
        )
        
        # Events scraping jobs
        schedule.every(self.config['events_comprehensive_interval']).hours.do(
            self.run_job_async, 'events_comprehensive_scrape'
        )
        schedule.every(self.config['events_daily_interval']).hours.do(
            self.run_job_async, 'events_daily_scrape'
        )
        
        # Analysis job
        schedule.every(self.config['analysis_interval']).hours.do(
            self.run_job_async, 'comprehensive_analysis'
        )
        
        # Maintenance jobs
        schedule.every(24).hours.do(self.run_job_async, 'data_cleanup')
        schedule.every(12).hours.do(self.run_job_async, 'health_check')
        
        logger.info("All pipeline jobs scheduled")
    
    def run_scheduler(self):
        """Run the job scheduler"""
        logger.info("Pipeline scheduler started")
        
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(300)  # Wait 5 minutes on error
        
        logger.info("Pipeline scheduler stopped")
    
    def run_job_async(self, job_name: str):
        """Run a job asynchronously"""
        if not self.is_running:
            return
        
        future = self.executor.submit(self.execute_job, job_name)
        future.add_done_callback(lambda f: self.handle_job_completion(job_name, f))
    
    def execute_job(self, job_name: str) -> Dict[str, Any]:
        """Execute a specific pipeline job"""
        start_time = datetime.now()
        logger.info(f"Executing job: {job_name}")
        
        try:
            result = {'job': job_name, 'status': 'success', 'start_time': start_time}
            
            if job_name == 'app_store_full_scrape':
                result['data'] = self.app_store_full_scrape()
            elif job_name == 'app_store_quick_scrape':
                result['data'] = self.app_store_quick_scrape()
            elif job_name == 'steam_comprehensive_scrape':
                result['data'] = self.steam_comprehensive_scrape()
            elif job_name == 'steam_quick_scrape':
                result['data'] = self.steam_quick_scrape()
            elif job_name == 'events_comprehensive_scrape':
                result['data'] = self.events_comprehensive_scrape()
            elif job_name == 'events_daily_scrape':
                result['data'] = self.events_daily_scrape()
            elif job_name == 'comprehensive_analysis':
                result['data'] = self.comprehensive_analysis()
            elif job_name == 'data_cleanup':
                result['data'] = self.data_cleanup()
            elif job_name == 'health_check':
                result['data'] = self.health_check()
            else:
                result['status'] = 'error'
                result['error'] = f"Unknown job: {job_name}"
            
            result['end_time'] = datetime.now()
            result['duration'] = (result['end_time'] - start_time).total_seconds()
            
            self.last_run_times[job_name.replace('_scrape', '')] = datetime.now()
            
            return result
            
        except Exception as e:
            logger.error(f"Job {job_name} failed: {e}")
            return {
                'job': job_name,
                'status': 'error',
                'error': str(e),
                'start_time': start_time,
                'end_time': datetime.now()
            }
    
    def handle_job_completion(self, job_name: str, future):
        """Handle job completion"""
        try:
            result = future.result()
            if result['status'] == 'success':
                logger.info(f"Job {job_name} completed successfully in {result.get('duration', 0):.2f}s")
            else:
                logger.error(f"Job {job_name} failed: {result.get('error', 'Unknown error')}")
        except Exception as e:
            logger.error(f"Error handling job completion for {job_name}: {e}")
    
    def app_store_full_scrape(self) -> Dict[str, Any]:
        """Full App Store scrape across all regions and categories"""
        logger.info("Starting full App Store scrape")
        
        results = {
            'top_free': [],
            'top_paid': [],
            'top_grossing': [],
            'new_apps': []
        }
        
        # Scrape different chart types
        for chart_type in ['top-free', 'top-paid', 'top-grossing', 'new-apps']:
            logger.info(f"Scraping {chart_type} charts")
            
            try:
                apps = self.app_store_scraper.scrape_top_charts_all_regions(
                    feed_type=chart_type,
                    category='all',
                    limit=200
                )
                
                results[chart_type.replace('-', '_')] = apps
                
                # Store in database
                self.store_apps_data(apps)
                
                # Add to cache
                self.data_cache['apps'].extend(apps)
                
            except Exception as e:
                logger.error(f"Error scraping {chart_type}: {e}")
        
        # Deduplicate cache
        self.deduplicate_apps_cache()
        
        total_apps = sum(len(apps) for apps in results.values())
        logger.info(f"Full App Store scrape complete: {total_apps} apps processed")
        
        return {
            'total_apps': total_apps,
            'charts_scraped': len(results),
            'results': results
        }
    
    def app_store_quick_scrape(self) -> Dict[str, Any]:
        """Quick App Store scrape for trending detection"""
        logger.info("Starting quick App Store scrape")
        
        try:
            # Get trending analysis
            trending_data = self.app_store_scraper.get_trending_analysis()
            
            # Extract trending apps
            trending_apps = trending_data.get('trending_apps', [])
            
            # Store trending apps
            for app_data in trending_apps:
                app = app_data.get('app', {})
                if app:
                    self.store_apps_data([app])
            
            logger.info(f"Quick App Store scrape complete: {len(trending_apps)} trending apps")
            
            return {
                'trending_apps_count': len(trending_apps),
                'analysis_timestamp': trending_data.get('analysis_timestamp'),
                'regions_covered': trending_data.get('regions_covered', 0)
            }
            
        except Exception as e:
            logger.error(f"Quick App Store scrape failed: {e}")
            return {'error': str(e)}
    
    def steam_comprehensive_scrape(self) -> Dict[str, Any]:
        """Comprehensive Steam scrape"""
        logger.info("Starting comprehensive Steam scrape")
        
        try:
            trending_data = self.steam_scraper.scrape_comprehensive_trending()
            
            # Store Steam games
            all_games = []
            for category, games in trending_data.items():
                if isinstance(games, list):
                    all_games.extend(games)
            
            self.store_steam_data(all_games)
            
            # Update cache
            self.data_cache['steam_games'] = all_games
            
            total_games = len(all_games)
            logger.info(f"Comprehensive Steam scrape complete: {total_games} games processed")
            
            return {
                'total_games': total_games,
                'categories_scraped': len([k for k, v in trending_data.items() if isinstance(v, list)]),
                'comprehensive_ranking_count': len(trending_data.get('comprehensive_ranking', []))
            }
            
        except Exception as e:
            logger.error(f"Comprehensive Steam scrape failed: {e}")
            return {'error': str(e)}
    
    def steam_quick_scrape(self) -> Dict[str, Any]:
        """Quick Steam scrape for immediate trends"""
        logger.info("Starting quick Steam scrape")
        
        try:
            # Get just top sellers and trending
            top_sellers = self.steam_scraper.get_top_sellers(50)
            trending_games = self.steam_scraper.get_trending_games(50)
            
            all_games = top_sellers + trending_games
            
            # Store games
            self.store_steam_data(all_games)
            
            logger.info(f"Quick Steam scrape complete: {len(all_games)} games processed")
            
            return {
                'top_sellers_count': len(top_sellers),
                'trending_count': len(trending_games),
                'total_games': len(all_games)
            }
            
        except Exception as e:
            logger.error(f"Quick Steam scrape failed: {e}")
            return {'error': str(e)}
    
    def events_comprehensive_scrape(self) -> Dict[str, Any]:
        """Comprehensive events scraping"""
        logger.info("Starting comprehensive events scrape")
        
        try:
            events_data = self.events_scraper.scrape_comprehensive_events(months_ahead=6)
            
            # Store events
            all_events = []
            for category, events in events_data.items():
                if isinstance(events, list):
                    all_events.extend(events)
            
            self.store_events_data(all_events)
            
            # Update cache
            self.data_cache['events'] = all_events
            
            total_events = len(all_events)
            logger.info(f"Comprehensive events scrape complete: {total_events} events processed")
            
            return {
                'total_events': total_events,
                'categories_scraped': len([k for k, v in events_data.items() if isinstance(v, list)]),
                'high_impact_events': len(events_data.get('comprehensive_analysis', {}).get('high_impact_events', []))
            }
            
        except Exception as e:
            logger.error(f"Comprehensive events scrape failed: {e}")
            return {'error': str(e)}
    
    def events_daily_scrape(self) -> Dict[str, Any]:
        """Daily events update"""
        logger.info("Starting daily events scrape")
        
        try:
            # Get trending topics and immediate events
            trending = self.events_scraper.scrape_trending_topics()
            holidays = self.events_scraper.scrape_major_holidays(
                datetime.now() + timedelta(days=30)
            )
            
            all_events = trending + holidays
            
            # Store events
            self.store_events_data(all_events)
            
            logger.info(f"Daily events scrape complete: {len(all_events)} events processed")
            
            return {
                'trending_topics': len(trending),
                'upcoming_holidays': len(holidays),
                'total_events': len(all_events)
            }
            
        except Exception as e:
            logger.error(f"Daily events scrape failed: {e}")
            return {'error': str(e)}
    
    def comprehensive_analysis(self) -> Dict[str, Any]:
        """Run comprehensive cross-platform analysis"""
        logger.info("Starting comprehensive analysis")
        
        try:
            analysis_results = {}
            
            # App Store analysis
            if self.data_cache['apps']:
                app_analysis = self.analytics.analyze_ranking_velocity(self.data_cache['apps'])
                analysis_results['app_store'] = app_analysis
            
            # Steam analysis  
            if self.data_cache['steam_games']:
                steam_analysis = self.analyze_steam_trends()
                analysis_results['steam'] = steam_analysis
            
            # Events analysis
            if self.data_cache['events']:
                events_analysis = self.analytics.analyze_seasonal_trends(
                    self.data_cache['apps'], 
                    self.data_cache['events']
                )
                analysis_results['events'] = events_analysis
            
            # Cross-platform correlation
            correlation_analysis = self.analyze_cross_platform_correlation()
            analysis_results['cross_platform'] = correlation_analysis
            
            # Success predictions
            predictions = self.generate_success_predictions()
            analysis_results['predictions'] = predictions
            
            # Store analysis results
            self.data_cache['analysis'] = analysis_results
            self.data_cache['last_updated'] = datetime.now()
            
            logger.info("Comprehensive analysis complete")
            
            return {
                'analysis_categories': len(analysis_results),
                'apps_analyzed': len(self.data_cache['apps']),
                'steam_games_analyzed': len(self.data_cache['steam_games']),
                'events_analyzed': len(self.data_cache['events']),
                'predictions_generated': len(predictions.get('top_predictions', []))
            }
            
        except Exception as e:
            logger.error(f"Comprehensive analysis failed: {e}")
            return {'error': str(e)}
    
    def analyze_steam_trends(self) -> Dict[str, Any]:
        """Analyze Steam game trends"""
        try:
            steam_games = self.data_cache['steam_games']
            
            # Calculate trend metrics
            trending_games = []
            for game in steam_games:
                trend_score = game.get('comprehensive_score', 0)
                if trend_score > 60:
                    trending_games.append({
                        'title': game.get('title', 'Unknown'),
                        'trend_score': trend_score,
                        'sources': game.get('sources', []),
                        'price': game.get('price', 0)
                    })
            
            # Sort by trend score
            trending_games.sort(key=lambda x: x['trend_score'], reverse=True)
            
            return {
                'total_games': len(steam_games),
                'trending_games': trending_games[:20],
                'average_trend_score': sum(g['trend_score'] for g in trending_games) / len(trending_games) if trending_games else 0,
                'free_games_trending': len([g for g in trending_games if g['price'] == 0])
            }
            
        except Exception as e:
            logger.error(f"Steam trends analysis failed: {e}")
            return {'error': str(e)}
    
    def analyze_cross_platform_correlation(self) -> Dict[str, Any]:
        """Analyze correlations between App Store and Steam"""
        try:
            correlations = []
            
            # Find similar game titles/genres between platforms
            app_games = [app for app in self.data_cache['apps'] if 'game' in app.get('category', '').lower()]
            steam_games = self.data_cache['steam_games']
            
            # Simple correlation based on title similarity
            for app in app_games[:50]:  # Limit for performance
                app_title = app.get('title', '').lower()
                for steam_game in steam_games[:100]:
                    steam_title = steam_game.get('title', '').lower()
                    
                    # Simple similarity check
                    similarity = self.calculate_title_similarity(app_title, steam_title)
                    if similarity > 0.6:
                        correlations.append({
                            'app_title': app.get('title'),
                            'steam_title': steam_game.get('title'),
                            'similarity': similarity,
                            'app_rank': app.get('global_average_rank', 999),
                            'steam_score': steam_game.get('comprehensive_score', 0)
                        })
            
            # Sort by similarity
            correlations.sort(key=lambda x: x['similarity'], reverse=True)
            
            return {
                'correlations_found': len(correlations),
                'top_correlations': correlations[:10],
                'avg_similarity': sum(c['similarity'] for c in correlations) / len(correlations) if correlations else 0
            }
            
        except Exception as e:
            logger.error(f"Cross-platform correlation analysis failed: {e}")
            return {'error': str(e)}
    
    def calculate_title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles"""
        words1 = set(title1.split())
        words2 = set(title2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def generate_success_predictions(self) -> Dict[str, Any]:
        """Generate success predictions for apps and games"""
        try:
            predictions = []
            
            # Predict for top apps
            for app in self.data_cache['apps'][:100]:
                try:
                    prediction = self.predictor.calculate_weighted_score(app)
                    if prediction.get('success_score', 0) > 70:
                        predictions.append({
                            'title': app.get('title', 'Unknown'),
                            'platform': 'App Store',
                            'success_score': prediction.get('success_score', 0),
                            'confidence': prediction.get('confidence', 0),
                            'rank': app.get('global_average_rank', 999)
                        })
                except Exception as e:
                    logger.error(f"Prediction error for app {app.get('title', 'Unknown')}: {e}")
            
            # Predict for Steam games (simplified)
            for game in self.data_cache['steam_games'][:50]:
                try:
                    # Convert Steam data to app format for prediction
                    game_as_app = {
                        'title': game.get('title', ''),
                        'rating': game.get('review_score', 0) / 2,  # Convert 0-10 to 0-5 scale
                        'review_count': game.get('total_reviews', 0),
                        'price': game.get('price', 0)
                    }
                    
                    prediction = self.predictor.calculate_weighted_score(game_as_app)
                    if prediction.get('success_score', 0) > 70:
                        predictions.append({
                            'title': game.get('title', 'Unknown'),
                            'platform': 'Steam',
                            'success_score': prediction.get('success_score', 0),
                            'confidence': prediction.get('confidence', 0),
                            'comprehensive_score': game.get('comprehensive_score', 0)
                        })
                except Exception as e:
                    logger.error(f"Prediction error for Steam game {game.get('title', 'Unknown')}: {e}")
            
            # Sort by success score
            predictions.sort(key=lambda x: x['success_score'], reverse=True)
            
            return {
                'total_predictions': len(predictions),
                'top_predictions': predictions[:20],
                'platform_breakdown': {
                    'app_store': len([p for p in predictions if p['platform'] == 'App Store']),
                    'steam': len([p for p in predictions if p['platform'] == 'Steam'])
                }
            }
            
        except Exception as e:
            logger.error(f"Success predictions generation failed: {e}")
            return {'error': str(e)}
    
    def data_cleanup(self) -> Dict[str, Any]:
        """Clean up old data"""
        logger.info("Starting data cleanup")
        
        try:
            cutoff_date = datetime.now() - timedelta(days=self.config['data_retention_days'])
            
            # Clean up cache
            original_apps_count = len(self.data_cache['apps'])
            original_games_count = len(self.data_cache['steam_games'])
            original_events_count = len(self.data_cache['events'])
            
            # Keep only recent data in cache
            self.data_cache['apps'] = [
                app for app in self.data_cache['apps'] 
                if self.parse_date(app.get('scraped_at', '')) and 
                self.parse_date(app.get('scraped_at', '')) > cutoff_date
            ]
            
            self.data_cache['steam_games'] = [
                game for game in self.data_cache['steam_games']
                if self.parse_date(game.get('scraped_at', '')) and
                self.parse_date(game.get('scraped_at', '')) > cutoff_date
            ]
            
            self.data_cache['events'] = [
                event for event in self.data_cache['events']
                if self.parse_date(event.get('scraped_at', '')) and
                self.parse_date(event.get('scraped_at', '')) > cutoff_date
            ]
            
            cleaned_apps = original_apps_count - len(self.data_cache['apps'])
            cleaned_games = original_games_count - len(self.data_cache['steam_games'])
            cleaned_events = original_events_count - len(self.data_cache['events'])
            
            logger.info(f"Data cleanup complete: removed {cleaned_apps} apps, {cleaned_games} games, {cleaned_events} events")
            
            return {
                'apps_cleaned': cleaned_apps,
                'games_cleaned': cleaned_games,
                'events_cleaned': cleaned_events,
                'total_cleaned': cleaned_apps + cleaned_games + cleaned_events
            }
            
        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")
            return {'error': str(e)}
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime"""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            return None
    
    def health_check(self) -> Dict[str, Any]:
        """Perform system health check"""
        logger.info("Performing health check")
        
        try:
            health_status = {
                'pipeline_running': self.is_running,
                'last_run_times': self.last_run_times,
                'cache_status': {
                    'apps_count': len(self.data_cache['apps']),
                    'steam_games_count': len(self.data_cache['steam_games']),
                    'events_count': len(self.data_cache['events']),
                    'last_updated': self.data_cache.get('last_updated')
                },
                'executor_status': {
                    'max_workers': self.executor._max_workers,
                    'active_threads': len(self.executor._threads)
                },
                'scheduler_status': {
                    'thread_alive': self.scheduler_thread.is_alive() if self.scheduler_thread else False,
                    'scheduled_jobs': len(schedule.jobs)
                }
            }
            
            logger.info("Health check complete")
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {'error': str(e)}
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status"""
        return {
            'is_running': self.is_running,
            'last_run_times': self.last_run_times,
            'cache_summary': {
                'apps': len(self.data_cache['apps']),
                'steam_games': len(self.data_cache['steam_games']),
                'events': len(self.data_cache['events']),
                'last_analysis': self.data_cache.get('last_updated')
            },
            'config': self.config
        }
    
    def deduplicate_apps_cache(self):
        """Remove duplicate apps from cache"""
        seen_ids = set()
        unique_apps = []
        
        for app in self.data_cache['apps']:
            app_id = app.get('app_store_id')
            if app_id and app_id not in seen_ids:
                seen_ids.add(app_id)
                unique_apps.append(app)
        
        self.data_cache['apps'] = unique_apps
    
    def store_apps_data(self, apps: List[Dict[str, Any]]):
        """Store apps data in database with proper datetime handling"""
        try:
            session = database.get_session()
            
            for app_data in apps:
                # Sanitize datetime fields for SQLite compatibility
                sanitized_data = self._sanitize_datetime_fields(app_data)
                
                # Create or update app record
                existing_app = session.query(App).filter_by(
                    app_store_id=sanitized_data.get('app_store_id')
                ).first()
                
                if existing_app:
                    # Update existing app
                    for key, value in sanitized_data.items():
                        if hasattr(existing_app, key):
                            setattr(existing_app, key, value)
                else:
                    # Create new app
                    filtered_data = {k: v for k, v in sanitized_data.items() if hasattr(App, k)}
                    new_app = App(**filtered_data)
                    session.add(new_app)
            
            session.commit()
            database.close_session(session)
            
        except Exception as e:
            logger.error(f"Error storing apps data: {e}")
    
    def store_steam_data(self, games: List[Dict[str, Any]]):
        """Store Steam games data in database with proper datetime handling"""
        try:
            session = database.get_session()
            
            for game_data in games:
                # Sanitize datetime fields for SQLite compatibility
                sanitized_data = self._sanitize_datetime_fields(game_data)
                
                # Create or update Steam game record
                existing_game = session.query(SteamGame).filter_by(
                    steam_id=sanitized_data.get('steam_id')
                ).first()
                
                if existing_game:
                    # Update existing game
                    for key, value in sanitized_data.items():
                        if hasattr(existing_game, key):
                            setattr(existing_game, key, value)
                else:
                    # Create new game
                    filtered_data = {k: v for k, v in sanitized_data.items() if hasattr(SteamGame, k)}
                    new_game = SteamGame(**filtered_data)
                    session.add(new_game)
            
            session.commit()
            database.close_session(session)
            
        except Exception as e:
            logger.error(f"Error storing Steam data: {e}")
    
    def store_events_data(self, events: List[Dict[str, Any]]):
        """Store events data in database with proper datetime handling"""
        try:
            session = database.get_session()
            
            for event_data in events:
                # Sanitize datetime fields for SQLite compatibility
                sanitized_data = self._sanitize_datetime_fields(event_data)
                
                # Create or update event record
                event_name = sanitized_data.get('name')
                
                existing_event = session.query(Event).filter_by(
                    name=event_name
                ).first()
                
                if existing_event:
                    # Update existing event
                    for key, value in sanitized_data.items():
                        if hasattr(existing_event, key):
                            setattr(existing_event, key, value)
                else:
                    # Create new event
                    filtered_data = {k: v for k, v in sanitized_data.items() if hasattr(Event, k)}
                    new_event = Event(**filtered_data)
                    session.add(new_event)
            
            session.commit()
            database.close_session(session)
            
        except Exception as e:
            logger.error(f"Error storing events data: {e}")
    
    def _sanitize_datetime_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize datetime fields for SQLite compatibility"""
        sanitized = data.copy()
        
        # List of common datetime field names
        datetime_fields = [
            'last_updated', 'scraped_at', 'release_date', 'current_version_release_date',
            'start_date', 'end_date', 'timestamp', 'created_at', 'updated_at'
        ]
        
        for field in datetime_fields:
            if field in sanitized and sanitized[field]:
                value = sanitized[field]
                
                if isinstance(value, str):
                    try:
                        # Parse ISO format string and make timezone-naive
                        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        sanitized[field] = dt.replace(tzinfo=None)
                    except (ValueError, TypeError):
                        # If parsing fails, use current time as fallback
                        sanitized[field] = datetime.now().replace(tzinfo=None)
                        
                elif isinstance(value, datetime):
                    # Make timezone-naive for SQLite
                    sanitized[field] = value.replace(tzinfo=None)
        
        return sanitized

# Global pipeline instance
automated_pipeline = AutomatedDataPipeline()