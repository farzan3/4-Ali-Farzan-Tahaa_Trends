# Task: Build "Hunter App/Game Discovery SaaS Platform"

## Vision
A SaaS platform that tracks global App Store & Steam data, links them with web-based trends/events, and uses analytics + ML to flag potential "hit" apps/games before they peak. Users can access via a secure web dashboard (multi-tenant SaaS) with alerts, reports, and APIs.

---

## System Goals
1. Scrape & ingest **App Store top charts** (all countries/categories).  
2. Scrape & ingest **Steam upcoming/trending games**.  
3. Scrape & ingest **web trends/events** (holidays, movies, sports, seasonal events).  
4. Store data in scalable DB (start SQLite for MVP, later PostgreSQL/BigQuery).  
5. Provide analytics:  
   - Chart ranking velocity  
   - Review velocity & sentiment  
   - Monetization (IAP/subscription patterns)  
   - Event & seasonal matching  
   - Steam correlation  
   - Clone/copy detection (icons, titles, descriptions, themes)  
6. Provide predictive scoring:  
   - Weighted model + ML-based classifier (success probability 0–100)  
   - Continually retrained with historical success data  
7. Deliver insights:  
   - Web dashboard (multi-tenant SaaS)  
   - Alerts (email/Slack/Discord) when a new potential hit is detected  
   - Public/private API for programmatic access  
   - Reports exportable to CSV/PDF  

---

## Functional Requirements

### Data Collection
- Continuous scraping pipeline with retries + rotating proxies.  
- Deduplication across countries & categories.  
- Support historical data storage (for trend modeling).  
- Event scrapers: holidays, sports schedules, movie releases, cultural events.  

### Data Processing
- **Ranking Analytics**: velocity detection (fast climbers, sudden drops).  
- **Review Analysis**: NLP sentiment (fast/lightweight), review velocity.  
- **Monetization Analysis**: detect IAP packs, subscriptions, price tiers.  
- **Clone Detection**:  
  - Icon similarity (image embeddings with CLIP/OpenCV).  
  - Text similarity (Sentence Transformers, TF-IDF).  
  - Cluster detection (multiple similar apps released close together).  
- **Event Matching**: semantic linking between app themes & upcoming events.  
- **Steam Correlation**: match App Store games with trending Steam titles.  

### Predictive Engine
- Weighted scoring rules for MVP.  
- ML model trained on historical data:  
  - Input: chart velocity, reviews, monetization, event match, clone signals.  
  - Output: probability of success.  
- Self-improving model (periodic retraining).  

### Dashboard (SaaS UI)
- Multi-tenant login (auth + roles).  
- Leaderboard: hottest apps/games globally.  
- Filters: country, category, event type, genre.  
- App detail page: chart graph, reviews, monetization, clone detection, event linkage.  
- Events tab: upcoming global events with linked apps.  
- Alerts/Watchlist: “Notify me if X game starts trending.”  

### APIs
- REST/GraphQL API for external clients.  
- Endpoints:  
  - `/apps/top` → top apps with success scores  
  - `/apps/{id}` → detailed app analytics  
  - `/events/upcoming` → events data  
  - `/alerts` → subscribe to notifications  

---

## Technical Requirements
- **Backend**: Python (scraping, ML), Node.js/Go (API layer optional).  
- **Database**: Start with SQLite (MVP), migrate to PostgreSQL/BigQuery.  
- **Storage**: S3/Blob for raw assets (icons, review dumps).  
- **Data Pipeline**: Airflow/Prefect for orchestration (or Cron jobs MVP).  
- **ML/NLP**: HuggingFace / Sentence Transformers / OpenCV / CLIP.  
- **Frontend**:  
  - MVP: Streamlit  
  - SaaS: Next.js/React with Tailwind + API integration  
- **Infra**: Dockerized services, deployable to AWS/GCP.  
- **Auth**: JWT-based multi-tenant login (Auth0/Supabase/Firebase).  
- **Monitoring**: Logging + metrics dashboard (Prometheus/Grafana).  

---

## Database Schema (Abstract)
- `apps` (id, app_store_id, title, developer, category, country, icon, description, release_date, rank, last_updated)  
- `reviews` (id, app_id, rating, review_text, sentiment, timestamp)  
- `iap` (id, app_id, product_name, price)  
- `events` (id, name, type, start_date, end_date, source)  
- `steam_games` (id, title, release_date, genre, tags, hype_score)  
- `clones` (id, app_id, similarity_score, matched_app_id)  
- `scores` (id, app_id, success_score, breakdown_json, model_version)  
- `users` (id, email, role, subscription_plan)  
- `alerts` (id, user_id, condition_json, status)  

---

## Success Metrics
- **Coverage**: % of App Store categories + Steam data ingested.  
- **Freshness**: Data updates within 1–3 hours globally.  
- **Accuracy**: Clone detection precision/recall.  
- **Prediction Quality**: % of flagged apps that later chart globally.  
- **Scalability**: Can handle 1M+ app records, multi-tenant SaaS load.  
