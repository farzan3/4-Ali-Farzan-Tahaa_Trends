# 🤖 Automated Scraping Guide - Hunter Platform

## ✅ **AUTOMATED PIPELINE IS NOW ACTIVE!**

**Status:** ✅ RUNNING  
**Dashboard:** http://localhost:8501  
**Started:** Just now  

---

## 📅 **SCRAPING SCHEDULE** (Now Active)

### 🍎 **App Store Scraping**
- **Full Comprehensive Scrape**: Every **6 hours**
  - All regions (US, UK, DE, FR, JP, CA, AU, etc.)
  - All categories (Games, Entertainment, Business, etc.)
  - All chart types (Top Free, Top Paid, Top Grossing)
  - **~10,000+ apps per run**

- **Quick Update Scrape**: Every **1 hour**
  - Priority regions and trending apps
  - **~500-1,000 apps per run**

### 🎮 **Steam Scraping**
- **Comprehensive Scrape**: Every **12 hours**
  - All game categories and genres
  - **~5,000+ games per run**

- **Quick Update Scrape**: Every **2 hours**
  - Trending and popular games
  - **~500 games per run**

### 📅 **Events Scraping**
- **Comprehensive Scrape**: Every **24 hours**
  - Global events, holidays, tech conferences
  - Gaming releases, seasonal trends
  - **~100-500 events per run**

- **Daily Update Scrape**: Every **6 hours**
  - Breaking events and updates
  - **~50-100 events per run**

### 🔍 **Data Processing**
- **Analysis & Insights**: Every **2 hours**
  - Process collected data
  - Generate success predictions
  - Update trending scores

- **System Maintenance**: 
  - Data cleanup: Every **24 hours**
  - Health checks: Every **12 hours**

---

## 🎯 **NEXT SCRAPING TIMES**

Based on the current time, here's when scrapers will run next:

**Immediate (within 1-2 hours):**
- App Store Quick Scrape (next: ~1 hour)
- Steam Quick Scrape (next: ~2 hours)
- Data Analysis (next: ~2 hours)

**Later today:**
- App Store Full Scrape (next: ~6 hours)
- Events Daily Scrape (next: ~6 hours)
- Steam Comprehensive (next: ~12 hours)

**Daily:**
- Events Comprehensive (next: ~24 hours)
- Data Cleanup (next: ~24 hours)

---

## 📊 **EXPECTED DATA GROWTH**

**Daily Collection Estimates:**
- **Apps**: 20,000-50,000 new/updated apps per day
- **Steam Games**: 2,000-5,000 new/updated games per day  
- **Events**: 200-1,000 new/updated events per day

**Weekly Growth:**
- Your database will grow from ~500 items to **50,000+ items** within a week
- After a month: **200,000+ total items**

---

## 🔧 **CONTROL THE PIPELINE**

### **Check Status:**
Go to: http://localhost:8501
- Look for "Pipeline Control" in the sidebar
- Status should show: "✅ Pipeline Active"

### **Stop/Start Pipeline:**
In the Enhanced Dashboard sidebar:
- Click "🛑 Stop Pipeline" to stop automated scraping
- Click "▶️ Start Pipeline" to restart automated scraping

### **Manual Scraping (Still Available):**
```bash
# Quick manual scrape (300-400 apps)
python get_tons_of_data.py
# Choose option 1

# Massive manual scrape (10,000+ apps)  
python get_tons_of_data.py
# Choose option 2
```

---

## 📈 **MONITORING DATA COLLECTION**

### **Real-time Dashboard:**
- Visit: http://localhost:8501
- Switch to "Live Dashboard" for real-time updates
- Enable "Auto Refresh" to see data as it comes in

### **Database Stats:**
Check current data counts:
```bash
python -c "
import sqlite3
conn = sqlite3.connect('hunter_app.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM apps')
apps = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM steam_games')  
steam = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM events')
events = cursor.fetchone()[0]
print(f'Apps: {apps:,} | Steam: {steam:,} | Events: {events:,} | Total: {apps+steam+events:,}')
"
```

### **View Recent Collections:**
Check what was scraped recently:
```bash
python -c "
import sqlite3
from datetime import datetime
conn = sqlite3.connect('hunter_app.db')
cursor = conn.cursor()
cursor.execute('SELECT title, country, last_updated FROM apps ORDER BY last_updated DESC LIMIT 5')
recent = cursor.fetchall()
print('Recent Apps:')
for i, (title, country, updated) in enumerate(recent, 1):
    print(f'  {i}. {title} ({country}) - {updated[:16]}')
"
```

---

## ⚠️ **IMPORTANT NOTES**

### **Performance Impact:**
- The automated pipeline runs in the background
- Minimal impact on dashboard performance
- Uses respectful delays between API calls

### **Data Storage:**
- Data is stored in SQLite database files
- Database will grow significantly over time
- Old data is automatically cleaned up after 30 days

### **Error Handling:**
- Pipeline automatically retries failed scrapes
- Continues running even if individual scrapers fail
- Check logs in the `logs/` directory for detailed information

### **Stopping the App:**
- Automated scraping stops when you close the enhanced app
- Data already collected remains in the database
- Restart `python start_enhanced.py` to resume automated scraping

---

## 🎉 **SUCCESS INDICATORS**

You'll know the automated scraping is working when:

1. **Dashboard shows increasing numbers** in the metrics
2. **New apps appear** in the "Live Trending Apps" section
3. **Database grows** when you check stats
4. **Recent apps** show current timestamps
5. **Pipeline status** remains "✅ Pipeline Active"

---

## 📞 **TROUBLESHOOTING**

**If pipeline shows "⏸️ Pipeline Stopped":**
- Click "▶️ Start Pipeline" in the sidebar
- Or restart: `python start_enhanced.py`

**If no new data appears after 2 hours:**
- Check your internet connection
- Check the logs in the `logs/` directory
- Restart the enhanced app

**If you see errors:**
- Most errors are temporary and auto-retry
- Check that all dependencies are installed
- Restart the app if problems persist

---

## 🚀 **ENJOY YOUR AUTOMATED DATA COLLECTION!**

Your Hunter platform is now collecting **thousands of apps, games, and events automatically**! 

The dashboard will show real, live data that updates throughout the day. Watch as your database grows from hundreds to hundreds of thousands of items over the coming weeks! 📈