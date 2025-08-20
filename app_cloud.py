import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, Any, List
import os
import sqlite3

# Streamlit Cloud Configuration
st.set_page_config(
    page_title="Hunter - App Discovery Platform",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Simple authentication for cloud deployment
def simple_auth():
    """Simple authentication system for Streamlit Cloud"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.title("🎯 Hunter - Login")
        
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                # Simple demo authentication
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

# Simple database functions for cloud
def init_demo_database():
    """Initialize demo database with sample data"""
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

class CloudHunterDashboard:
    def __init__(self):
        init_demo_database()
        
        # Initialize session state
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'dashboard'
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = datetime.now()
    
    def run(self):
        """Main application entry point"""
        # Check authentication
        if not simple_auth():
            return
        
        # Sidebar navigation
        self.render_sidebar()
        
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
    
    def render_sidebar(self):
        """Render navigation sidebar"""
        with st.sidebar:
            st.title("🎯 Hunter")
            
            user = st.session_state.get('user', {})
            st.write(f"Welcome, {user.get('email', 'User')}")
            st.write(f"Plan: {user.get('subscription_plan', 'free').title()}")
            
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
                st.session_state.authenticated = False
                st.rerun()
    
    def render_dashboard(self):
        """Render main dashboard"""
        st.title("🎯 Hunter - App Discovery Dashboard")
        
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        apps_count = len(st.session_state.demo_data['apps'])
        steam_count = len(st.session_state.demo_data['steam_games'])
        events_count = len(st.session_state.demo_data['events'])
        
        with col1:
            st.metric("Apps Tracked", f"{apps_count:,}", f"+{apps_count}")
        
        with col2:
            st.metric("Steam Games", f"{steam_count:,}", f"+{steam_count}")
        
        with col3:
            st.metric("Active Alerts", "5", "+2")
        
        with col4:
            st.metric("Trending Score", "87%", "+Live")
        
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
        apps = st.session_state.demo_data['apps']
        
        trending_data = {
            'App Name': [app['title'] for app in apps],
            'Developer': [app['developer'] for app in apps],
            'Category': [app['category'] for app in apps],
            'Current Rank': [app['current_rank'] for app in apps],
            'Rating': [f"{app['rating']:.1f}" for app in apps],
            'Reviews': [f"{app['review_count']:,}" for app in apps]
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
        events = st.session_state.demo_data['events']
        
        for event in events:
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{event['name']}**")
                    st.caption(f"{event['start_date']} • {event['event_type']} • {event['region']}")
                with col2:
                    st.write("📅 Upcoming")
                st.divider()
    
    def render_quick_actions(self):
        """Render quick action buttons"""
        if st.button("🎯 Find Next Hit", use_container_width=True):
            st.info("Analyzing market trends... (Demo mode)")
        
        if st.button("📊 Generate Report", use_container_width=True):
            st.info("Preparing comprehensive report... (Demo mode)")
        
        if st.button("🔔 Set Alert", use_container_width=True):
            st.info("Opening alert configuration... (Demo mode)")
        
        if st.button("💾 Export Data", use_container_width=True):
            sample_data = pd.DataFrame(st.session_state.demo_data['apps'])
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
            
            # App data from demo
            apps_df = pd.DataFrame(st.session_state.demo_data['apps'])
            st.dataframe(apps_df, use_container_width=True)
            
            # Category distribution
            categories = apps_df['category'].value_counts()
            fig = px.pie(values=categories.values, names=categories.index, title="App Distribution by Category")
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.subheader("🤖 AI Predictions (Demo)")
            
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
            
            selected_app = st.selectbox(
                "Select App for Analysis",
                [app['title'] for app in st.session_state.demo_data['apps']]
            )
            
            if selected_app:
                app_data = next(app for app in st.session_state.demo_data['apps'] if app['title'] == selected_app)
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.write(f"**{selected_app}**")
                    st.write(f"{app_data['category']} • Free with IAP")
                    st.write(f"⭐ {app_data['rating']} ({app_data['review_count']:,} reviews)")
                
                with col2:
                    metrics_col1, metrics_col2 = st.columns(2)
                    with metrics_col1:
                        st.metric("Current Rank", f"#{app_data['current_rank']}", "-2")
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
            steam_df = pd.DataFrame(st.session_state.demo_data['steam_games'])
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
        
        events = st.session_state.demo_data['events']
        
        st.subheader("Major Upcoming Events")
        
        for event in events:
            with st.expander(f"{event['name']} - {event['start_date']}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Event Type", event['event_type'])
                with col2:
                    st.metric("Related Apps", "200+")
                with col3:
                    st.metric("Impact Score", "High")
    
    def render_analytics_page(self):
        """Render advanced analytics page"""
        st.title("🔍 Advanced Analytics")
        
        user = st.session_state.get('user', {})
        if user.get('subscription_plan') == 'free':
            st.warning("🔒 Advanced Analytics is available for Premium subscribers only.")
            if st.button("Upgrade to Premium"):
                st.info("This is a demo. In production, this would redirect to upgrade page.")
            return
        
        st.subheader("Clone Detection Results (Demo)")
        
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
                            st.info("Opening alert editor... (Demo mode)")
                st.divider()
        
        with col2:
            st.subheader("Create New Alert")
            
            with st.form("new_alert"):
                alert_name = st.text_input("Alert Name")
                alert_type = st.selectbox("Alert Type", ["Rank Change", "Score Threshold", "New App"])
                condition = st.text_input("Condition")
                notification_method = st.selectbox("Notify Via", ["Email", "Dashboard", "Webhook"])
                
                if st.form_submit_button("Create Alert"):
                    st.success("Alert created successfully! (Demo mode)")

# Main application entry point
def main():
    dashboard = CloudHunterDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()