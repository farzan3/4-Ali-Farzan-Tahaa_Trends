"""
Comprehensive Accuracy Test Suite
Tests all scrapers with robust validation and detailed reporting
"""

import time
from datetime import datetime, timedelta
from scrapers.enhanced_app_store_scraper import EnhancedAppStoreScraper
from scrapers.enhanced_steam_scraper import EnhancedSteamScraper
from scrapers.comprehensive_events_scraper import ComprehensiveEventsScraper
from utils.robust_logger import get_logger

def test_app_store_accuracy():
    """Test App Store scraper accuracy with real data validation"""
    print("\n🍎 TESTING APP STORE SCRAPER ACCURACY")
    print("=" * 50)
    
    logger = get_logger("accuracy_test_appstore")
    scraper = EnhancedAppStoreScraper()
    
    # Test with limited regions for speed
    scraper.regions = scraper.regions[:3]  # US, UK, Canada
    
    try:
        start_time = time.time()
        apps = scraper.scrape_top_charts_all_regions('top-free', 'games', 10)
        execution_time = time.time() - start_time
        
        print(f"Execution Time: {execution_time:.2f}s")
        print(f"Apps Scraped: {len(apps)}")
        
        if apps:
            # Test first app
            app = apps[0]
            print(f"\nSample App Analysis:")
            print(f"  Title: {app.get('title', 'N/A')}")
            print(f"  Developer: {app.get('developer', 'N/A')}")
            print(f"  App Store ID: {app.get('app_store_id', 'N/A')}")
            print(f"  Price: ${app.get('price', 'N/A')}")
            print(f"  Rating: {app.get('rating', 'N/A')}/5.0")
            print(f"  Category: {app.get('category', 'N/A')}")
            print(f"  Regional Rankings: {len(app.get('regional_rankings', []))}")
            print(f"  Data Quality: {app.get('data_quality_score', 'N/A')}/100")
            
            # Accuracy checks
            accuracy_score = 0
            total_checks = 8
            
            if app.get('app_store_id', '').isdigit(): accuracy_score += 1
            if len(app.get('title', '')) > 0: accuracy_score += 1
            if len(app.get('developer', '')) > 0: accuracy_score += 1
            if isinstance(app.get('price', 0), (int, float)): accuracy_score += 1
            if 0 <= app.get('rating', 0) <= 5: accuracy_score += 1
            if len(app.get('category', '')) > 0: accuracy_score += 1
            if len(app.get('regional_rankings', [])) > 0: accuracy_score += 1
            if app.get('data_quality_score', 0) >= 50: accuracy_score += 1
            
            accuracy_percentage = (accuracy_score / total_checks) * 100
            print(f"  Accuracy Score: {accuracy_percentage:.1f}% ({accuracy_score}/{total_checks})")
            
            return {
                'platform': 'App Store',
                'success': len(apps) > 0,
                'apps_count': len(apps),
                'accuracy_percentage': accuracy_percentage,
                'execution_time': execution_time,
                'data_quality': app.get('data_quality_score', 0)
            }
        
        return {'platform': 'App Store', 'success': False, 'error': 'No apps returned'}
        
    except Exception as e:
        logger.error("App Store accuracy test failed", exception=e)
        return {'platform': 'App Store', 'success': False, 'error': str(e)}

def test_steam_accuracy():
    """Test Steam scraper accuracy with real SteamSpy data"""
    print("\n🎮 TESTING STEAM SCRAPER ACCURACY")
    print("=" * 50)
    
    logger = get_logger("accuracy_test_steam")
    scraper = EnhancedSteamScraper()
    
    try:
        start_time = time.time()
        games = scraper.get_top_sellers(10)  # Test with 10 games
        execution_time = time.time() - start_time
        
        print(f"Execution Time: {execution_time:.2f}s")
        print(f"Games Scraped: {len(games)}")
        
        if games:
            # Test first game
            game = games[0]
            print(f"\nSample Game Analysis:")
            print(f"  Title: {game.get('title', 'N/A')}")
            print(f"  Developer: {game.get('developer', 'N/A')}")
            print(f"  Steam ID: {game.get('steam_id', 'N/A')}")
            print(f"  Owners: {game.get('owners_estimate', 'N/A'):,}")
            print(f"  Players (2w): {game.get('players_2weeks', 'N/A'):,}")
            print(f"  Reviews: {game.get('total_reviews', 'N/A'):,}")
            print(f"  Positive: {game.get('positive_percentage', 'N/A'):.1f}%")
            print(f"  Data Quality: {game.get('data_quality_score', 'N/A')}/100")
            
            # Accuracy checks
            accuracy_score = 0
            total_checks = 8
            
            if game.get('steam_id', '').isdigit(): accuracy_score += 1
            if len(game.get('title', '')) > 0: accuracy_score += 1
            if len(game.get('developer', '')) > 0: accuracy_score += 1
            if isinstance(game.get('owners_estimate', 0), int): accuracy_score += 1
            if 0 <= game.get('positive_percentage', 0) <= 100: accuracy_score += 1
            if game.get('total_reviews', 0) >= 0: accuracy_score += 1
            if game.get('players_2weeks', 0) >= 0: accuracy_score += 1
            if game.get('data_quality_score', 0) >= 50: accuracy_score += 1
            
            accuracy_percentage = (accuracy_score / total_checks) * 100
            print(f"  Accuracy Score: {accuracy_percentage:.1f}% ({accuracy_score}/{total_checks})")
            
            return {
                'platform': 'Steam',
                'success': len(games) > 0,
                'games_count': len(games),
                'accuracy_percentage': accuracy_percentage,
                'execution_time': execution_time,
                'data_quality': game.get('data_quality_score', 0)
            }
        
        return {'platform': 'Steam', 'success': False, 'error': 'No games returned'}
        
    except Exception as e:
        logger.error("Steam accuracy test failed", exception=e)
        return {'platform': 'Steam', 'success': False, 'error': str(e)}

def test_events_accuracy():
    """Test Events scraper accuracy"""
    print("\n📅 TESTING EVENTS SCRAPER ACCURACY")
    print("=" * 50)
    
    logger = get_logger("accuracy_test_events")
    scraper = ComprehensiveEventsScraper()
    
    try:
        start_time = time.time()
        
        # Test major holidays
        end_date = datetime.now() + timedelta(days=60)
        holidays = scraper.scrape_major_holidays(end_date)
        
        # Test comprehensive events
        comprehensive = scraper.scrape_comprehensive_events(months_ahead=2)
        
        execution_time = time.time() - start_time
        
        print(f"Execution Time: {execution_time:.2f}s")
        print(f"Holidays: {len(holidays)}")
        print(f"Total Event Categories: {len(comprehensive)}")
        
        total_events = sum(len(events) for events in comprehensive.values() if isinstance(events, list))
        print(f"Total Events: {total_events}")
        
        if holidays:
            # Test first holiday
            holiday = holidays[0]
            print(f"\nSample Holiday Analysis:")
            print(f"  Name: {holiday.get('name', 'N/A')}")
            print(f"  Date: {holiday.get('start_date', 'N/A')}")
            print(f"  Category: {holiday.get('category', 'N/A')}")
            print(f"  Impact Score: {holiday.get('impact_score', 'N/A')}")
            print(f"  Tags: {len(holiday.get('tags', []))}")
            
            # Accuracy checks
            accuracy_score = 0
            total_checks = 6
            
            if len(holiday.get('name', '')) > 0: accuracy_score += 1
            if holiday.get('start_date'): accuracy_score += 1
            if len(holiday.get('category', '')) > 0: accuracy_score += 1
            if 0 <= holiday.get('impact_score', 0) <= 100: accuracy_score += 1
            if len(holiday.get('tags', [])) > 0: accuracy_score += 1
            if holiday.get('scraped_at'): accuracy_score += 1
            
            accuracy_percentage = (accuracy_score / total_checks) * 100
            print(f"  Accuracy Score: {accuracy_percentage:.1f}% ({accuracy_score}/{total_checks})")
            
            return {
                'platform': 'Events',
                'success': len(holidays) > 0,
                'events_count': total_events,
                'holidays_count': len(holidays),
                'accuracy_percentage': accuracy_percentage,
                'execution_time': execution_time
            }
        
        return {'platform': 'Events', 'success': False, 'error': 'No events returned'}
        
    except Exception as e:
        logger.error("Events accuracy test failed", exception=e)
        return {'platform': 'Events', 'success': False, 'error': str(e)}

def generate_comprehensive_report(results):
    """Generate comprehensive accuracy report"""
    print("\n" + "="*80)
    print("🎯 COMPREHENSIVE SCRAPING ACCURACY REPORT")
    print("="*80)
    
    total_platforms = len(results)
    successful_platforms = len([r for r in results if r.get('success', False)])
    
    print(f"\nOVERALL SUMMARY:")
    print(f"  Platforms Tested: {total_platforms}")
    print(f"  Successful Platforms: {successful_platforms}")
    print(f"  Overall Success Rate: {(successful_platforms/total_platforms)*100:.1f}%")
    
    print(f"\nDETAILED RESULTS:")
    print("-" * 60)
    
    total_accuracy = 0
    total_execution_time = 0
    
    for result in results:
        platform = result.get('platform', 'Unknown')
        success = result.get('success', False)
        
        if success:
            status = "✅ PASS"
            accuracy = result.get('accuracy_percentage', 0)
            execution_time = result.get('execution_time', 0)
            
            print(f"{platform:12} | {status:8} | {accuracy:5.1f}% | {execution_time:6.2f}s")
            
            # Platform-specific details
            if platform == 'App Store':
                print(f"             | Apps: {result.get('apps_count', 0):4} | Quality: {result.get('data_quality', 0):3}/100")
            elif platform == 'Steam':
                print(f"             | Games: {result.get('games_count', 0):3} | Quality: {result.get('data_quality', 0):3}/100")
            elif platform == 'Events':
                print(f"             | Events: {result.get('events_count', 0):3} | Holidays: {result.get('holidays_count', 0):2}")
            
            total_accuracy += accuracy
            total_execution_time += execution_time
        else:
            status = "❌ FAIL"
            error = result.get('error', 'Unknown error')
            print(f"{platform:12} | {status:8} | Error: {error}")
    
    if successful_platforms > 0:
        avg_accuracy = total_accuracy / successful_platforms
        print(f"\nPERFORMANCE METRICS:")
        print(f"  Average Accuracy: {avg_accuracy:.1f}%")
        print(f"  Total Execution Time: {total_execution_time:.2f}s")
        print(f"  Average Response Time: {total_execution_time/successful_platforms:.2f}s")
        
        # Overall assessment
        if avg_accuracy >= 90 and successful_platforms == total_platforms:
            print(f"\n🎉 EXCELLENT: All scrapers performing at high accuracy!")
        elif avg_accuracy >= 80:
            print(f"\n✅ GOOD: Scrapers performing well with room for improvement")
        else:
            print(f"\n⚠️  WARNING: Some scrapers need attention")

def main():
    """Run comprehensive accuracy testing"""
    print("🔍 HUNTER PLATFORM - COMPREHENSIVE SCRAPING ACCURACY TEST")
    print("="*80)
    print(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Test all scrapers
    try:
        results.append(test_app_store_accuracy())
    except Exception as e:
        print(f"App Store test failed: {e}")
        results.append({'platform': 'App Store', 'success': False, 'error': str(e)})
    
    try:
        results.append(test_steam_accuracy())
    except Exception as e:
        print(f"Steam test failed: {e}")
        results.append({'platform': 'Steam', 'success': False, 'error': str(e)})
    
    try:
        results.append(test_events_accuracy())
    except Exception as e:
        print(f"Events test failed: {e}")
        results.append({'platform': 'Events', 'success': False, 'error': str(e)})
    
    # Generate comprehensive report
    generate_comprehensive_report(results)
    
    print(f"\nTest Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

if __name__ == "__main__":
    main()