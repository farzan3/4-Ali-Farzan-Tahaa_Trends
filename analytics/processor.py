import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from transformers import pipeline
from sentence_transformers import SentenceTransformer
import cv2
from PIL import Image
import requests
from io import BytesIO
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalyticsProcessor:
    def __init__(self):
        self.sentiment_analyzer = None
        self.similarity_model = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize ML models"""
        try:
            # Initialize sentiment analysis model
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                return_all_scores=True
            )
            
            # Initialize similarity model
            self.similarity_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            logger.info("Analytics models initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing models: {e}")
    
    def analyze_ranking_velocity(self, app_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze ranking velocity and detect fast climbers"""
        try:
            df = pd.DataFrame(app_data)
            
            if df.empty or 'current_rank' not in df.columns:
                return {'error': 'Invalid app data'}
            
            # Calculate ranking velocity
            df['rank_change'] = df['previous_rank'] - df['current_rank']
            df['velocity_score'] = df['rank_change'] / df['previous_rank'] * 100
            
            # Identify fast climbers (top 10% velocity)
            velocity_threshold = df['velocity_score'].quantile(0.9)
            fast_climbers = df[df['velocity_score'] >= velocity_threshold]
            
            # Identify sudden drops
            drop_threshold = df['velocity_score'].quantile(0.1)
            sudden_drops = df[df['velocity_score'] <= drop_threshold]
            
            analysis = {
                'total_apps': len(df),
                'fast_climbers': fast_climbers[['title', 'current_rank', 'previous_rank', 'velocity_score']].to_dict('records'),
                'sudden_drops': sudden_drops[['title', 'current_rank', 'previous_rank', 'velocity_score']].to_dict('records'),
                'average_velocity': float(df['velocity_score'].mean()),
                'velocity_std': float(df['velocity_score'].std())
            }
            
            logger.info(f"Ranking velocity analysis completed for {len(df)} apps")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing ranking velocity: {e}")
            return {'error': str(e)}
    
    def analyze_review_sentiment(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sentiment of app reviews"""
        try:
            if not reviews or not self.sentiment_analyzer:
                return {'error': 'No reviews or sentiment analyzer not available'}
            
            sentiments = []
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            
            for review in reviews:
                review_text = review.get('review_text', '')
                if not review_text:
                    continue
                
                # Analyze sentiment
                result = self.sentiment_analyzer(review_text[:512])  # Limit text length
                
                # Get the highest scoring sentiment
                best_sentiment = max(result[0], key=lambda x: x['score'])
                sentiment_label = best_sentiment['label']
                sentiment_score = best_sentiment['score']
                
                sentiments.append({
                    'review_id': review.get('id', ''),
                    'sentiment_label': sentiment_label,
                    'sentiment_score': sentiment_score,
                    'rating': review.get('rating', 0)
                })
                
                # Count sentiments
                if 'POSITIVE' in sentiment_label.upper():
                    positive_count += 1
                elif 'NEGATIVE' in sentiment_label.upper():
                    negative_count += 1
                else:
                    neutral_count += 1
            
            total_reviews = len(sentiments)
            if total_reviews == 0:
                return {'error': 'No valid reviews to analyze'}
            
            analysis = {
                'total_reviews_analyzed': total_reviews,
                'positive_percentage': (positive_count / total_reviews) * 100,
                'negative_percentage': (negative_count / total_reviews) * 100,
                'neutral_percentage': (neutral_count / total_reviews) * 100,
                'average_sentiment_score': np.mean([s['sentiment_score'] for s in sentiments]),
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
        """Analyze monetization patterns and IAP strategies"""
        try:
            df = pd.DataFrame(apps)
            
            if df.empty:
                return {'error': 'No app data provided'}
            
            # Categorize apps by pricing model
            free_apps = df[df['price'] == 0]
            paid_apps = df[df['price'] > 0]
            
            # Analyze IAP patterns (mock implementation)
            iap_analysis = {
                'apps_with_iap': len([app for app in apps if app.get('iap_products')]),
                'average_iap_count': np.mean([len(app.get('iap_products', [])) for app in apps]),
                'common_iap_tiers': ['$0.99', '$2.99', '$4.99', '$9.99', '$19.99']  # Mock data
            }
            
            analysis = {
                'total_apps': len(df),
                'free_apps': len(free_apps),
                'paid_apps': len(paid_apps),
                'average_price': float(paid_apps['price'].mean()) if not paid_apps.empty else 0,
                'price_distribution': {
                    'under_1': len(paid_apps[paid_apps['price'] < 1]),
                    '1_to_5': len(paid_apps[(paid_apps['price'] >= 1) & (paid_apps['price'] < 5)]),
                    '5_to_10': len(paid_apps[(paid_apps['price'] >= 5) & (paid_apps['price'] < 10)]),
                    'over_10': len(paid_apps[paid_apps['price'] >= 10])
                },
                'iap_analysis': iap_analysis
            }
            
            logger.info(f"Monetization analysis completed for {len(df)} apps")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing monetization patterns: {e}")
            return {'error': str(e)}
    
    def detect_clones(self, apps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect potential app clones using various similarity metrics"""
        try:
            clones = []
            
            for i, app1 in enumerate(apps):
                for j, app2 in enumerate(apps[i+1:], i+1):
                    similarity_scores = {}
                    
                    # Title similarity
                    title_sim = self._calculate_text_similarity(
                        app1.get('title', ''), app2.get('title', '')
                    )
                    similarity_scores['title'] = title_sim
                    
                    # Description similarity
                    desc_sim = self._calculate_text_similarity(
                        app1.get('description', ''), app2.get('description', '')
                    )
                    similarity_scores['description'] = desc_sim
                    
                    # Icon similarity (mock implementation)
                    icon_sim = self._calculate_icon_similarity(
                        app1.get('icon_url', ''), app2.get('icon_url', '')
                    )
                    similarity_scores['icon'] = icon_sim
                    
                    # Calculate overall similarity
                    overall_similarity = (
                        title_sim * 0.4 + 
                        desc_sim * 0.3 + 
                        icon_sim * 0.3
                    )
                    
                    # Consider as potential clone if similarity is high
                    if overall_similarity > 0.7:
                        clones.append({
                            'app1_id': app1.get('app_store_id', ''),
                            'app1_title': app1.get('title', ''),
                            'app2_id': app2.get('app_store_id', ''),
                            'app2_title': app2.get('title', ''),
                            'overall_similarity': overall_similarity,
                            'similarity_breakdown': similarity_scores,
                            'detection_type': 'multi_factor'
                        })
            
            logger.info(f"Clone detection completed, found {len(clones)} potential clones")
            return clones
            
        except Exception as e:
            logger.error(f"Error detecting clones: {e}")
            return []
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using sentence transformers"""
        try:
            if not text1 or not text2 or not self.similarity_model:
                return 0.0
            
            embeddings = self.similarity_model.encode([text1, text2])
            similarity = np.dot(embeddings[0], embeddings[1]) / (
                np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
            )
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating text similarity: {e}")
            return 0.0
    
    def _calculate_icon_similarity(self, icon_url1: str, icon_url2: str) -> float:
        """Calculate icon similarity using image processing"""
        try:
            if not icon_url1 or not icon_url2:
                return 0.0
            
            # Mock implementation - in production, use actual image comparison
            # This would involve:
            # 1. Download images
            # 2. Extract features using CLIP or OpenCV
            # 3. Calculate similarity
            
            # For now, return a random similarity score
            import random
            return random.uniform(0.0, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating icon similarity: {e}")
            return 0.0
    
    def analyze_seasonal_trends(self, apps: List[Dict[str, Any]], 
                              events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze seasonal trends and event correlations"""
        try:
            current_date = datetime.now()
            
            # Group apps by category and analyze trends
            category_trends = {}
            
            df = pd.DataFrame(apps)
            if not df.empty and 'category' in df.columns:
                for category in df['category'].unique():
                    category_apps = df[df['category'] == category]
                    
                    # Calculate trend metrics
                    avg_velocity = category_apps['rank_velocity'].mean() if 'rank_velocity' in category_apps.columns else 0
                    app_count = len(category_apps)
                    
                    category_trends[category] = {
                        'app_count': app_count,
                        'average_velocity': float(avg_velocity),
                        'trending_score': self._calculate_category_trend_score(category_apps)
                    }
            
            # Analyze upcoming events impact
            upcoming_events = [
                event for event in events 
                if event.get('start_date', current_date) >= current_date
            ]
            
            event_correlations = []
            for event in upcoming_events[:10]:  # Limit to next 10 events
                correlation = self._calculate_event_app_correlation(event, apps)
                if correlation['relevance_score'] > 0.3:
                    event_correlations.append(correlation)
            
            analysis = {
                'category_trends': category_trends,
                'seasonal_insights': self._generate_seasonal_insights(current_date),
                'event_correlations': event_correlations,
                'trending_categories': sorted(
                    category_trends.items(), 
                    key=lambda x: x[1]['trending_score'], 
                    reverse=True
                )[:5]
            }
            
            logger.info("Seasonal trend analysis completed")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing seasonal trends: {e}")
            return {'error': str(e)}
    
    def _calculate_category_trend_score(self, category_apps: pd.DataFrame) -> float:
        """Calculate trending score for a category"""
        try:
            if category_apps.empty:
                return 0.0
            
            # Consider multiple factors
            velocity_score = category_apps['rank_velocity'].mean() if 'rank_velocity' in category_apps.columns else 0
            review_score = category_apps['review_count'].mean() if 'review_count' in category_apps.columns else 0
            rating_score = category_apps['rating'].mean() if 'rating' in category_apps.columns else 0
            
            # Normalize and combine scores
            trend_score = (
                min(velocity_score / 10, 10) * 0.4 +
                min(review_score / 1000, 10) * 0.3 +
                rating_score * 2 * 0.3
            )
            
            return min(trend_score, 10.0)
            
        except Exception as e:
            logger.error(f"Error calculating category trend score: {e}")
            return 0.0
    
    def _calculate_event_app_correlation(self, event: Dict[str, Any], 
                                       apps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate correlation between an event and apps"""
        try:
            event_keywords = self._extract_event_keywords(event)
            relevant_apps = []
            
            for app in apps:
                app_keywords = self._extract_app_keywords(app)
                
                # Calculate keyword overlap
                common_keywords = set(event_keywords) & set(app_keywords)
                relevance_score = len(common_keywords) / max(len(event_keywords), 1)
                
                if relevance_score > 0.2:
                    relevant_apps.append({
                        'app_id': app.get('app_store_id', ''),
                        'title': app.get('title', ''),
                        'relevance_score': relevance_score,
                        'matching_keywords': list(common_keywords)
                    })
            
            return {
                'event_name': event.get('name', ''),
                'event_date': event.get('start_date', ''),
                'relevant_apps_count': len(relevant_apps),
                'relevance_score': np.mean([app['relevance_score'] for app in relevant_apps]) if relevant_apps else 0,
                'top_relevant_apps': sorted(relevant_apps, key=lambda x: x['relevance_score'], reverse=True)[:5]
            }
            
        except Exception as e:
            logger.error(f"Error calculating event-app correlation: {e}")
            return {'relevance_score': 0}
    
    def _extract_event_keywords(self, event: Dict[str, Any]) -> List[str]:
        """Extract keywords from event data"""
        keywords = []
        
        text = f"{event.get('name', '')} {event.get('description', '')}"
        
        # Simple keyword extraction
        common_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        words = [word.lower().strip('.,!?()[]{}":;') for word in text.split()]
        keywords = [word for word in words if len(word) > 2 and word not in common_words]
        
        # Add tags and event type
        if event.get('tags'):
            keywords.extend(event['tags'])
        if event.get('event_type'):
            keywords.append(event['event_type'])
        
        return list(set(keywords))
    
    def _extract_app_keywords(self, app: Dict[str, Any]) -> List[str]:
        """Extract keywords from app data"""
        keywords = []
        
        text = f"{app.get('title', '')} {app.get('description', '')} {app.get('category', '')}"
        
        common_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'app', 'game']
        words = [word.lower().strip('.,!?()[]{}":;') for word in text.split()]
        keywords = [word for word in words if len(word) > 2 and word not in common_words]
        
        if app.get('genres'):
            keywords.extend([genre.lower() for genre in app['genres']])
        
        return list(set(keywords))
    
    def _generate_seasonal_insights(self, current_date: datetime) -> List[str]:
        """Generate seasonal insights based on current date"""
        insights = []
        month = current_date.month
        
        seasonal_insights = {
            1: ["New Year fitness apps trending", "Resolution-based productivity apps popular"],
            2: ["Valentine's Day dating apps surge", "Photo editing apps for romantic content"],
            3: ["Spring cleaning organization apps", "Outdoor activity apps gaining traction"],
            4: ["Tax preparation apps peak", "Easter-themed games popular"],
            5: ["Mother's Day gift apps trending", "Spring fashion apps popular"],
            6: ["Father's Day and graduation apps", "Summer vacation planning apps"],
            7: ["Summer fitness and beach apps", "Travel and outdoor recreation apps"],
            8: ["Back-to-school apps surge", "Student productivity tools popular"],
            9: ["Fall fashion and home decor apps", "Fitness apps for fall routines"],
            10: ["Halloween-themed apps and games", "Horror entertainment apps trending"],
            11: ["Black Friday shopping apps", "Thanksgiving recipe and planning apps"],
            12: ["Holiday shopping and gift apps", "Christmas-themed entertainment apps"]
        }
        
        insights.extend(seasonal_insights.get(month, []))
        
        return insights