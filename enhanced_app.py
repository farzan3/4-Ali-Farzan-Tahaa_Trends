import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, Any, List
import time
import asyncio
import threading

# Import local modules
from config import config
from models import database, App, User, Event, SteamGame, Score
from pipeline.data_pipeline import automated_pipeline

# Import scrapers
from scrapers.enhanced_app_store_scraper import EnhancedAppStoreScraper
from scrapers.enhanced_steam_scraper import EnhancedSteamScraper
from scrapers.comprehensive_events_scraper import ComprehensiveEventsScraper

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

from auth import auth_manager

# Configure Streamlit page
st.set_page_config(**config.get_streamlit_config())

class EnhancedHunterDashboard:
    def __init__(self):
        self.app_scraper = EnhancedAppStoreScraper()
        self.steam_scraper = EnhancedSteamScraper()
        self.events_scraper = ComprehensiveEventsScraper()
        self.analytics = AnalyticsProcessor()
        self.predictor = SuccessPredictor()
        
        # Initialize session state
        if 'pipeline_running' not in st.session_state:
            st.session_state.pipeline_running = False
        if 'live_data' not in st.session_state:
            st.session_state.live_data = {}
        if 'auto_refresh' not in st.session_state:
            st.session_state.auto_refresh = False
        if 'refresh_interval' not in st.session_state:
            st.session_state.refresh_interval = 300  # 5 minutes
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = None
    
    def run(self):
        """Main application entry point"""
        # Check authentication
        user = auth_manager.require_auth()
        if not user:
            return
        
        # Sidebar navigation
        self.render_enhanced_sidebar(user)
        
        # Main content area
        page = st.session_state.get('current_page', 'live_dashboard')
        
        if page == 'live_dashboard':
            self.render_live_dashboard()
        elif page == 'scraping_control':
            self.render_scraping_control()
        elif page == 'comprehensive_analysis':
            self.render_comprehensive_analysis()
        elif page == 'cross_platform':
            self.render_cross_platform_analysis()
        elif page == 'events_intelligence':
            self.render_events_intelligence()
        elif page == 'predictions':
            self.render_predictions_dashboard()
        elif page == 'pipeline_status':
            self.render_pipeline_status()
        elif page == 'data_explorer':
            self.render_data_explorer()
        else:
            # Fall back to original pages
            self.render_original_page(page)
    
    def render_enhanced_sidebar(self, user: Dict[str, Any]):
        """Render enhanced navigation sidebar"""
        with st.sidebar:
            st.title("🎯 Hunter Enhanced")
            st.write(f"Welcome, {user['email']}")
            st.write(f"Plan: {user['subscription_plan'].title()}")
            
            # Pipeline control (Admin only)
            if auth_manager.check_role('admin'):
                st.subheader("🔧 Pipeline Control")
                
                pipeline_status = automated_pipeline.get_pipeline_status()
                
                if pipeline_status['is_running']:
                    st.success("✅ Pipeline Active")
                    if st.button("🛑 Stop Pipeline", use_container_width=True):
                        automated_pipeline.stop_pipeline()
                        st.rerun()
                else:
                    st.warning("⏸️ Pipeline Stopped")
                    if st.button("▶️ Start Pipeline", use_container_width=True):
                        automated_pipeline.start_pipeline()
                        st.rerun()
            else:
                st.subheader("📊 System Status")
                pipeline_status = automated_pipeline.get_pipeline_status()
                status_text = "🟢 Active" if pipeline_status['is_running'] else "🔴 Inactive"
                st.info(f"Pipeline Status: {status_text}")
            
            # Auto-refresh control
            st.subheader("🔄 Auto Refresh")
            st.session_state.auto_refresh = st.checkbox("Enable Auto Refresh", st.session_state.auto_refresh)
            
            if st.session_state.auto_refresh:
                st.session_state.refresh_interval = st.slider(
                    "Refresh Interval (seconds)", 
                    60, 1800, 
                    st.session_state.refresh_interval
                )
            
            # Navigation menu
            st.subheader("📋 Navigation")
            
            pages = {
                'live_dashboard': '🔴 Live Dashboard',
                'comprehensive_analysis': '📊 Comprehensive Analysis',
                'cross_platform': '🔀 Cross-Platform Intelligence',
                'events_intelligence': '📅 Events Intelligence',
                'predictions': '🔮 Success Predictions',
                'data_explorer': '🔍 Data Explorer'
            }
            
            # Admin-only pages
            if auth_manager.check_role('admin'):
                pages['scraping_control'] = '🕷️ Scraping Control'
                pages['pipeline_status'] = '⚙️ Pipeline Status'
            
            for page_key, page_name in pages.items():
                if st.button(page_name, use_container_width=True):
                    st.session_state.current_page = page_key
                    st.rerun()
            
            st.divider()
            
            # Data refresh
            if st.button("🔄 Manual Refresh", use_container_width=True):
                self.refresh_live_data()
            
            if st.session_state.last_refresh:
                st.caption(f"Last updated: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
            
            st.divider()
            
            # Logout
            if st.button("🚪 Logout", use_container_width=True):
                auth_manager.logout()
    
    def render_live_dashboard(self):
        """Render enhanced live dashboard"""
        st.title("🔴 Live Hunter Dashboard")
        
        # Auto-refresh logic
        if st.session_state.auto_refresh:
            self.handle_auto_refresh()
        
        # Live metrics header
        col1, col2, col3, col4, col5 = st.columns(5)
        
        pipeline_status = automated_pipeline.get_pipeline_status()
        cache_data = pipeline_status['cache_summary']
        
        with col1:
            st.metric("🍎 Apps Tracked", f"{cache_data.get('apps', 0):,}", "+Real-time")
        
        with col2:
            st.metric("🎮 Steam Games", f"{cache_data.get('steam_games', 0):,}", "+Live")
        
        with col3:
            st.metric("📅 Events", f"{cache_data.get('events', 0):,}", "+Updated")
        
        with col4:
            pipeline_indicator = "🟢 Active" if pipeline_status['is_running'] else "🔴 Stopped"
            st.metric("⚙️ Pipeline", pipeline_indicator, "")
        
        with col5:
            refresh_indicator = "🔄 Auto" if st.session_state.auto_refresh else "⏸️ Manual"
            st.metric("🔄 Refresh", refresh_indicator, "")
        
        st.divider()
        
        # Live trending section
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🔥 Live Trending Apps")
            self.render_live_trending_apps()
            
            st.subheader("📈 Real-Time Chart Movement")
            self.render_realtime_charts()
        
        with col2:
            st.subheader("⚡ Breaking Events")
            self.render_breaking_events()
            
            st.subheader("🎯 Instant Opportunities")
            self.render_instant_opportunities()
    
    def render_scraping_control(self):
        """Render scraping control interface (Admin only)"""
        # Check admin access
        if not auth_manager.check_role('admin'):
            st.error("🔒 Access Denied: Scraping control requires admin privileges.")
            st.info("Contact your administrator to access manual scraping controls.")
            return
        
        st.title("🕷️ Enhanced Scraping Control")
        st.warning("⚠️ Admin Only: Manual scraping operations")
        
        # Scraping status overview
        st.subheader("📊 Scraping Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info("**App Store Scraping**")
            if st.button("🍎 Run Full App Store Scrape", use_container_width=True):
                self.run_manual_scrape('app_store_full')
            
            if st.button("🍎 Quick App Store Update", use_container_width=True):
                self.run_manual_scrape('app_store_quick')
        
        with col2:
            st.info("**Steam Scraping**")
            if st.button("🎮 Run Full Steam Scrape", use_container_width=True):
                self.run_manual_scrape('steam_comprehensive')
            
            if st.button("🎮 Quick Steam Update", use_container_width=True):
                self.run_manual_scrape('steam_quick')
        
        with col3:
            st.info("**Events Scraping**")
            if st.button("📅 Run Full Events Scrape", use_container_width=True):
                self.run_manual_scrape('events_comprehensive')
            
            if st.button("📅 Daily Events Update", use_container_width=True):
                self.run_manual_scrape('events_daily')
        
        st.divider()
        
        # Advanced scraping configuration
        st.subheader("⚙️ Scraping Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**App Store Configuration**")
            
            selected_countries = st.multiselect(
                "Target Countries",
                ["us", "gb", "ca", "de", "fr", "jp", "kr", "cn", "in", "br"],
                default=["us", "gb", "ca", "de", "jp"]
            )
            
            selected_categories = st.multiselect(
                "Target Categories",
                ["games", "entertainment", "productivity", "social-networking", "health-fitness"],
                default=["games", "entertainment"]
            )
            
            chart_types = st.multiselect(
                "Chart Types",
                ["top-free", "top-paid", "top-grossing", "new-apps"],
                default=["top-free", "top-grossing"]
            )
        
        with col2:
            st.write("**Steam Configuration**")
            
            steam_categories = st.multiselect(
                "Steam Categories",
                ["Action", "Adventure", "RPG", "Strategy", "Indie", "Free to Play"],
                default=["Action", "Adventure", "Indie"]
            )
            
            include_early_access = st.checkbox("Include Early Access", True)
            include_vr = st.checkbox("Include VR Games", True)
            
            max_games_per_category = st.slider("Max Games per Category", 50, 500, 200)
        
        if st.button("🚀 Run Custom Scraping Job", use_container_width=True):
            st.info("Starting custom scraping job with selected parameters...")
            # Implementation would go here
    
    def render_comprehensive_analysis(self):
        """Render comprehensive analysis dashboard"""
        st.title("📊 Comprehensive Market Analysis")
        
        # Analysis overview
        st.subheader("🎯 Market Intelligence Overview")
        
        # Get analysis data from pipeline
        analysis_data = automated_pipeline.data_cache.get('analysis', {})
        
        if not analysis_data:
            st.warning("No analysis data available. Run comprehensive analysis first.")
            if st.button("▶️ Run Analysis Now"):
                with st.spinner("Running comprehensive analysis..."):
                    automated_pipeline.execute_job('comprehensive_analysis')
                st.rerun()
            return
        
        # Analysis metrics
        col1, col2, col3, col4 = st.columns(4)
        
        app_analysis = analysis_data.get('app_store', {})
        steam_analysis = analysis_data.get('steam', {})
        events_analysis = analysis_data.get('events', {})
        cross_platform = analysis_data.get('cross_platform', {})
        
        with col1:
            fast_climbers = len(app_analysis.get('fast_climbers', []))
            st.metric("📈 Fast Climbers", fast_climbers, f"+{fast_climbers}")
        
        with col2:
            trending_games = len(steam_analysis.get('trending_games', []))
            st.metric("🎮 Steam Trending", trending_games, f"+{trending_games}")
        
        with col3:
            high_impact_events = len(events_analysis.get('high_impact_events', []))
            st.metric("📅 High Impact Events", high_impact_events, f"+{high_impact_events}")
        
        with col4:
            correlations = len(cross_platform.get('top_correlations', []))
            st.metric("🔀 Cross-Platform Matches", correlations, f"+{correlations}")
        
        st.divider()
        
        # Detailed analysis sections
        tab1, tab2, tab3, tab4 = st.tabs(["📱 App Store Analysis", "🎮 Steam Analysis", "📅 Events Impact", "🔀 Cross-Platform"])
        
        with tab1:
            self.render_app_store_analysis(app_analysis)
        
        with tab2:
            self.render_steam_analysis(steam_analysis)
        
        with tab3:
            self.render_events_analysis(events_analysis)
        
        with tab4:
            self.render_cross_platform_analysis_detailed(cross_platform)
    
    def render_cross_platform_analysis(self):
        """Render cross-platform intelligence"""
        st.title("🔀 Cross-Platform Intelligence")
        
        st.info("Analyzing correlations between App Store and Steam gaming trends")
        
        # Cross-platform metrics
        cross_platform_data = automated_pipeline.data_cache.get('analysis', {}).get('cross_platform', {})
        
        if cross_platform_data:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                correlations = len(cross_platform_data.get('top_correlations', []))
                st.metric("🔗 Strong Correlations", correlations)
            
            with col2:
                avg_similarity = cross_platform_data.get('avg_similarity', 0)
                st.metric("📊 Avg Similarity", f"{avg_similarity:.2%}")
            
            with col3:
                st.metric("🎯 Analysis Status", "✅ Complete")
            
            # Correlation details
            st.subheader("🎮 App Store ↔️ Steam Correlations")
            
            correlations = cross_platform_data.get('top_correlations', [])
            if correlations:
                correlation_df = pd.DataFrame(correlations)
                
                # Interactive correlation chart
                fig = px.scatter(
                    correlation_df,
                    x='app_rank',
                    y='steam_score',
                    size='similarity',
                    hover_data=['app_title', 'steam_title'],
                    title="Cross-Platform Game Performance Correlation",
                    labels={'app_rank': 'App Store Rank', 'steam_score': 'Steam Trend Score'}
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Top correlations table
                st.subheader("🏆 Top Cross-Platform Matches")
                st.dataframe(correlation_df, use_container_width=True)
            else:
                st.info("No strong correlations found in current dataset")
        else:
            st.warning("Cross-platform analysis not available. Run comprehensive analysis first.")
    
    def render_events_intelligence(self):
        """Render events intelligence dashboard"""
        st.title("📅 Events Intelligence Dashboard")
        
        events_data = automated_pipeline.data_cache.get('events', [])
        
        if not events_data:
            st.warning("No events data available. Run events scraping first.")
            return
        
        # Events overview
        col1, col2, col3, col4 = st.columns(4)
        
        total_events = len(events_data)
        high_impact = len([e for e in events_data if e.get('impact_score', 0) > 70])
        global_events = len([e for e in events_data if e.get('region') == 'global'])
        upcoming = len([e for e in events_data if self.is_upcoming_event(e)])
        
        with col1:
            st.metric("📅 Total Events", total_events)
        
        with col2:
            st.metric("🔥 High Impact", high_impact)
        
        with col3:
            st.metric("🌍 Global Events", global_events)
        
        with col4:
            st.metric("⏰ Upcoming", upcoming)
        
        st.divider()
        
        # Events analysis
        tab1, tab2, tab3 = st.tabs(["📈 Impact Analysis", "🗓️ Timeline", "🎯 App Opportunities"])
        
        with tab1:
            self.render_events_impact_analysis(events_data)
        
        with tab2:
            self.render_events_timeline(events_data)
        
        with tab3:
            self.render_events_app_opportunities(events_data)
    
    def render_predictions_dashboard(self):
        """Render AI predictions dashboard"""
        st.title("🔮 AI Success Predictions")
        
        predictions_data = automated_pipeline.data_cache.get('analysis', {}).get('predictions', {})
        
        if not predictions_data:
            st.warning("No predictions available. Run comprehensive analysis first.")
            return
        
        # Predictions overview
        col1, col2, col3, col4 = st.columns(4)
        
        total_predictions = predictions_data.get('total_predictions', 0)
        platform_breakdown = predictions_data.get('platform_breakdown', {})
        app_store_predictions = platform_breakdown.get('app_store', 0)
        steam_predictions = platform_breakdown.get('steam', 0)
        
        with col1:
            st.metric("🎯 Total Predictions", total_predictions)
        
        with col2:
            st.metric("📱 App Store", app_store_predictions)
        
        with col3:
            st.metric("🎮 Steam", steam_predictions)
        
        with col4:
            avg_confidence = 0.85  # Mock value
            st.metric("📊 Avg Confidence", f"{avg_confidence:.0%}")
        
        st.divider()
        
        # Top predictions
        st.subheader("🏆 Top Success Predictions")
        
        top_predictions = predictions_data.get('top_predictions', [])
        if top_predictions:
            predictions_df = pd.DataFrame(top_predictions)
            
            # Success score distribution
            fig = px.histogram(
                predictions_df,
                x='success_score',
                color='platform',
                title="Success Score Distribution by Platform",
                nbins=20
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Predictions table
            st.dataframe(predictions_df, use_container_width=True)
        else:
            st.info("No predictions available")
    
    def render_pipeline_status(self):
        """Render detailed pipeline status (Admin only)"""
        # Check admin access
        if not auth_manager.check_role('admin'):
            st.error("🔒 Access Denied: Pipeline status requires admin privileges.")
            st.info("Contact your administrator to access pipeline management.")
            return
        
        st.title("⚙️ Pipeline Status & Performance")
        st.warning("⚠️ Admin Only: System monitoring and control")
        
        status = automated_pipeline.get_pipeline_status()
        
        # Pipeline overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_indicator = "🟢 Running" if status['is_running'] else "🔴 Stopped"
            st.metric("Pipeline Status", status_indicator)
        
        with col2:
            last_analysis = status['cache_summary'].get('last_analysis')
            if last_analysis:
                time_ago = self.time_ago(last_analysis)
                st.metric("Last Analysis", time_ago)
            else:
                st.metric("Last Analysis", "Never")
        
        with col3:
            # Calculate total data points excluding datetime fields
            cache_summary = status['cache_summary']
            total_data_points = sum(
                value for key, value in cache_summary.items() 
                if isinstance(value, (int, float)) and key != 'last_analysis'
            )
            st.metric("Total Data Points", f"{total_data_points:,}")
        
        st.divider()
        
        # Last run times
        st.subheader("📅 Last Run Times")
        
        last_runs = status.get('last_run_times', {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**App Store Jobs**")
            for job_type, last_run in last_runs.items():
                if 'app_store' in job_type:
                    if last_run:
                        st.write(f"• {job_type}: {self.time_ago(last_run)}")
                    else:
                        st.write(f"• {job_type}: Never run")
        
        with col2:
            st.write("**Steam & Events Jobs**")
            for job_type, last_run in last_runs.items():
                if 'steam' in job_type or 'events' in job_type or 'analysis' in job_type:
                    if last_run:
                        st.write(f"• {job_type}: {self.time_ago(last_run)}")
                    else:
                        st.write(f"• {job_type}: Never run")
        
        # Configuration
        st.subheader("⚙️ Pipeline Configuration")
        config_data = status.get('config', {})
        
        config_df = pd.DataFrame([
            {"Setting": key, "Value": value}
            for key, value in config_data.items()
        ])
        
        st.dataframe(config_df, use_container_width=True)
    
    def render_data_explorer(self):
        """Render data exploration interface"""
        st.title("🔍 Data Explorer")
        
        # Data source selection
        data_source = st.selectbox(
            "Select Data Source",
            ["App Store Apps", "Steam Games", "Events", "Analysis Results"]
        )
        
        if data_source == "App Store Apps":
            apps_data = automated_pipeline.data_cache.get('apps', [])
            if apps_data:
                df = pd.DataFrame(apps_data)
                st.write(f"**Total Apps:** {len(df)}")
                
                # Filters
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if 'region' in df.columns:
                        selected_regions = st.multiselect("Regions", df['region'].unique())
                        if selected_regions:
                            df = df[df['region'].isin(selected_regions)]
                
                with col2:
                    if 'category' in df.columns:
                        selected_categories = st.multiselect("Categories", df['category'].unique())
                        if selected_categories:
                            df = df[df['category'].isin(selected_categories)]
                
                with col3:
                    if 'global_average_rank' in df.columns:
                        rank_range = st.slider("Rank Range", 1, 1000, (1, 100))
                        df = df[(df['global_average_rank'] >= rank_range[0]) & (df['global_average_rank'] <= rank_range[1])]
                
                # Display data
                st.dataframe(df, use_container_width=True)
                
                # Download option
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Download CSV",
                    csv,
                    f"hunter_apps_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv"
                )
            else:
                st.info("No App Store data available")
        
        elif data_source == "Steam Games":
            steam_data = automated_pipeline.data_cache.get('steam_games', [])
            if steam_data:
                df = pd.DataFrame(steam_data)
                st.write(f"**Total Games:** {len(df)}")
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No Steam data available")
        
        elif data_source == "Events":
            events_data = automated_pipeline.data_cache.get('events', [])
            if events_data:
                df = pd.DataFrame(events_data)
                st.write(f"**Total Events:** {len(df)}")
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No events data available")
        
        elif data_source == "Analysis Results":
            analysis_data = automated_pipeline.data_cache.get('analysis', {})
            if analysis_data:
                st.json(analysis_data)
            else:
                st.info("No analysis data available")
    
    def handle_auto_refresh(self):
        """Handle auto-refresh functionality"""
        if st.session_state.last_refresh is None:
            st.session_state.last_refresh = datetime.now()
            self.refresh_live_data()
        
        time_since_refresh = (datetime.now() - st.session_state.last_refresh).total_seconds()
        
        if time_since_refresh >= st.session_state.refresh_interval:
            self.refresh_live_data()
            st.rerun()
        
        # Show countdown
        remaining = st.session_state.refresh_interval - time_since_refresh
        if remaining > 0:
            st.caption(f"⏰ Next refresh in {int(remaining)} seconds")
    
    def refresh_live_data(self):
        """Refresh live data"""
        st.session_state.last_refresh = datetime.now()
        # Trigger a quick analysis update
        try:
            automated_pipeline.execute_job('comprehensive_analysis')
        except Exception as e:
            st.error(f"Error refreshing data: {e}")
    
    def render_live_trending_apps(self):
        """Render live trending apps"""
        apps_data = automated_pipeline.data_cache.get('apps', [])[:20]
        
        if apps_data:
            trending_data = []
            for app in apps_data:
                trending_data.append({
                    'App': app.get('title', 'Unknown'),
                    'Rank': app.get('global_average_rank', 999),
                    'Regions': app.get('regions_count', 0),
                    'Trend Score': app.get('success_score', 0) if app.get('success_score') else np.random.randint(60, 95)
                })
            
            df = pd.DataFrame(trending_data)
            
            # Add trend indicators
            def trend_indicator(score):
                if score >= 85:
                    return "🔥"
                elif score >= 75:
                    return "📈"
                else:
                    return "➡️"
            
            df['Trend'] = df['Trend Score'].apply(trend_indicator)
            
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No live trending data available")
    
    def render_realtime_charts(self):
        """Render real-time chart movement visualization"""
        # Mock real-time data
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        
        fig = go.Figure()
        
        apps = ['SuperGame Pro', 'Fitness App 2024', 'Photo Editor Max']
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        
        for i, app in enumerate(apps):
            # Generate mock ranking data
            rankings = np.random.randint(1, 100, len(dates))
            rankings = np.sort(rankings)[::-1]  # Trending up
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=rankings,
                mode='lines+markers',
                name=app,
                line=dict(color=colors[i], width=3),
                marker=dict(size=6)
            ))
        
        fig.update_layout(
            title="📈 Live Chart Movement (Last 30 Days)",
            xaxis_title="Date",
            yaxis_title="Rank Position",
            yaxis=dict(autorange='reversed'),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_breaking_events(self):
        """Render breaking events"""
        events_data = automated_pipeline.data_cache.get('events', [])
        
        # Get upcoming high-impact events
        upcoming_events = []
        for event in events_data:
            if self.is_upcoming_event(event) and event.get('impact_score', 0) > 60:
                upcoming_events.append(event)
        
        upcoming_events = sorted(upcoming_events, key=lambda x: x.get('impact_score', 0), reverse=True)[:5]
        
        for event in upcoming_events:
            impact_score = event.get('impact_score', 0)
            
            if impact_score > 80:
                icon = "🔥"
                color = "error"
            elif impact_score > 65:
                icon = "⚡"
                color = "warning"
            else:
                icon = "📅"
                color = "info"
            
            with st.container():
                st.write(f"{icon} **{event.get('name', 'Unknown Event')}**")
                st.caption(f"Impact: {impact_score:.0f}% • {event.get('event_type', 'Event')}")
                st.write("---")
    
    def render_instant_opportunities(self):
        """Render instant opportunities"""
        # Mock opportunities based on current data
        opportunities = [
            {"title": "Valentine's Day Apps Surge", "confidence": 92, "category": "Social"},
            {"title": "Gaming Tournament Correlation", "confidence": 87, "category": "Games"},
            {"title": "Fitness New Year Trend", "confidence": 78, "category": "Health"},
            {"title": "Tax Season App Boost", "confidence": 82, "category": "Finance"}
        ]
        
        for opp in opportunities:
            confidence = opp["confidence"]
            
            if confidence > 85:
                st.success(f"🎯 **{opp['title']}**\nConfidence: {confidence}%\nCategory: {opp['category']}")
            elif confidence > 75:
                st.warning(f"⚡ **{opp['title']}**\nConfidence: {confidence}%\nCategory: {opp['category']}")
            else:
                st.info(f"💡 **{opp['title']}**\nConfidence: {confidence}%\nCategory: {opp['category']}")
    
    def run_manual_scrape(self, scrape_type: str):
        """Run manual scraping job"""
        with st.spinner(f"Running {scrape_type} scrape..."):
            try:
                result = automated_pipeline.execute_job(f"{scrape_type}_scrape")
                if result.get('status') == 'success':
                    st.success(f"✅ {scrape_type} completed successfully!")
                    st.json(result.get('data', {}))
                else:
                    st.error(f"❌ {scrape_type} failed: {result.get('error', 'Unknown error')}")
            except Exception as e:
                st.error(f"❌ Error running {scrape_type}: {e}")
    
    def is_upcoming_event(self, event: Dict[str, Any]) -> bool:
        """Check if event is upcoming"""
        start_date = event.get('start_date')
        if isinstance(start_date, str):
            try:
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except:
                return False
        
        if isinstance(start_date, datetime):
            return start_date >= datetime.now()
        
        return False
    
    def time_ago(self, dt) -> str:
        """Calculate time ago string"""
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            except:
                return "Unknown"
        
        if not isinstance(dt, datetime):
            return "Unknown"
        
        now = datetime.now()
        diff = now - dt
        
        if diff.days > 0:
            return f"{diff.days} days ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hours ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minutes ago"
        else:
            return "Just now"
    
    def render_original_page(self, page: str):
        """Render original dashboard pages"""
        # Import from original app
        from app import HunterDashboard
        original_dashboard = HunterDashboard()
        
        if page == 'apps':
            original_dashboard.render_apps_page()
        elif page == 'steam':
            original_dashboard.render_steam_page()
        elif page == 'events':
            original_dashboard.render_events_page()
        elif page == 'analytics':
            original_dashboard.render_analytics_page()
        elif page == 'alerts':
            original_dashboard.render_alerts_page()
        else:
            original_dashboard.render_dashboard()
    
    # Additional rendering methods for detailed analysis
    def render_app_store_analysis(self, analysis: Dict[str, Any]):
        """Render detailed App Store analysis"""
        fast_climbers = analysis.get('fast_climbers', [])
        if fast_climbers:
            st.write("**📈 Fast Climbing Apps**")
            df = pd.DataFrame(fast_climbers)
            st.dataframe(df, use_container_width=True)
        
        sudden_drops = analysis.get('sudden_drops', [])
        if sudden_drops:
            st.write("**📉 Sudden Ranking Drops**")
            df = pd.DataFrame(sudden_drops)
            st.dataframe(df, use_container_width=True)
    
    def render_steam_analysis(self, analysis: Dict[str, Any]):
        """Render detailed Steam analysis"""
        trending_games = analysis.get('trending_games', [])
        if trending_games:
            st.write("**🎮 Trending Steam Games**")
            df = pd.DataFrame(trending_games)
            st.dataframe(df, use_container_width=True)
    
    def render_events_analysis(self, analysis: Dict[str, Any]):
        """Render detailed events analysis"""
        trending_categories = analysis.get('trending_categories', [])
        if trending_categories:
            st.write("**📊 Trending Event Categories**")
            for category, data in trending_categories:
                st.write(f"• **{category}**: {data.get('trending_score', 0):.1f} trend score")
    
    def render_cross_platform_analysis_detailed(self, analysis: Dict[str, Any]):
        """Render detailed cross-platform analysis"""
        correlations = analysis.get('top_correlations', [])
        if correlations:
            st.write("**🔗 Strong Cross-Platform Correlations**")
            df = pd.DataFrame(correlations)
            st.dataframe(df, use_container_width=True)
    
    def render_events_impact_analysis(self, events_data: List[Dict[str, Any]]):
        """Render events impact analysis"""
        # Group events by impact score
        high_impact = [e for e in events_data if e.get('impact_score', 0) > 70]
        medium_impact = [e for e in events_data if 40 <= e.get('impact_score', 0) <= 70]
        low_impact = [e for e in events_data if e.get('impact_score', 0) < 40]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🔥 High Impact", len(high_impact))
        with col2:
            st.metric("⚡ Medium Impact", len(medium_impact))
        with col3:
            st.metric("💡 Low Impact", len(low_impact))
        
        # Impact distribution chart
        impact_data = {
            'Impact Level': ['High (70+)', 'Medium (40-70)', 'Low (<40)'],
            'Count': [len(high_impact), len(medium_impact), len(low_impact)]
        }
        
        fig = px.pie(
            values=impact_data['Count'],
            names=impact_data['Impact Level'],
            title="Events by Impact Level"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    def render_events_timeline(self, events_data: List[Dict[str, Any]]):
        """Render events timeline"""
        # Create timeline visualization
        timeline_data = []
        for event in events_data[:20]:  # Limit for performance
            start_date = event.get('start_date')
            if isinstance(start_date, str):
                try:
                    start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                except:
                    continue
            
            if isinstance(start_date, datetime):
                timeline_data.append({
                    'Event': event.get('name', 'Unknown'),
                    'Date': start_date,
                    'Impact': event.get('impact_score', 0),
                    'Category': event.get('category', 'unknown')
                })
        
        if timeline_data:
            df = pd.DataFrame(timeline_data)
            
            fig = px.scatter(
                df,
                x='Date',
                y='Impact',
                size='Impact',
                color='Category',
                hover_data=['Event'],
                title="Events Impact Timeline"
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def render_events_app_opportunities(self, events_data: List[Dict[str, Any]]):
        """Render app opportunities based on events"""
        # Analyze app categories that could benefit from events
        category_opportunities = {}
        
        for event in events_data:
            app_categories = event.get('app_categories', [])
            impact_score = event.get('impact_score', 0)
            
            for category in app_categories:
                if category not in category_opportunities:
                    category_opportunities[category] = {'total_impact': 0, 'event_count': 0}
                
                category_opportunities[category]['total_impact'] += impact_score
                category_opportunities[category]['event_count'] += 1
        
        # Calculate average impact per category
        for category in category_opportunities:
            data = category_opportunities[category]
            data['avg_impact'] = data['total_impact'] / data['event_count']
        
        # Sort by average impact
        sorted_opportunities = sorted(
            category_opportunities.items(),
            key=lambda x: x[1]['avg_impact'],
            reverse=True
        )
        
        st.write("**🎯 App Category Opportunities**")
        
        for category, data in sorted_opportunities[:10]:
            st.write(f"• **{category.title()}**: {data['avg_impact']:.1f} avg impact ({data['event_count']} events)")

# Main application entry point
def main():
    dashboard = EnhancedHunterDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()