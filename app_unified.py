import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, Any, List
import os

# Detect environment
IS_CLOUD = os.getenv('STREAMLIT_SHARING') or 'share.streamlit.io' in os.getenv('HOSTNAME', '')

# Configure Streamlit page
st.set_page_config(
    page_title="Hunter - App Discovery Platform",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Environment-specific imports and setup
if IS_CLOUD:
    # Cloud mode - lightweight dependencies only
    def simple_auth():
        """Simple authentication system for cloud deployment"""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        
        if not st.session_state.authenticated:
            st.title("🎯 Hunter - Login")
            
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login")
                
                if submitted:
                    if email == "admin@hunter.app" and password == "admin123":
                        st.session_state.authenticated = True
                        st.session_state.user = {
                            'email': email,
                            'subscription_plan': 'premium',
                            'role': 'admin'
                        }
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Use admin@hunter.app / admin123")
            
            st.info("Demo credentials: admin@hunter.app / admin123")
            return False
        
        return True
    
    def init_demo_data():
        """Initialize demo data for cloud"""
        if 'demo_data' not in st.session_state:
            st.session_state.demo_data = {
                'apps': [
                    {'title': 'SuperGame Pro', 'developer': 'GameStudio Inc', 'category': 'Games', 'current_rank': 3, 'rating': 4.8, 'review_count': 12500},
                    {'title': 'Fitness Tracker 2024', 'developer': 'HealthTech', 'category': 'Health & Fitness', 'current_rank': 7, 'rating': 4.6, 'review_count': 8900},
                    {'title': 'Photo Editor Max', 'developer': 'PhotoPro', 'category': 'Photography', 'current_rank': 12, 'rating': 4.5, 'review_count': 6700},
                    {'title': 'Learning Path', 'developer': 'EduTech', 'category': 'Education', 'current_rank': 18, 'rating': 4.7, 'review_count': 4300},
                    {'title': 'Social Connect', 'developer': 'SocialApp Inc', 'category': 'Social Networking', 'current_rank': 25, 'rating': 4.4, 'review_count': 15600}
                ],
                'steam_games': [
                    {'name': 'Cyberpunk 2078', 'genre': 'RPG', 'players': '125K', 'hype_score': 95, 'price': '$59.99'},
                    {'name': 'Fantasy RPG X', 'genre': 'RPG', 'players': '89K', 'hype_score': 88, 'price': '$29.99'},
                    {'name': 'Battle Arena Pro', 'genre': 'Action', 'players': '67K', 'hype_score': 82, 'price': '$19.99'}
                ],
                'events': [
                    {'name': 'Valentine\'s Day', 'start_date': '2024-02-14', 'event_type': 'Holiday', 'region': 'Global'},
                    {'name': 'March Madness', 'start_date': '2024-03-15', 'event_type': 'Sports', 'region': 'US'},
                    {'name': 'Easter', 'start_date': 'Upcoming', 'event_type': 'Holiday', 'region': 'Global'}
                ]
            }
    
    auth_function = simple_auth
    data_init = init_demo_data
    
else:
    # Local mode - full features with database
    try:
        from config import config
        from models import database, App, User, Event, SteamGame, Score
        from auth import auth_manager
        from dashboard_utils import get_database_stats, get_recent_apps, get_upcoming_events
        
        # Import enhanced scrapers
        try:
            from scrapers.enhanced_app_store_scraper import EnhancedAppStoreScraper as AppStoreScraper
            from scrapers.enhanced_steam_scraper import EnhancedSteamScraper as SteamScraper
            from scrapers.comprehensive_events_scraper import ComprehensiveEventsScraper as EventsScraper
        except ImportError:
            from scrapers.app_store_scraper import AppStoreScraper
            from scrapers.steam_scraper import SteamScraper
            from scrapers.events_scraper import EventsScraper
        
        # Import analytics
        try:
            from analytics.processor import AnalyticsProcessor
        except ImportError:
            from analytics.processor_simple import AnalyticsProcessor
        
        try:
            from ml.predictor import SuccessPredictor
        except ImportError:
            class SuccessPredictor:
                def __init__(self):
                    self.is_trained = False
                def calculate_weighted_score(self, app_data, analytics_data=None):
                    rating = float(app_data.get('rating', 0))
                    review_count = int(app_data.get('review_count', 0))
                    score = (rating / 5.0) * 50 + min(review_count / 1000, 50)
                    return {'success_score': min(score, 100), 'breakdown': {'rating': rating * 10, 'reviews': min(review_count / 100, 40)}}
        
        def local_auth():
            return auth_manager.require_auth()
        
        def local_data_init():
            pass  # Database already initialized
            
        auth_function = local_auth
        data_init = local_data_init
        
    except ImportError as e:
        st.error(f"Local dependencies not available: {e}")
        st.info("Falling back to cloud mode...")
        IS_CLOUD = True
        # Use cloud mode functions
        auth_function = simple_auth
        data_init = init_demo_data

class UnifiedHunterDashboard:
    def __init__(self):
        data_init()
        
        # Initialize session state
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'dashboard'
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = datetime.now()
        
        # Environment-specific initialization
        if not IS_CLOUD:
            try:
                self.app_scraper = AppStoreScraper()
                self.steam_scraper = SteamScraper()
                self.events_scraper = EventsScraper()
                self.analytics = AnalyticsProcessor()
                self.predictor = SuccessPredictor()
            except:
                pass  # Fallback handled in methods
    
    def run(self):
        """Main application entry point"""
        # Check authentication
        user = auth_function()
        if not user:
            return
        
        # Environment indicator
        if IS_CLOUD:
            st.sidebar.info("🌐 Running in Cloud Mode")
        else:
            st.sidebar.info("💻 Running in Local Mode")
        
        # Sidebar navigation
        self.render_sidebar(user)
        
        # Main content area
        page = st.session_state.get('current_page', 'dashboard')
        
        if page == 'dashboard':
            self.render_dashboard()
        elif page == 'apps':
            self.render_apps_page()
        elif page == 'steam':
            self.render_steam_page()
        elif page == 'events':
            self.render_events_page()
        elif page == 'analytics':
            self.render_analytics_page()
        elif page == 'alerts':
            self.render_alerts_page()
    
    def render_sidebar(self, user: Dict[str, Any]):
        """Render navigation sidebar"""
        with st.sidebar:
            st.title("🎯 Hunter")
            
            st.write(f"Welcome, {user.get('email', 'User')}")
            plan = user.get('subscription_plan', 'free').title()
            plan_emoji = "👑" if plan == "Premium" else "🆓"
            st.write(f"Plan: {plan_emoji} {plan}")
            
            # Navigation menu
            st.subheader("Navigation")
            
            pages = {
                'dashboard': '📊 Dashboard',
                'apps': '📱 App Store',
                'steam': '🎮 Steam Games',
                'events': '📅 Events',
                'analytics': '🔍 Premium Analytics',
                'alerts': '🔔 Alerts'
            }
            
            # Use radio buttons for navigation
            page_names = list(pages.values())
            page_keys = list(pages.keys())
            
            current_page = st.session_state.get('current_page', 'dashboard')
            current_index = page_keys.index(current_page) if current_page in page_keys else 0
            
            selected_index = st.radio(
                "Navigate to:",
                range(len(page_names)),
                format_func=lambda x: page_names[x],
                index=current_index,
                key="navigation"
            )
            
            if selected_index != current_index:
                st.session_state.current_page = page_keys[selected_index]
                st.rerun()
            
            st.divider()
            
            # Data refresh
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.session_state.last_refresh = datetime.now()
                st.success("Data refreshed!")
            
            st.caption(f"Last updated: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
            
            st.divider()
            
            # Logout
            if st.button("🚪 Logout", use_container_width=True):
                if IS_CLOUD:
                    st.session_state.authenticated = False
                else:
                    auth_manager.logout()
                st.rerun()
    
    def render_dashboard(self):
        """Render main dashboard"""
        st.title("🎯 Hunter - App Discovery Dashboard")
        
        # Get statistics based on environment
        if IS_CLOUD:
            stats = {
                'apps_count': len(st.session_state.demo_data['apps']),
                'steam_games_count': len(st.session_state.demo_data['steam_games']),
                'events_count': len(st.session_state.demo_data['events']),
                'alerts_count': 5
            }
        else:
            try:
                stats = get_database_stats()
            except:
                stats = {'apps_count': 0, 'steam_games_count': 0, 'events_count': 0, 'alerts_count': 0}
        
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Apps Tracked", f"{stats['apps_count']:,}", f"+{stats['apps_count']}")
        
        with col2:
            st.metric("Steam Games", f"{stats['steam_games_count']:,}", f"+{stats['steam_games_count']}")
        
        with col3:
            st.metric("Active Alerts", f"{stats['alerts_count']}", f"+{stats['alerts_count']}")
        
        with col4:
            trending_score = min(100, (stats['apps_count'] + stats['steam_games_count']) * 2)
            st.metric("Trending Score", f"{trending_score}%", "+Live")
        
        st.divider()
        
        # Main content columns
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🔥 Hottest Apps Right Now")
            self.render_trending_apps()
            
            st.subheader("📈 Chart Climbers")
            self.render_chart_climbers()
        
        with col2:
            st.subheader("🎭 Upcoming Events")
            self.render_upcoming_events()
            
            st.subheader("⚡ Quick Actions")
            self.render_quick_actions()
    
    def render_trending_apps(self):
        """Render trending apps table"""
        if IS_CLOUD:
            apps = st.session_state.demo_data['apps']
            trending_data = {
                'App Name': [app['title'] for app in apps],
                'Developer': [app['developer'] for app in apps],
                'Category': [app['category'] for app in apps],
                'Current Rank': [app['current_rank'] for app in apps],
                'Rating': [f"{app['rating']:.1f}" for app in apps],
                'Reviews': [f"{app['review_count']:,}" for app in apps]
            }
        else:
            try:
                apps = get_recent_apps(10)
                if apps:
                    trending_data = {
                        'App Name': [app['title'] for app in apps],
                        'Developer': [app['developer'] or 'Unknown' for app in apps],
                        'Category': [app['category'] or 'Unknown' for app in apps],
                        'Current Rank': [app['current_rank'] or 'N/A' for app in apps],
                        'Rating': [f"{app['rating']:.1f}" if app['rating'] else 'N/A' for app in apps],
                        'Reviews': [app['review_count'] or 0 for app in apps]
                    }
                else:
                    st.info("No apps found in database. Run the scraper to collect app data.")
                    return
            except:
                # Fallback to demo data
                trending_data = {
                    'App Name': ['Demo App 1', 'Demo App 2', 'Demo App 3'],
                    'Category': ['Games', 'Utilities', 'Entertainment'],
                    'Status': ['No real data', 'Run scraper', 'to populate']
                }
        
        df = pd.DataFrame(trending_data)
        st.dataframe(df, use_container_width=True)
    
    def render_chart_climbers(self):
        """Render chart showing ranking changes"""
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        
        fig = go.Figure()
        
        apps = ['SuperGame Pro', 'Fitness Tracker 2024', 'Photo Editor Max']
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        
        for i, app in enumerate(apps):
            rankings = np.random.randint(1, 100, len(dates))
            rankings = np.sort(rankings)[::-1]
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=rankings,
                mode='lines+markers',
                name=app,
                line=dict(color=colors[i], width=3),
                marker=dict(size=6)
            ))
        
        fig.update_layout(
            title="App Store Ranking Trends (Last 30 Days)",
            xaxis_title="Date",
            yaxis_title="Rank Position",
            yaxis=dict(autorange='reversed'),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_upcoming_events(self):
        """Render upcoming events list"""
        if IS_CLOUD:
            events = st.session_state.demo_data['events']
        else:
            try:
                events = get_upcoming_events(5)
            except:
                events = [
                    {"name": "Demo Event", "start_date": "Future", "event_type": "Demo", "region": "Demo"}
                ]
        
        for event in events:
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{event['name']}**")
                    date_str = event.get('start_date', 'TBD')[:10] if len(str(event.get('start_date', ''))) > 10 else event.get('start_date', 'TBD')
                    st.caption(f"{date_str} • {event.get('event_type', 'N/A')} • {event.get('region', 'N/A')}")
                with col2:
                    st.write("📅 Upcoming")
                st.divider()
    
    def render_quick_actions(self):
        """Render quick action buttons"""
        if st.button("🎯 Find Next Hit", use_container_width=True):
            mode = "Demo mode" if IS_CLOUD else "Local mode"
            st.info(f"Analyzing market trends... ({mode})")
        
        if st.button("📊 Generate Report", use_container_width=True):
            mode = "Demo mode" if IS_CLOUD else "Local mode"
            st.info(f"Preparing comprehensive report... ({mode})")
        
        if st.button("🔔 Set Alert", use_container_width=True):
            mode = "Demo mode" if IS_CLOUD else "Local mode"
            st.info(f"Opening alert configuration... ({mode})")
        
        if st.button("💾 Export Data", use_container_width=True):
            if IS_CLOUD:
                sample_data = pd.DataFrame(st.session_state.demo_data['apps'])
            else:
                sample_data = pd.DataFrame({
                    'App': ['SuperGame Pro', 'Fitness Tracker 2024'],
                    'Score': [94, 89],
                    'Rank': [3, 7]
                })
            
            csv = sample_data.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                "hunter_apps_export.csv",
                "text/csv"
            )
    
    def render_apps_page(self):
        """Render App Store analysis page"""
        st.title("📱 App Store Analysis")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_country = st.selectbox(
                "Country",
                ["All", "United States", "United Kingdom", "Germany", "Japan"]
            )
        
        with col2:
            selected_category = st.selectbox(
                "Category",
                ["All", "Games", "Entertainment", "Utilities", "Health & Fitness"]
            )
        
        with col3:
            time_range = st.selectbox(
                "Time Range",
                ["Last 24 Hours", "Last 7 Days", "Last 30 Days"]
            )
        
        # Main content tabs
        tab1, tab2, tab3 = st.tabs(["📈 Rankings", "💡 Predictions", "🔍 Deep Dive"])
        
        with tab1:
            st.subheader("Current Top Apps")
            
            if IS_CLOUD:
                apps_df = pd.DataFrame(st.session_state.demo_data['apps'])
            else:
                # Use real data or fallback
                try:
                    apps = get_recent_apps(20)
                    if apps:
                        apps_df = pd.DataFrame(apps)
                    else:
                        apps_df = pd.DataFrame([{'title': 'No data', 'category': 'Run scraper'}])
                except:
                    apps_df = pd.DataFrame([{'title': 'Error loading', 'category': 'Check database'}])
            
            st.dataframe(apps_df, use_container_width=True)
            
            # Category distribution
            if 'category' in apps_df.columns:
                categories = apps_df['category'].value_counts()
                fig = px.pie(values=categories.values, names=categories.index, title="App Distribution by Category")
                st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.subheader("🤖 AI Predictions")
            
            mode = "Demo" if IS_CLOUD else "Live"
            st.info(f"Running in {mode} mode")
            
            predictions = {
                'App Name': ['NewGame Alpha', 'Productivity Pro', 'Social Connect', 'Learning Path'],
                'Predicted Score': [92, 87, 83, 79],
                'Confidence': ['95%', '89%', '91%', '86%'],
                'Key Factors': [
                    'High review velocity, seasonal boost',
                    'Strong monetization model',
                    'Social media trend alignment',
                    'Educational event correlation'
                ]
            }
            
            df = pd.DataFrame(predictions)
            st.dataframe(df, use_container_width=True)
        
        with tab3:
            st.subheader("🔍 App Deep Dive")
            
            if IS_CLOUD:
                app_list = [app['title'] for app in st.session_state.demo_data['apps']]
            else:
                app_list = ["SuperGame Pro", "Fitness Tracker 2024", "Photo Editor Max"]
            
            selected_app = st.selectbox("Select App for Analysis", app_list)
            
            if selected_app:
                if IS_CLOUD:
                    app_data = next((app for app in st.session_state.demo_data['apps'] if app['title'] == selected_app), {})
                else:
                    app_data = {'title': selected_app, 'category': 'Games', 'rating': 4.8, 'review_count': 12500, 'current_rank': 3}
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.write(f"**{selected_app}**")
                    st.write(f"{app_data.get('category', 'Games')} • Free with IAP")
                    st.write(f"⭐ {app_data.get('rating', 4.8)} ({app_data.get('review_count', 12500):,} reviews)")
                
                with col2:
                    metrics_col1, metrics_col2 = st.columns(2)
                    with metrics_col1:
                        st.metric("Current Rank", f"#{app_data.get('current_rank', 3)}", "-2")
                        st.metric("Success Score", "94", "+7")
                    
                    with metrics_col2:
                        st.metric("Review Velocity", "+45%", "+12%")
                        st.metric("Revenue Estimate", "$125K", "+23%")
    
    def render_steam_page(self):
        """Render Steam games analysis page"""
        st.title("🎮 Steam Games Analysis")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Trending Steam Games")
            
            if IS_CLOUD:
                steam_df = pd.DataFrame(st.session_state.demo_data['steam_games'])
            else:
                # Mock Steam data for now
                steam_data = {
                    'Game': ['Cyberpunk 2078', 'Fantasy RPG X', 'Battle Arena Pro', 'Puzzle Quest', 'Racing Sim 24'],
                    'Genre': ['RPG', 'RPG', 'Action', 'Puzzle', 'Racing'],
                    'Players': ['125K', '89K', '67K', '45K', '38K'],
                    'Hype Score': [95, 88, 82, 76, 71],
                    'Price': ['$59.99', '$29.99', '$19.99', '$9.99', '$39.99']
                }
                steam_df = pd.DataFrame(steam_data)
            
            st.dataframe(steam_df, use_container_width=True)
        
        with col2:
            st.subheader("Platform Comparison")
            platforms = ['Steam', 'Epic', 'GOG', 'Xbox']
            market_share = [65, 20, 8, 7]
            
            fig = px.pie(values=market_share, names=platforms, title="PC Gaming Market Share")
            st.plotly_chart(fig, use_container_width=True)
    
    def render_events_page(self):
        """Render events analysis page"""
        st.title("📅 Events & Trends Analysis")
        
        if IS_CLOUD:
            events = st.session_state.demo_data['events']
        else:
            try:
                events = get_upcoming_events(10)
            except:
                events = [
                    {"name": "Valentine's Day", "start_date": "2024-02-14", "event_type": "Holiday"},
                    {"name": "March Madness", "start_date": "2024-03-15", "event_type": "Sports"},
                    {"name": "Easter", "start_date": "2024-04-21", "event_type": "Holiday"},
                ]
        
        st.subheader("Major Upcoming Events")
        
        for event in events:
            with st.expander(f"{event['name']} - {event.get('start_date', 'TBD')}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Event Type", event.get('event_type', 'N/A'))
                with col2:
                    st.metric("Related Apps", "200+")
                with col3:
                    st.metric("Impact Score", "High")
    
    def render_analytics_page(self):
        """Render advanced analytics page"""
        st.title("🔍 Premium Analytics Dashboard")
        
        user = st.session_state.get('user', {})
        if user.get('subscription_plan') == 'free':
            st.warning("🔒 Premium Analytics is available for Premium subscribers only.")
            st.info("💡 Upgrade to unlock: Clone Detection, Sentiment Analysis, Revenue Intelligence, and more!")
            if st.button("Upgrade to Premium"):
                mode = "demo" if IS_CLOUD else "production"
                st.info(f"This is a {mode}. In production, this would redirect to upgrade page.")
            return
        
        # Premium feature indicator
        mode = "Cloud Demo" if IS_CLOUD else "Local Live"
        st.success(f"🎉 Premium Analytics Unlocked! ({mode} Mode)")
        
        # Multiple analytics sections for premium users
        tab1, tab2, tab3 = st.tabs(["🔍 Clone Detection", "📊 Sentiment Analysis", "💰 Revenue Insights"])
        
        with tab1:
            st.subheader("AI-Powered Clone Detection")
            
            clones = [
                {"original": "PopularGame Pro", "clone": "PopGame Clone", "similarity": "94%", "risk": "High"},
                {"original": "Photo Editor", "clone": "Picture Edit Pro", "similarity": "87%", "risk": "Medium"},
                {"original": "Fitness Tracker", "clone": "Health Monitor", "similarity": "82%", "risk": "Medium"}
            ]
            
            for clone in clones:
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                    with col1:
                        st.write(f"**Original:** {clone['original']}")
                    with col2:
                        st.write(f"**Potential Clone:** {clone['clone']}")
                    with col3:
                        st.write(f"**Similarity:** {clone['similarity']}")
                    with col4:
                        risk_color = "🔴" if clone['risk'] == "High" else "🟡"
                        st.write(f"{risk_color} {clone['risk']}")
                    st.divider()
        
        with tab2:
            st.subheader("Review Sentiment Analysis")
            
            sentiment_data = {
                'App': ['SuperGame Pro', 'Fitness Tracker 2024', 'Photo Editor Max'],
                'Positive %': [78, 85, 72],
                'Negative %': [12, 8, 18],
                'Neutral %': [10, 7, 10],
                'Sentiment Score': [8.2, 8.7, 7.8]
            }
            
            df = pd.DataFrame(sentiment_data)
            st.dataframe(df, use_container_width=True)
            
            # Sentiment chart
            fig = px.bar(df, x='App', y=['Positive %', 'Negative %', 'Neutral %'], 
                        title="Review Sentiment Distribution")
            st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            st.subheader("Revenue Intelligence")
            
            revenue_data = {
                'App': ['SuperGame Pro', 'Fitness Tracker 2024', 'Photo Editor Max'],
                'Est. Daily Revenue': ['$12,500', '$8,900', '$6,700'],
                'Revenue Trend': ['+23%', '+15%', '-5%'],
                'Monetization': ['Freemium + IAP', 'Subscription', 'One-time + IAP']
            }
            
            df = pd.DataFrame(revenue_data)
            st.dataframe(df, use_container_width=True)
            
            st.info("💡 **Premium Insight:** Apps with subscription models show 40% more stable revenue growth.")
    
    def render_alerts_page(self):
        """Render alerts management page"""
        st.title("🔔 Alerts & Notifications")
        
        mode = "Demo" if IS_CLOUD else "Live"
        st.info(f"Running in {mode} mode")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Active Alerts")
            
            alerts = [
                {"name": "SuperGame Pro Rank Change", "condition": "Rank < 5", "status": "Active"},
                {"name": "New Gaming Apps", "condition": "Score > 85", "status": "Active"},
                {"name": "Holiday Event Apps", "condition": "Holiday correlation", "status": "Paused"}
            ]
            
            for alert in alerts:
                with st.container():
                    col_a, col_b, col_c = st.columns([3, 2, 1])
                    with col_a:
                        st.write(f"**{alert['name']}**")
                        st.caption(alert['condition'])
                    with col_b:
                        status_color = "🟢" if alert['status'] == "Active" else "⏸️"
                        st.write(f"{status_color} {alert['status']}")
                    with col_c:
                        if st.button("Edit", key=f"edit_{alert['name']}"):
                            st.info(f"Opening alert editor... ({mode} mode)")
                st.divider()
        
        with col2:
            st.subheader("Create New Alert")
            
            with st.form("new_alert"):
                alert_name = st.text_input("Alert Name")
                alert_type = st.selectbox("Alert Type", ["Rank Change", "Score Threshold", "New App"])
                condition = st.text_input("Condition")
                notification_method = st.selectbox("Notify Via", ["Email", "Dashboard", "Webhook"])
                
                if st.form_submit_button("Create Alert"):
                    st.success(f"Alert created successfully! ({mode} mode)")

# Main application entry point
def main():
    dashboard = UnifiedHunterDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()