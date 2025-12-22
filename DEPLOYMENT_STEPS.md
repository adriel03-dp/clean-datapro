# Beginner's Deployment Guide - Step by Step

## Part 1: Deploy Frontend to Streamlit Cloud (5 minutes)

### Step 1: Make sure your code is on GitHub
```bash
cd C:\Users\lenovo\Desktop\clean-datapro
git add .
git commit -m "Ready for deployment"
git push origin main
```

### Step 2: Go to Streamlit Cloud
1. Open https://streamlit.io/cloud
2. Click **"Sign in with GitHub"**
3. Give it permission to access your GitHub

### Step 3: Deploy your app
1. Click **"New App"**
2. Fill in:
   - **Repository**: `adriel03-dp/clean-datapro`
   - **Branch**: `main`
   - **Main file path**: `frontend/streamlit_app.py`
3. Click **"Deploy"**

**That's it!** Your frontend will be live in 2-3 minutes at a URL like:
`https://clean-datapro-xxx.streamlit.app`

---

## Part 2: Deploy Backend to Railway (10 minutes)

### Step 1: Create Railway Account
1. Go to https://railway.app
2. Click **"Start Free"**
3. Sign in with GitHub
4. Give it permission

### Step 2: Deploy Backend
1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Find and select `adriel03-dp/clean-datapro`
4. After connecting, click **"Add service"**
5. Select **"From Dockerfile"** or **"Python"**

### Step 3: Configure the Backend
1. Click on your project
2. Click **"Variables"** on the left
3. Add this environment variable:
   ```
   MONGODB_URI=mongodb://localhost:27017/cleandatapro
   ```
4. Click **"Deploy"**

### Step 4: Get your Backend URL
1. Click your deployment
2. Look for **"Domain"** section
3. Copy the URL (looks like: `https://clean-datapro-prod.up.railway.app`)

---

## Part 3: Connect Frontend to Backend (5 minutes)

### Step 1: Add Backend URL to Streamlit
1. Go to https://streamlit.io/cloud
2. Click your deployed app
3. Click the **menu (⋯)** in the top right
4. Select **"Settings"**
5. Click **"Secrets"** on the left
6. Add this line:
   ```
   CLEAN_DATAPRO_BACKEND="https://your-railway-url.up.railway.app"
   ```
   (Replace with your actual Railway URL from Part 2 Step 4)
7. Click **"Save"**

### Step 2: Restart Streamlit
1. Go back to your app
2. Click the **menu (⋯)**
3. Select **"Reboot app"**

**Done!** Your app is now deployed and connected!

---

## Testing Your Deployment

1. Go to your Streamlit app URL
2. Upload a CSV file
3. Click **"Process & Clean"**
4. It should work! (It will connect to your Railway backend)

---

## Troubleshooting

### App shows error about backend
- **Problem**: Cannot connect to backend
- **Solution**: Double-check the `CLEAN_DATAPRO_BACKEND` URL in Streamlit secrets
- Check that it's exactly right and reboot the app

### Backend takes long time to respond
- **Problem**: Railway might be spinning up
- **Solution**: Wait 30 seconds and try again. Railway free tier sleeps when inactive

### MongoDB error
- **Problem**: Backend can't save history
- **Solution**: You can ignore this for now. The cleaning still works, just doesn't save history

---

## Optional: Better MongoDB Setup (For Production)

If you want to save processing history:

1. Go to https://www.mongodb.com/cloud/atlas
2. Sign up (free tier)
3. Create a cluster
4. Get your connection string
5. In Railway, update `MONGODB_URI` with your MongoDB Atlas connection string

---

## Your URLs After Deployment

- **Frontend**: `https://clean-datapro-xxx.streamlit.app`
- **Backend API**: `https://clean-datapro-prod.up.railway.app`
- **API Docs**: `https://clean-datapro-prod.up.railway.app/docs`

---

## Need Help?

If something doesn't work:
1. Check the deployment logs:
   - Streamlit: Click "Manage app" → "View logs"
   - Railway: Click your service → "Logs" tab
2. Look for error messages
3. Try redeploying

**Common issues are usually just typos in URLs or environment variables!**
