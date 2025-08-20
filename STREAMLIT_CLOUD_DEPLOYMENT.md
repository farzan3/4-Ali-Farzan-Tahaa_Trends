# 🚀 Deploying Hunter to Streamlit Cloud

This guide will help you deploy your Hunter app to Streamlit Cloud.

## 📋 Prerequisites

1. GitHub account
2. Streamlit Cloud account (free at https://share.streamlit.io/)
3. Your Hunter app code in a GitHub repository

## 🔧 Setup Steps

### 1. Prepare Your Repository

1. **Push your code to GitHub** (if not already done):
   ```bash
   git add .
   git commit -m "Prepare for Streamlit Cloud deployment"
   git push origin main
   ```

2. **Ensure these files are in your repository**:
   - `app_cloud.py` (cloud-optimized version)
   - `requirements-streamlit-cloud.txt` (lightweight dependencies)
   - `.streamlit/secrets.toml` (template for secrets)

### 2. Deploy to Streamlit Cloud

1. **Go to https://share.streamlit.io/**

2. **Click "New app"**

3. **Fill in the deployment form**:
   - **Repository**: Select your GitHub repository
   - **Branch**: `main` (or your preferred branch)
   - **Main file path**: `app_cloud.py`
   - **App URL**: Choose a custom URL (e.g., `your-username-hunter-app`)

4. **Click "Deploy!"**

### 3. Configure Secrets (Important!)

1. **Go to your app settings** (click the hamburger menu → Settings)

2. **Click on "Secrets"**

3. **Add the following secrets**:
   ```toml
   [general]
   JWT_SECRET = "your-super-secret-key-change-this"
   DATABASE_URL = "sqlite:///hunter_app.db"

   [auth]
   ADMIN_EMAIL = "admin@hunter.app"
   ADMIN_PASSWORD = "your-secure-password"

   [scraping]
   SCRAPER_DELAY = "1.0"
   USE_PROXY = "false"
   MAX_RETRIES = "3"
   ```

4. **Click "Save"**

### 4. Update Requirements (If Needed)

If you want to use the lightweight version, rename your requirements file:

1. **In your GitHub repository**:
   - Rename `requirements-streamlit-cloud.txt` to `requirements.txt`
   - Or update your existing `requirements.txt` with the lightweight dependencies

2. **Commit and push**:
   ```bash
   git add requirements.txt
   git commit -m "Update requirements for Streamlit Cloud"
   git push origin main
   ```

## 🎯 What's Different in the Cloud Version?

The `app_cloud.py` file includes several modifications for cloud deployment:

### ✅ Cloud-Friendly Features:
- **Simplified authentication** (no complex database dependencies)
- **Demo data** (works without external databases)
- **Lightweight dependencies** (no heavy ML libraries that might cause deployment issues)
- **In-memory storage** (using Streamlit session state)
- **Simplified navigation** (optimized for cloud performance)

### 🚫 Removed for Cloud:
- Heavy ML libraries (torch, transformers, opencv)
- Complex database operations
- File system dependencies
- Selenium (browser automation)

## 🔐 Login Credentials

**Default demo credentials:**
- Email: `admin@hunter.app`
- Password: `admin123`

*Make sure to change these in your secrets configuration for production use!*

## 🛠️ Troubleshooting

### Common Issues:

1. **"Module not found" errors**:
   - Check your `requirements.txt` file
   - Ensure all imports in `app_cloud.py` are available in your requirements

2. **App won't start**:
   - Check the logs in Streamlit Cloud dashboard
   - Verify your main file path is correct (`app_cloud.py`)

3. **Authentication issues**:
   - Verify your secrets are configured correctly
   - Check that `ADMIN_EMAIL` and `ADMIN_PASSWORD` match your login attempts

4. **Performance issues**:
   - The cloud version uses demo data to avoid heavy database operations
   - Consider upgrading your Streamlit Cloud plan for better performance

### 📧 Getting Help:

- **Streamlit Community**: https://discuss.streamlit.io/
- **Documentation**: https://docs.streamlit.io/streamlit-community-cloud
- **GitHub Issues**: Create an issue in your repository

## 🎉 Success!

Once deployed, your Hunter app will be available at:
`https://share.streamlit.io/your-username/your-repo-name/main/app_cloud.py`

## 🔄 Making Updates

To update your deployed app:

1. **Make changes to your code**
2. **Commit and push to GitHub**:
   ```bash
   git add .
   git commit -m "Update app"
   git push origin main
   ```
3. **Streamlit Cloud will automatically redeploy** (usually takes 1-2 minutes)

## 📈 Next Steps

1. **Customize the app** with your branding
2. **Add real data sources** (if needed)
3. **Configure custom domain** (available in paid plans)
4. **Set up monitoring** and analytics
5. **Share your app** with users!

---

**🎯 Your Hunter app is now live on the web! 🚀**