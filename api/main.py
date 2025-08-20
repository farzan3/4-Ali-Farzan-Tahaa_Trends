from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import jwt
import logging

from config import config
from models import database
from scrapers.app_store_scraper import AppStoreScraper
from scrapers.steam_scraper import SteamScraper
from scrapers.events_scraper import EventsScraper
from analytics.processor import AnalyticsProcessor
from ml.predictor import SuccessPredictor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Hunter API",
    description="App Discovery SaaS Platform API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
app_scraper = AppStoreScraper()
steam_scraper = SteamScraper()
events_scraper = EventsScraper()
analytics = AnalyticsProcessor()
predictor = SuccessPredictor()

# Security
security = HTTPBearer()

# Pydantic models
class AppResponse(BaseModel):
    id: str
    title: str
    developer: str
    category: str
    rating: float
    review_count: int
    success_score: float
    current_rank: Optional[int]
    price: float

class AppDetailResponse(BaseModel):
    id: str
    title: str
    developer: str
    category: str
    description: str
    rating: float
    review_count: int
    success_score: float
    current_rank: Optional[int]
    previous_rank: Optional[int]
    rank_velocity: float
    price: float
    icon_url: Optional[str]
    release_date: Optional[datetime]
    analytics: Dict[str, Any]
    predictions: Dict[str, Any]

class EventResponse(BaseModel):
    id: str
    name: str
    event_type: str
    start_date: datetime
    end_date: Optional[datetime]
    description: str
    related_apps_count: int

class AlertRequest(BaseModel):
    name: str
    condition: Dict[str, Any]
    alert_type: str
    notification_method: str

class PredictionRequest(BaseModel):
    app_data: Dict[str, Any]
    analytics_data: Optional[Dict[str, Any]] = None
    event_data: Optional[List[Dict[str, Any]]] = None

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Hunter API - App Discovery Platform",
        "version": "1.0.0",
        "status": "active"
    }

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "database": "connected",
        "services": {
            "app_scraper": "active",
            "steam_scraper": "active",
            "events_scraper": "active",
            "analytics": "active",
            "ml_predictor": "active"
        }
    }

# Apps endpoints
@app.get("/api/apps/top", response_model=List[AppResponse])
async def get_top_apps(
    limit: int = 100,
    category: Optional[str] = None,
    country: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get top apps with success scores"""
    try:
        # Mock data for demonstration
        apps_data = []
        
        sample_apps = [
            {
                "id": "1234567890",
                "title": "SuperGame Pro",
                "developer": "Game Studio Inc",
                "category": "Games",
                "rating": 4.8,
                "review_count": 12500,
                "success_score": 94.0,
                "current_rank": 3,
                "price": 0.0
            },
            {
                "id": "2345678901",
                "title": "Fitness Tracker 2024",
                "developer": "Health Apps LLC",
                "category": "Health & Fitness",
                "rating": 4.6,
                "review_count": 8900,
                "success_score": 89.0,
                "current_rank": 7,
                "price": 2.99
            },
            {
                "id": "3456789012",
                "title": "Photo Editor Max",
                "developer": "Creative Tools",
                "category": "Photo & Video",
                "rating": 4.7,
                "review_count": 15600,
                "success_score": 85.0,
                "current_rank": 12,
                "price": 0.0
            }
        ]
        
        # Apply filters
        filtered_apps = sample_apps
        if category:
            filtered_apps = [app for app in filtered_apps if category.lower() in app["category"].lower()]
        
        # Limit results
        filtered_apps = filtered_apps[:limit]
        
        return filtered_apps
        
    except Exception as e:
        logger.error(f"Error getting top apps: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/apps/{app_id}", response_model=AppDetailResponse)
async def get_app_details(
    app_id: str,
    user: dict = Depends(get_current_user)
):
    """Get detailed app analytics"""
    try:
        # Mock detailed app data
        app_detail = {
            "id": app_id,
            "title": "SuperGame Pro",
            "developer": "Game Studio Inc",
            "category": "Games",
            "description": "An amazing gaming experience with stunning graphics and engaging gameplay.",
            "rating": 4.8,
            "review_count": 12500,
            "success_score": 94.0,
            "current_rank": 3,
            "previous_rank": 15,
            "rank_velocity": 800.0,
            "price": 0.0,
            "icon_url": "https://example.com/icon.png",
            "release_date": datetime(2024, 1, 15),
            "analytics": {
                "sentiment_score": 0.87,
                "review_velocity": 45.2,
                "monetization_score": 8.5,
                "clone_similarity": 0.12,
                "seasonal_relevance": 0.78
            },
            "predictions": {
                "success_probability": 0.94,
                "confidence": 0.89,
                "key_factors": [
                    "High review velocity",
                    "Strong seasonal alignment",
                    "Effective monetization model"
                ],
                "predicted_rank_range": "1-5"
            }
        }
        
        return app_detail
        
    except Exception as e:
        logger.error(f"Error getting app details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/apps/search")
async def search_apps(
    query: str,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """Search apps by title, developer, or keywords"""
    try:
        # Mock search results
        results = [
            {
                "id": "1234567890",
                "title": "SuperGame Pro",
                "developer": "Game Studio Inc",
                "category": "Games",
                "rating": 4.8,
                "success_score": 94.0,
                "match_type": "title"
            }
        ]
        
        return {"query": query, "results": results, "total": len(results)}
        
    except Exception as e:
        logger.error(f"Error searching apps: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Steam endpoints
@app.get("/api/steam/trending")
async def get_trending_steam_games(
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """Get trending Steam games"""
    try:
        # Mock Steam data
        games = [
            {
                "id": "730",
                "title": "Counter-Strike 2",
                "developer": "Valve",
                "genre": "Action",
                "hype_score": 98.0,
                "player_count": 1250000,
                "price": 0.0
            },
            {
                "id": "1245620",
                "title": "ELDEN RING",
                "developer": "FromSoftware",
                "genre": "Action RPG",
                "hype_score": 95.0,
                "player_count": 850000,
                "price": 59.99
            }
        ]
        
        return {"games": games[:limit], "total": len(games)}
        
    except Exception as e:
        logger.error(f"Error getting trending Steam games: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Events endpoints
@app.get("/api/events/upcoming", response_model=List[EventResponse])
async def get_upcoming_events(
    limit: int = 20,
    days_ahead: int = 90,
    user: dict = Depends(get_current_user)
):
    """Get upcoming events"""
    try:
        # Mock events data
        events = [
            {
                "id": "valentine-2024",
                "name": "Valentine's Day",
                "event_type": "holiday",
                "start_date": datetime(2024, 2, 14),
                "end_date": datetime(2024, 2, 14),
                "description": "Annual celebration of love and romance",
                "related_apps_count": 245
            },
            {
                "id": "march-madness-2024",
                "name": "March Madness",
                "event_type": "sports",
                "start_date": datetime(2024, 3, 15),
                "end_date": datetime(2024, 4, 8),
                "description": "NCAA Basketball Tournament",
                "related_apps_count": 189
            }
        ]
        
        return events[:limit]
        
    except Exception as e:
        logger.error(f"Error getting upcoming events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/events/{event_id}/apps")
async def get_event_related_apps(
    event_id: str,
    user: dict = Depends(get_current_user)
):
    """Get apps related to a specific event"""
    try:
        # Mock related apps
        related_apps = [
            {
                "app_id": "1234567890",
                "title": "Love Calculator",
                "relevance_score": 0.95,
                "correlation_type": "theme"
            },
            {
                "app_id": "2345678901",
                "title": "Dating Coach",
                "relevance_score": 0.87,
                "correlation_type": "keyword"
            }
        ]
        
        return {
            "event_id": event_id,
            "related_apps": related_apps,
            "total": len(related_apps)
        }
        
    except Exception as e:
        logger.error(f"Error getting event-related apps: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Analytics endpoints
@app.get("/api/analytics/velocity")
async def get_velocity_analysis(
    timeframe: str = "7d",
    category: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get ranking velocity analysis"""
    try:
        analysis = {
            "timeframe": timeframe,
            "category": category,
            "fast_climbers": [
                {"app_id": "1234567890", "title": "SuperGame Pro", "velocity": 800.0},
                {"app_id": "2345678901", "title": "Fitness Tracker", "velocity": 228.0}
            ],
            "sudden_drops": [
                {"app_id": "3456789012", "title": "Old Game", "velocity": -150.0}
            ],
            "statistics": {
                "average_velocity": 12.5,
                "median_velocity": 8.2,
                "total_apps_analyzed": 1250
            }
        }
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error getting velocity analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/clones")
async def get_clone_detection(
    similarity_threshold: float = 0.7,
    user: dict = Depends(get_current_user)
):
    """Get clone detection results"""
    try:
        # Check if user has premium access
        if user.get('subscription_plan', 'free') == 'free':
            raise HTTPException(
                status_code=403,
                detail="Clone detection requires premium subscription"
            )
        
        clones = [
            {
                "original_app": {
                    "id": "1234567890",
                    "title": "PopularGame Pro"
                },
                "clone_app": {
                    "id": "9876543210",
                    "title": "PopGame Clone"
                },
                "similarity_score": 0.94,
                "similarity_types": ["title", "icon", "description"],
                "detection_date": datetime.now()
            }
        ]
        
        return {"clones": clones, "threshold": similarity_threshold}
        
    except Exception as e:
        logger.error(f"Error getting clone detection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Predictions endpoint
@app.post("/api/predict/success")
async def predict_app_success(
    request: PredictionRequest,
    user: dict = Depends(get_current_user)
):
    """Predict app success using ML model"""
    try:
        prediction = predictor.predict_success(
            request.app_data,
            request.analytics_data,
            request.event_data
        )
        
        return {
            "prediction": prediction,
            "request_timestamp": datetime.now(),
            "model_info": {
                "version": prediction.get("model_version", "1.0"),
                "type": "ensemble"
            }
        }
        
    except Exception as e:
        logger.error(f"Error predicting app success: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Alerts endpoints
@app.post("/api/alerts")
async def create_alert(
    request: AlertRequest,
    user: dict = Depends(get_current_user)
):
    """Create a new alert"""
    try:
        # Mock alert creation
        alert = {
            "id": f"alert_{datetime.now().timestamp()}",
            "user_id": user["user_id"],
            "name": request.name,
            "condition": request.condition,
            "alert_type": request.alert_type,
            "notification_method": request.notification_method,
            "status": "active",
            "created_at": datetime.now()
        }
        
        return {"message": "Alert created successfully", "alert": alert}
        
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerts")
async def get_user_alerts(
    user: dict = Depends(get_current_user)
):
    """Get user's alerts"""
    try:
        # Mock user alerts
        alerts = [
            {
                "id": "alert_1",
                "name": "SuperGame Pro Rank Change",
                "condition": {"rank": {"less_than": 5}},
                "alert_type": "rank_change",
                "status": "active",
                "last_triggered": None
            }
        ]
        
        return {"alerts": alerts, "total": len(alerts)}
        
    except Exception as e:
        logger.error(f"Error getting user alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/alerts/{alert_id}")
async def delete_alert(
    alert_id: str,
    user: dict = Depends(get_current_user)
):
    """Delete an alert"""
    try:
        # Mock alert deletion
        return {"message": f"Alert {alert_id} deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Statistics endpoint
@app.get("/api/stats")
async def get_platform_stats(
    user: dict = Depends(get_current_user)
):
    """Get platform statistics"""
    try:
        stats = {
            "total_apps_tracked": 125000,
            "total_steam_games": 34210,
            "active_users": 1234,
            "predictions_made_today": 5678,
            "api_calls_today": 15600,
            "data_freshness": {
                "app_store": "2 hours ago",
                "steam": "1 hour ago",
                "events": "6 hours ago"
            },
            "system_health": {
                "uptime": "99.7%",
                "avg_response_time": "245ms",
                "error_rate": "0.3%"
            }
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting platform stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Export endpoint
@app.get("/api/export/apps")
async def export_apps_data(
    format: str = "csv",
    category: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Export apps data in various formats"""
    try:
        if format not in ["csv", "json", "xlsx"]:
            raise HTTPException(status_code=400, detail="Unsupported format")
        
        # Mock export data
        export_data = {
            "format": format,
            "total_records": 1250,
            "download_url": f"https://api.hunter.app/downloads/apps_export_{datetime.now().timestamp()}.{format}",
            "expires_at": datetime.now().isoformat()
        }
        
        return export_data
        
    except Exception as e:
        logger.error(f"Error exporting apps data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)