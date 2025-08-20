"""
Simplified Analytics Processor that works without heavy ML dependencies
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalyticsProcessor:
    def __init__(self):
        # Initialize without heavy ML models for basic functionality
        self.sentiment_analyzer = None
        self.similarity_model = None
        logger.info("Analytics processor initialized in simple mode")
    
    def analyze_ranking_velocity(self, app_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze ranking velocity and detect fast climbers"""
        try:
            if not app_data:
                return {'error': 'No app data provided'}
            
            df = pd.DataFrame(app_data)
            
            if df.empty:
                return {'error': 'Invalid app data'}
            
            # Mock velocity calculation for demonstration
            velocities = []
            for app in app_data:
                current_rank = app.get('current_rank', 50)
                previous_rank = app.get('previous_rank', current_rank)
                
                if previous_rank > 0:
                    velocity = ((previous_rank - current_rank) / previous_rank) * 100
                    velocities.append({
                        'title': app.get('title', 'Unknown'),
                        'current_rank': current_rank,
                        'previous_rank': previous_rank,
                        'velocity_score': round(velocity, 2)
                    })
            
            # Sort by velocity
            velocities.sort(key=lambda x: x['velocity_score'], reverse=True)
            
            analysis = {
                'total_apps': len(app_data),
                'fast_climbers': velocities[:10],  # Top 10 climbers
                'sudden_drops': [v for v in velocities if v['velocity_score'] < -20],
                'average_velocity': np.mean([v['velocity_score'] for v in velocities]) if velocities else 0
            }
            
            logger.info(f"Ranking velocity analysis completed for {len(app_data)} apps")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing ranking velocity: {e}")
            return {'error': str(e)}
    
    def analyze_review_sentiment(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simple sentiment analysis without ML models"""
        try:
            if not reviews:
                return {'error': 'No reviews provided'}
            
            # Simple keyword-based sentiment analysis
            positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'best', 'awesome', 'perfect']
            negative_words = ['bad', 'terrible', 'awful', 'hate', 'worst', 'horrible', 'useless', 'broken']
            
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            
            for review in reviews:
                review_text = review.get('review_text', '').lower()
                rating = review.get('rating', 3)
                
                # Use rating as primary indicator
                if rating >= 4:
                    positive_count += 1
                elif rating <= 2:
                    negative_count += 1
                else:
                    # For 3-star reviews, use keyword analysis
                    pos_matches = sum(1 for word in positive_words if word in review_text)
                    neg_matches = sum(1 for word in negative_words if word in review_text)
                    
                    if pos_matches > neg_matches:
                        positive_count += 1
                    elif neg_matches > pos_matches:
                        negative_count += 1
                    else:
                        neutral_count += 1
            
            total_reviews = len(reviews)
            
            analysis = {
                'total_reviews_analyzed': total_reviews,
                'positive_percentage': (positive_count / total_reviews) * 100,
                'negative_percentage': (negative_count / total_reviews) * 100,
                'neutral_percentage': (neutral_count / total_reviews) * 100,
                'sentiment_distribution': {
                    'positive': positive_count,
                    'negative': negative_count,
                    'neutral': neutral_count
                }
            }
            
            logger.info(f"Sentiment analysis completed for {total_reviews} reviews")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing review sentiment: {e}")
            return {'error': str(e)}
    
    def analyze_monetization_patterns(self, apps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze monetization patterns"""
        try:
            if not apps:
                return {'error': 'No app data provided'}
            
            free_apps = [app for app in apps if app.get('price', 0) == 0]
            paid_apps = [app for app in apps if app.get('price', 0) > 0]
            
            # Analyze IAP patterns
            apps_with_iap = [app for app in apps if app.get('iap_products')]
            
            analysis = {
                'total_apps': len(apps),
                'free_apps': len(free_apps),
                'paid_apps': len(paid_apps),
                'apps_with_iap': len(apps_with_iap),
                'average_price': np.mean([app.get('price', 0) for app in paid_apps]) if paid_apps else 0,
                'price_distribution': {
                    'under_1': len([app for app in paid_apps if app.get('price', 0) < 1]),
                    '1_to_5': len([app for app in paid_apps if 1 <= app.get('price', 0) < 5]),
                    '5_to_10': len([app for app in paid_apps if 5 <= app.get('price', 0) < 10]),
                    'over_10': len([app for app in paid_apps if app.get('price', 0) >= 10])
                }
            }
            
            logger.info(f"Monetization analysis completed for {len(apps)} apps")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing monetization patterns: {e}")
            return {'error': str(e)}
    
    def detect_clones(self, apps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Simple clone detection using string similarity"""
        try:
            clones = []
            
            for i, app1 in enumerate(apps):
                for j, app2 in enumerate(apps[i+1:], i+1):
                    # Simple title similarity
                    title1 = app1.get('title', '').lower()
                    title2 = app2.get('title', '').lower()
                    
                    # Calculate simple similarity
                    similarity = self._simple_text_similarity(title1, title2)
                    
                    if similarity > 0.6:  # 60% similarity threshold
                        clones.append({
                            'app1_id': app1.get('app_store_id', ''),
                            'app1_title': app1.get('title', ''),
                            'app2_id': app2.get('app_store_id', ''),
                            'app2_title': app2.get('title', ''),
                            'similarity_score': similarity,
                            'detection_type': 'title_similarity'
                        })
            
            logger.info(f"Clone detection completed, found {len(clones)} potential clones")
            return clones
            
        except Exception as e:
            logger.error(f"Error detecting clones: {e}")
            return []
    
    def _simple_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity using word overlap"""
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def analyze_seasonal_trends(self, apps: List[Dict[str, Any]], 
                              events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze seasonal trends"""
        try:
            current_date = datetime.now()
            
            # Simple category analysis
            categories = {}
            for app in apps:
                category = app.get('category', 'Unknown')
                if category not in categories:
                    categories[category] = {'count': 0, 'avg_rating': 0}
                
                categories[category]['count'] += 1
                categories[category]['avg_rating'] += app.get('rating', 0)
            
            # Calculate averages
            for category in categories:
                if categories[category]['count'] > 0:
                    categories[category]['avg_rating'] /= categories[category]['count']
            
            # Generate seasonal insights
            month = current_date.month
            seasonal_insights = {
                1: ["New Year fitness apps trending", "Resolution-based productivity apps popular"],
                2: ["Valentine's Day dating apps surge", "Photo editing apps for romantic content"],
                12: ["Holiday shopping apps", "Christmas-themed entertainment apps"]
            }.get(month, ["General app trends"])
            
            analysis = {
                'category_distribution': categories,
                'seasonal_insights': seasonal_insights,
                'current_month': month,
                'total_events': len(events) if events else 0
            }
            
            logger.info("Seasonal trend analysis completed")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing seasonal trends: {e}")
            return {'error': str(e)}