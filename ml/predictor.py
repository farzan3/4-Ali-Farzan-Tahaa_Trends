import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, mean_squared_error
import joblib
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SuccessPredictor:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_importance = {}
        self.model_version = "1.0"
        self.is_trained = False
        
    def extract_features(self, app_data: Dict[str, Any], 
                        analytics_data: Optional[Dict[str, Any]] = None,
                        event_data: Optional[List[Dict[str, Any]]] = None) -> np.ndarray:
        """Extract features for prediction from app data"""
        try:
            features = {}
            
            # Basic app features
            features['rating'] = float(app_data.get('rating', 0))
            features['review_count'] = int(app_data.get('review_count', 0))
            features['price'] = float(app_data.get('price', 0))
            features['is_free'] = 1 if features['price'] == 0 else 0
            
            # Release timing features
            release_date = app_data.get('release_date')
            if release_date:
                if isinstance(release_date, str):
                    release_date = datetime.fromisoformat(release_date.replace('Z', '+00:00'))
                
                days_since_release = (datetime.now() - release_date).days
                features['days_since_release'] = days_since_release
                features['is_new_release'] = 1 if days_since_release < 30 else 0
            else:
                features['days_since_release'] = 0
                features['is_new_release'] = 0
            
            # Category features (encoded)
            category = app_data.get('category', 'unknown')
            features['category_games'] = 1 if 'game' in category.lower() else 0
            features['category_entertainment'] = 1 if 'entertainment' in category.lower() else 0
            features['category_utility'] = 1 if 'util' in category.lower() else 0
            
            # Analytics-based features
            if analytics_data:
                features['rank_velocity'] = float(analytics_data.get('rank_velocity', 0))
                features['sentiment_score'] = float(analytics_data.get('sentiment_score', 0.5))
                features['clone_similarity'] = float(analytics_data.get('clone_similarity', 0))
            else:
                features['rank_velocity'] = 0
                features['sentiment_score'] = 0.5
                features['clone_similarity'] = 0
            
            # Event correlation features
            if event_data:
                features['event_correlation'] = self._calculate_event_correlation_score(
                    app_data, event_data
                )
            else:
                features['event_correlation'] = 0
            
            # Monetization features
            features['has_iap'] = 1 if app_data.get('iap_products') else 0
            features['iap_count'] = len(app_data.get('iap_products', []))
            
            # Developer features
            developer = app_data.get('developer', '')
            features['developer_experience'] = self._estimate_developer_experience(developer)
            
            # Market timing features
            features['seasonal_score'] = self._calculate_seasonal_score(
                datetime.now(), app_data.get('category', '')
            )
            
            # Convert to numpy array
            feature_vector = np.array(list(features.values())).reshape(1, -1)
            
            return feature_vector
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            # Return zero vector as fallback
            return np.zeros((1, 15))
    
    def calculate_weighted_score(self, app_data: Dict[str, Any],
                               analytics_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Calculate success score using weighted rules (MVP approach)"""
        try:
            score = 0.0
            breakdown = {}
            
            # Rating component (0-25 points)
            rating = float(app_data.get('rating', 0))
            rating_score = min((rating / 5.0) * 25, 25)
            score += rating_score
            breakdown['rating'] = rating_score
            
            # Review velocity component (0-20 points)
            review_count = int(app_data.get('review_count', 0))
            review_velocity_score = min(np.log10(review_count + 1) * 4, 20)
            score += review_velocity_score
            breakdown['review_velocity'] = review_velocity_score
            
            # Ranking velocity component (0-20 points)
            if analytics_data and 'rank_velocity' in analytics_data:
                rank_velocity = float(analytics_data['rank_velocity'])
                rank_velocity_score = min(max(rank_velocity, 0) / 50 * 20, 20)
                score += rank_velocity_score
                breakdown['rank_velocity'] = rank_velocity_score
            else:
                breakdown['rank_velocity'] = 0
            
            # Sentiment component (0-15 points)
            if analytics_data and 'sentiment_score' in analytics_data:
                sentiment = float(analytics_data['sentiment_score'])
                sentiment_score = sentiment * 15
                score += sentiment_score
                breakdown['sentiment'] = sentiment_score
            else:
                breakdown['sentiment'] = 7.5  # Neutral
                score += 7.5
            
            # Monetization strategy component (0-10 points)
            price = float(app_data.get('price', 0))
            has_iap = bool(app_data.get('iap_products'))
            
            if price == 0 and has_iap:
                monetization_score = 10  # Freemium model
            elif price > 0 and not has_iap:
                monetization_score = 8   # Premium model
            elif price == 0 and not has_iap:
                monetization_score = 5   # Free with ads
            else:
                monetization_score = 6   # Paid with IAP
            
            score += monetization_score
            breakdown['monetization'] = monetization_score
            
            # New release bonus (0-10 points)
            release_date = app_data.get('release_date')
            if release_date:
                if isinstance(release_date, str):
                    release_date = datetime.fromisoformat(release_date.replace('Z', '+00:00'))
                
                days_since_release = (datetime.now() - release_date).days
                if days_since_release < 7:
                    new_release_score = 10
                elif days_since_release < 30:
                    new_release_score = 5
                elif days_since_release < 90:
                    new_release_score = 2
                else:
                    new_release_score = 0
            else:
                new_release_score = 0
            
            score += new_release_score
            breakdown['new_release'] = new_release_score
            
            # Normalize to 0-100 scale
            final_score = min(score, 100)
            
            return {
                'success_score': final_score,
                'breakdown': breakdown,
                'model_version': 'weighted_v1.0',
                'confidence': self._calculate_confidence(breakdown),
                'prediction_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating weighted score: {e}")
            return {
                'success_score': 0.0,
                'breakdown': {},
                'model_version': 'weighted_v1.0',
                'confidence': 0.0,
                'prediction_date': datetime.now().isoformat()
            }
    
    def train_ml_model(self, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Train ML model on historical data"""
        try:
            if len(training_data) < 100:
                return {'error': 'Insufficient training data (minimum 100 samples required)'}
            
            # Prepare training data
            X = []
            y = []
            
            for data in training_data:
                features = self.extract_features(
                    data['app_data'], 
                    data.get('analytics_data'),
                    data.get('event_data')
                ).flatten()
                
                X.append(features)
                y.append(data['success_label'])  # 0 or 1 for binary classification
            
            X = np.array(X)
            y = np.array(y)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            )
            
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            train_pred = self.model.predict(X_train_scaled)
            test_pred = self.model.predict(X_test_scaled)
            
            # Get feature importance
            feature_names = [
                'rating', 'review_count', 'price', 'is_free', 'days_since_release',
                'is_new_release', 'category_games', 'category_entertainment',
                'category_utility', 'rank_velocity', 'sentiment_score',
                'clone_similarity', 'event_correlation', 'has_iap', 'iap_count'
            ]
            
            self.feature_importance = dict(zip(
                feature_names, self.model.feature_importances_
            ))
            
            self.is_trained = True
            
            metrics = {
                'train_accuracy': accuracy_score(y_train, train_pred),
                'test_accuracy': accuracy_score(y_test, test_pred),
                'train_precision': precision_score(y_train, train_pred),
                'test_precision': precision_score(y_test, test_pred),
                'train_recall': recall_score(y_train, train_pred),
                'test_recall': recall_score(y_test, test_pred),
                'feature_importance': self.feature_importance,
                'training_samples': len(training_data),
                'model_version': self.model_version
            }
            
            logger.info(f"ML model trained successfully with {len(training_data)} samples")
            logger.info(f"Test accuracy: {metrics['test_accuracy']:.3f}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error training ML model: {e}")
            return {'error': str(e)}
    
    def predict_success(self, app_data: Dict[str, Any],
                       analytics_data: Optional[Dict[str, Any]] = None,
                       event_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Predict success probability using trained ML model"""
        try:
            if not self.is_trained or self.model is None:
                # Fall back to weighted scoring
                return self.calculate_weighted_score(app_data, analytics_data)
            
            # Extract features
            features = self.extract_features(app_data, analytics_data, event_data)
            features_scaled = self.scaler.transform(features)
            
            # Predict
            probability = self.model.predict_proba(features_scaled)[0][1]  # Probability of success
            prediction = self.model.predict(features_scaled)[0]
            
            # Convert probability to 0-100 score
            success_score = probability * 100
            
            return {
                'success_score': float(success_score),
                'success_probability': float(probability),
                'binary_prediction': int(prediction),
                'model_version': self.model_version,
                'confidence': float(probability if prediction == 1 else 1 - probability),
                'feature_importance': self.feature_importance,
                'prediction_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error predicting success: {e}")
            return self.calculate_weighted_score(app_data, analytics_data)
    
    def _calculate_event_correlation_score(self, app_data: Dict[str, Any],
                                         event_data: List[Dict[str, Any]]) -> float:
        """Calculate correlation score with upcoming events"""
        try:
            if not event_data:
                return 0.0
            
            app_keywords = self._extract_app_keywords(app_data)
            max_correlation = 0.0
            
            current_date = datetime.now()
            
            for event in event_data:
                event_date = event.get('start_date', current_date)
                if isinstance(event_date, str):
                    event_date = datetime.fromisoformat(event_date.replace('Z', '+00:00'))
                
                # Only consider events in the next 90 days
                if (event_date - current_date).days > 90:
                    continue
                
                event_keywords = self._extract_event_keywords(event)
                
                # Calculate keyword overlap
                common_keywords = set(app_keywords) & set(event_keywords)
                correlation = len(common_keywords) / max(len(event_keywords), 1)
                
                # Weight by proximity to event
                days_to_event = (event_date - current_date).days
                proximity_weight = max(0, 1 - days_to_event / 90)
                
                weighted_correlation = correlation * proximity_weight
                max_correlation = max(max_correlation, weighted_correlation)
            
            return max_correlation
            
        except Exception as e:
            logger.error(f"Error calculating event correlation: {e}")
            return 0.0
    
    def _estimate_developer_experience(self, developer: str) -> float:
        """Estimate developer experience (mock implementation)"""
        # In production, this would analyze developer history
        # For now, return a score based on developer name length (very basic)
        if not developer:
            return 0.5
        
        # Mock scoring based on name characteristics
        score = min(len(developer) / 50, 1.0)
        
        # Bonus for known indicators
        if any(keyword in developer.lower() for keyword in ['games', 'studio', 'entertainment', 'inc']):
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_seasonal_score(self, current_date: datetime, category: str) -> float:
        """Calculate seasonal relevance score"""
        month = current_date.month
        
        seasonal_categories = {
            1: ['fitness', 'health', 'productivity'],  # January - New Year resolutions
            2: ['photo', 'social', 'dating'],          # February - Valentine's Day
            6: ['travel', 'photography', 'outdoor'],   # June - Summer
            9: ['education', 'productivity', 'books'], # September - Back to school
            10: ['games', 'entertainment', 'horror'],  # October - Halloween
            11: ['shopping', 'finance', 'deals'],      # November - Black Friday
            12: ['games', 'entertainment', 'photo']    # December - Holidays
        }
        
        relevant_categories = seasonal_categories.get(month, [])
        
        if any(cat in category.lower() for cat in relevant_categories):
            return 1.0
        
        return 0.5
    
    def _extract_app_keywords(self, app_data: Dict[str, Any]) -> List[str]:
        """Extract keywords from app data"""
        keywords = []
        
        text = f"{app_data.get('title', '')} {app_data.get('description', '')} {app_data.get('category', '')}"
        
        common_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'app', 'game']
        words = [word.lower().strip('.,!?()[]{}":;') for word in text.split()]
        keywords = [word for word in words if len(word) > 2 and word not in common_words]
        
        return list(set(keywords))
    
    def _extract_event_keywords(self, event: Dict[str, Any]) -> List[str]:
        """Extract keywords from event data"""
        keywords = []
        
        text = f"{event.get('name', '')} {event.get('description', '')}"
        
        common_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        words = [word.lower().strip('.,!?()[]{}":;') for word in text.split()]
        keywords = [word for word in words if len(word) > 2 and word not in common_words]
        
        if event.get('tags'):
            keywords.extend(event['tags'])
        
        return list(set(keywords))
    
    def _calculate_confidence(self, breakdown: Dict[str, float]) -> float:
        """Calculate prediction confidence based on available data"""
        # Higher confidence when we have more complete data
        data_completeness = len([v for v in breakdown.values() if v > 0]) / len(breakdown)
        
        # Higher confidence for extreme scores (very high or very low)
        total_score = sum(breakdown.values())
        score_extremeness = abs(total_score - 50) / 50
        
        confidence = (data_completeness * 0.7) + (score_extremeness * 0.3)
        
        return min(confidence, 1.0)
    
    def save_model(self, filepath: str) -> bool:
        """Save trained model to file"""
        try:
            if not self.is_trained:
                logger.warning("No trained model to save")
                return False
            
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_importance': self.feature_importance,
                'model_version': self.model_version,
                'is_trained': self.is_trained
            }
            
            joblib.dump(model_data, filepath)
            logger.info(f"Model saved to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False
    
    def load_model(self, filepath: str) -> bool:
        """Load trained model from file"""
        try:
            model_data = joblib.load(filepath)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_importance = model_data['feature_importance']
            self.model_version = model_data['model_version']
            self.is_trained = model_data['is_trained']
            
            logger.info(f"Model loaded from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False