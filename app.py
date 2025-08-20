import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, Any, List

# Import local modules
from config import config
from models import database, App, User, Event, SteamGame, Score
try:
    from scrapers.enhanced_app_store_scraper import EnhancedAppStoreScraper as AppStoreScraper
    from scrapers.enhanced_steam_scraper import EnhancedSteamScraper as SteamScraper
    from scrapers.comprehensive_events_scraper import ComprehensiveEventsScraper as EventsScraper
    print("Using enhanced scrapers")
except ImportError:
    from scrapers.app_store_scraper import AppStoreScraper
    from scrapers.steam_scraper import SteamScraper
    from scrapers.events_scraper import EventsScraper
    print("Using basic scrapers")
try:
    from analytics.processor import AnalyticsProcessor
except ImportError:
    from analytics.processor_simple import AnalyticsProcessor
    print("Using simplified analytics processor (some ML features disabled)")
try:
    from ml.predictor import SuccessPredictor
except ImportError:
    # Create a simple fallback predictor
    class SuccessPredictor:
        def __init__(self):
            self.is_trained = False
        def calculate_weighted_score(self, app_data, analytics_data=None):
            rating = float(app_data.get('rating', 0))
            review_count = int(app_data.get('review_count', 0))
            score = (rating / 5.0) * 50 + min(review_count / 1000, 50)
            return {'success_score': min(score, 100), 'breakdown': {'rating': rating * 10, 'reviews': min(review_count / 100, 40)}}
    print("Using simplified ML predictor (advanced ML features disabled)")
from auth import auth_manager

# Configure Streamlit page
st.set_page_config(**config.get_streamlit_config())

class HunterDashboard:
    def __init__(self):
        self.app_scraper = AppStoreScraper()
        self.steam_scraper = SteamScraper()
        self.events_scraper = EventsScraper()
        self.analytics = AnalyticsProcessor()
        self.predictor = SuccessPredictor()
        
        # Initialize session state
        if 'data_cache' not in st.session_state:
            st.session_state.data_cache = {}
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = None
    
    def run(self):
        """Main application entry point"""
        # Check authentication
        user = auth_manager.require_auth()
        if not user:
            return
        
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
        elif page == 'api':
            self.render_api_page()
        elif page == 'settings':
            self.render_settings_page()
    
    def render_sidebar(self, user: Dict[str, Any]):
        """Render navigation sidebar"""
        with st.sidebar:
            st.title("🎯 Hunter")
            st.write(f"Welcome, {user['email']}")
            st.write(f"Plan: {user['subscription_plan'].title()}")
            
            # Navigation menu
            st.subheader("Navigation")
            
            pages = {
                'dashboard': '📊 Dashboard',
                'apps': '📱 App Store',
                'steam': '🎮 Steam Games',
                'events': '📅 Events',
                'analytics': '🔍 Analytics',
                'alerts': '🔔 Alerts'
            }
            
            # Admin-only pages
            if auth_manager.check_role('admin'):
                pages['api'] = '🔌 API'
                pages['settings'] = '⚙️ Settings'
            
            # Use radio buttons instead of buttons to avoid rerun issues
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
            
            st.divider()
            
            # Data refresh
            if st.button("🔄 Refresh Data", use_container_width=True):
                self.refresh_data()
            
            if st.session_state.last_refresh:
                st.caption(f"Last updated: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
            
            st.divider()
            
            # Logout
            if st.button("🚪 Logout", use_container_width=True):
                auth_manager.logout()
    
    def render_dashboard(self):
        """Render main dashboard"""
        st.title("🎯 Hunter - App Discovery Dashboard")
        
        # Get real database statistics
        try:
            from dashboard_utils import get_database_stats
            stats = get_database_stats()
        except ImportError:
            # Fallback to basic stats if utils not available
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
            # Calculate a simple trending score based on data availability
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
        try:
            from dashboard_utils import get_recent_apps
            apps = get_recent_apps(10)
            
            if apps:
                # Convert real data to display format
                trending_data = {
                    'App Name': [app['title'] for app in apps],
                    'Developer': [app['developer'] or 'Unknown' for app in apps],
                    'Category': [app['category'] or 'Unknown' for app in apps],
                    'Current Rank': [app['current_rank'] or 'N/A' for app in apps],
                    'Rating': [f"{app['rating']:.1f}" if app['rating'] else 'N/A' for app in apps],
                    'Reviews': [app['review_count'] or 0 for app in apps]
                }
                
                df = pd.DataFrame(trending_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No apps found in database. Run the scraper to collect app data.")
                
        except ImportError:
            # Fallback to mock data if utils not available
            trending_data = {
                'App Name': ['Demo App 1', 'Demo App 2', 'Demo App 3'],
                'Category': ['Games', 'Utilities', 'Entertainment'],
                'Status': ['No real data', 'Run scraper', 'to populate']
            }
            
            df = pd.DataFrame(trending_data)
            st.dataframe(df, use_container_width=True)
            st.warning("Showing demo data. Import dashboard_utils to see real database statistics.")
    
    def render_chart_climbers(self):
        """Render chart showing ranking changes"""
        # Mock chart data
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        
        fig = go.Figure()
        
        # Add sample app ranking trends
        apps = ['SuperGame Pro', 'Fitness Tracker 2024', 'Photo Editor Max']
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        
        for i, app in enumerate(apps):
            # Generate mock ranking data (lower is better)
            rankings = np.random.randint(1, 100, len(dates))
            rankings = np.sort(rankings)[::-1]  # Trending up (improving rank)
            
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
            yaxis=dict(autorange='reversed'),  # Lower rank numbers at top
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_upcoming_events(self):
        """Render upcoming events list"""
        try:
            from dashboard_utils import get_upcoming_events
            events = get_upcoming_events(5)
            
            if events:
                for event in events:
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**{event['name']}**")
                            st.caption(f"{event['start_date'][:10]} • {event['event_type']} • {event['region']}")
                        with col2:
                            st.write("📅 Upcoming")
                        st.divider()
            else:
                st.info("No upcoming events found in database.")
                
        except ImportError:
            # Fallback to demo events
            events_data = [
                {"name": "Demo Event", "date": "Future", "type": "Demo", "status": "No real data"},
            ]
            
            for event in events_data:
                with st.container():
                    st.write(f"**{event['name']}**")
                    st.caption(f"{event['date']} • {event['type']} • {event['status']}")
                    st.divider()
            st.warning("Showing demo data. Import dashboard_utils to see real events.")
    
    def render_quick_actions(self):
        """Render quick action buttons"""
        if st.button("🎯 Find Next Hit", use_container_width=True):
            st.info("Analyzing market trends...")
            # Here you would trigger the ML prediction pipeline
        
        if st.button("📊 Generate Report", use_container_width=True):
            st.info("Preparing comprehensive report...")
        
        if st.button("🔔 Set Alert", use_container_width=True):
            st.info("Opening alert configuration...")
        
        if st.button("💾 Export Data", use_container_width=True):
            # Generate sample CSV
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
        
        # Main content
        tab1, tab2, tab3 = st.tabs(["📈 Rankings", "💡 Predictions", "🔍 Deep Dive"])
        
        with tab1:
            self.render_app_rankings()
        
        with tab2:
            self.render_app_predictions()
        
        with tab3:
            self.render_app_deep_dive()
    
    def render_app_rankings(self):
        """Render app rankings analysis"""
        st.subheader("Current Top Apps")
        
        # Category distribution pie chart
        col1, col2 = st.columns(2)
        
        with col1:
            categories = ['Games', 'Entertainment', 'Utilities', 'Health', 'Education']
            values = [35, 25, 15, 15, 10]
            
            fig = px.pie(
                values=values,
                names=categories,
                title="App Distribution by Category"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Velocity distribution
            velocities = np.random.normal(50, 20, 100)
            fig = px.histogram(
                x=velocities,
                nbins=20,
                title="Ranking Velocity Distribution"
            )
            fig.update_xaxis(title="Velocity Score")
            fig.update_yaxis(title="Number of Apps")
            st.plotly_chart(fig, use_container_width=True)
    
    def render_app_predictions(self):
        """Render ML predictions for apps"""
        st.subheader("🤖 AI Predictions")
        
        # Mock prediction data
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
        
        # Prediction accuracy metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Model Accuracy", "87.3%", "+2.1%")
        
        with col2:
            st.metric("Predictions Made", "1,234", "+45")
        
        with col3:
            st.metric("Success Rate", "82%", "+1%")
    
    def render_app_deep_dive(self):
        """Render detailed app analysis"""
        st.subheader("🔍 App Deep Dive")
        
        selected_app = st.selectbox(
            "Select App for Analysis",
            ["SuperGame Pro", "Fitness Tracker 2024", "Photo Editor Max"]
        )
        
        if selected_app:
            # App info
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.image("https://via.placeholder.com/100x100", width=100)
                st.write(f"**{selected_app}**")
                st.write("Games • Free with IAP")
                st.write("⭐ 4.8 (12.5K reviews)")
            
            with col2:
                # Metrics
                metrics_col1, metrics_col2 = st.columns(2)
                with metrics_col1:
                    st.metric("Current Rank", "#3", "-12")
                    st.metric("Success Score", "94", "+7")
                
                with metrics_col2:
                    st.metric("Review Velocity", "+45%", "+12%")
                    st.metric("Revenue Estimate", "$125K", "+23%")
            
            # Charts
            st.subheader("Performance Charts")
            
            # Sample time series data
            dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
            ranks = np.random.randint(1, 50, 30)
            scores = np.random.randint(70, 100, 30)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dates, y=ranks, name="Rank", yaxis="y"))
            fig.add_trace(go.Scatter(x=dates, y=scores, name="Success Score", yaxis="y2"))
            
            fig.update_layout(
                title=f"{selected_app} - Performance Timeline",
                yaxis=dict(title="Rank", side="left"),
                yaxis2=dict(title="Success Score", side="right", overlaying="y"),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def render_steam_page(self):
        """Render Steam games analysis page"""
        st.title("🎮 Steam Games Analysis")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Trending Steam Games")
            
            # Mock Steam data
            steam_data = {
                'Game': ['Cyberpunk 2078', 'Fantasy RPG X', 'Battle Arena Pro', 'Puzzle Quest', 'Racing Sim 24'],
                'Genre': ['RPG', 'RPG', 'Action', 'Puzzle', 'Racing'],
                'Players': ['125K', '89K', '67K', '45K', '38K'],
                'Hype Score': [95, 88, 82, 76, 71],
                'Price': ['$59.99', '$29.99', '$19.99', '$9.99', '$39.99']
            }
            
            df = pd.DataFrame(steam_data)
            st.dataframe(df, use_container_width=True)
        
        with col2:
            st.subheader("Platform Comparison")
            
            platforms = ['Steam', 'Epic', 'GOG', 'Xbox']
            market_share = [65, 20, 8, 7]
            
            fig = px.pie(values=market_share, names=platforms, title="PC Gaming Market Share")
            st.plotly_chart(fig, use_container_width=True)
    
    def render_events_page(self):
        """Render events analysis page"""
        st.title("📅 Events & Trends Analysis")
        
        tab1, tab2 = st.tabs(["🗓️ Upcoming Events", "📊 Event Impact"])
        
        with tab1:
            st.subheader("Major Upcoming Events")
            
            events = [
                {"name": "Valentine's Day", "date": "2024-02-14", "type": "Holiday", "apps": 245},
                {"name": "March Madness", "date": "2024-03-15", "type": "Sports", "apps": 189},
                {"name": "Easter", "date": "2024-04-21", "type": "Holiday", "apps": 167},
            ]
            
            for event in events:
                with st.expander(f"{event['name']} - {event['date']}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Event Type", event['type'])
                    with col2:
                        st.metric("Related Apps", event['apps'])
                    with col3:
                        st.metric("Impact Score", "High")
        
        with tab2:
            st.subheader("Historical Event Impact")
            
            # Sample event impact chart
            events_timeline = pd.date_range(start='2023-01-01', periods=12, freq='M')
            impact_scores = np.random.randint(60, 100, 12)
            
            fig = px.line(
                x=events_timeline,
                y=impact_scores,
                title="Event Impact on App Downloads",
                labels={'x': 'Month', 'y': 'Impact Score'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def render_analytics_page(self):
        """Render advanced analytics page"""
        st.title("🔍 Advanced Analytics")
        
        # Only for premium users
        user = st.session_state.get('user', {})
        if user.get('subscription_plan') == 'free':
            st.warning("🔒 Advanced Analytics is available for Premium subscribers only.")
            if st.button("Upgrade to Premium"):
                st.info("Redirecting to upgrade page...")
            return
        
        st.subheader("Clone Detection Results")
        
        # Mock clone detection data
        clones = [
            {"original": "PopularGame Pro", "clone": "PopGame Clone", "similarity": "94%"},
            {"original": "Photo Editor", "clone": "Picture Edit Pro", "similarity": "87%"},
            {"original": "Fitness Tracker", "clone": "Health Monitor", "similarity": "82%"}
        ]
        
        for clone in clones:
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(f"**Original:** {clone['original']}")
                with col2:
                    st.write(f"**Potential Clone:** {clone['clone']}")
                with col3:
                    st.write(f"**Similarity:** {clone['similarity']}")
                st.divider()
    
    def render_alerts_page(self):
        """Render alerts management page"""
        st.title("🔔 Alerts & Notifications")
        
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
                            st.info("Opening alert editor...")
                st.divider()
        
        with col2:
            st.subheader("Create New Alert")
            
            with st.form("new_alert"):
                alert_name = st.text_input("Alert Name")
                alert_type = st.selectbox("Alert Type", ["Rank Change", "Score Threshold", "New App"])
                condition = st.text_input("Condition")
                notification_method = st.selectbox("Notify Via", ["Email", "Dashboard", "Webhook"])
                
                if st.form_submit_button("Create Alert"):
                    st.success("Alert created successfully!")
    
    def render_api_page(self):
        """Render API documentation page (admin only)"""
        if not auth_manager.check_role('admin'):
            st.error("Access denied. Admin role required.")
            return
        
        st.title("🔌 API Documentation")
        
        st.subheader("Available Endpoints")
        
        endpoints = [
            {"method": "GET", "endpoint": "/api/apps/top", "description": "Get top apps with success scores"},
            {"method": "GET", "endpoint": "/api/apps/{id}", "description": "Get detailed app analytics"},
            {"method": "GET", "endpoint": "/api/events/upcoming", "description": "Get upcoming events"},
            {"method": "POST", "endpoint": "/api/alerts", "description": "Create new alert"}
        ]
        
        for endpoint in endpoints:
            with st.expander(f"{endpoint['method']} {endpoint['endpoint']}"):
                st.write(endpoint['description'])
                st.code(f"""
curl -X {endpoint['method']} \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  https://api.hunter.app{endpoint['endpoint']}
                """)
    
    def render_settings_page(self):
        """Render settings page (admin only)"""
        if not auth_manager.check_role('admin'):
            st.error("Access denied. Admin role required.")
            return
        
        st.title("⚙️ System Settings")
        
        tab1, tab2, tab3 = st.tabs(["🔧 Configuration", "👥 Users", "📊 System Stats"])
        
        with tab1:
            st.subheader("Scraper Configuration")
            
            col1, col2 = st.columns(2)
            
            with col1:
                scraper_delay = st.slider("Scraper Delay (seconds)", 0.5, 5.0, 1.0)
                use_proxy = st.checkbox("Use Proxy Rotation")
                max_retries = st.number_input("Max Retries", 1, 10, 3)
            
            with col2:
                countries = st.multiselect(
                    "Target Countries",
                    ["US", "UK", "DE", "JP", "KR"],
                    default=["US", "UK"]
                )
                categories = st.multiselect(
                    "Target Categories",
                    ["Games", "Entertainment", "Utilities", "Health"],
                    default=["Games", "Entertainment"]
                )
            
            if st.button("Save Configuration"):
                st.success("Configuration saved!")
        
        with tab2:
            st.subheader("User Management")
            
            # Mock user data
            users_data = {
                'Email': ['admin@hunter.app', 'user1@example.com', 'user2@example.com'],
                'Role': ['Admin', 'User', 'Premium'],
                'Plan': ['Premium', 'Free', 'Premium'],
                'Status': ['Active', 'Active', 'Active']
            }
            
            df = pd.DataFrame(users_data)
            st.dataframe(df, use_container_width=True)
        
        with tab3:
            st.subheader("System Statistics")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Users", "1,234", "+45")
                st.metric("API Calls Today", "15.6K", "+2.3K")
            
            with col2:
                st.metric("Apps in Database", "125K", "+1.2K")
                st.metric("Predictions Made", "5.8K", "+234")
            
            with col3:
                st.metric("System Uptime", "99.7%", "+0.1%")
                st.metric("Storage Used", "85%", "+2%")
    
    def refresh_data(self):
        """Refresh data cache"""
        st.session_state.data_cache = {}
        st.session_state.last_refresh = datetime.now()
        st.success("Data refreshed!")
        # Don't use rerun here to avoid infinite loops

# Main application entry point
def main():
    dashboard = HunterDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()