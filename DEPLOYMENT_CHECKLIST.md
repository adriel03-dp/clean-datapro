# Deployment Checklist

## Before You Start

- [ ] Your code is on GitHub (adriel03-dp/clean-datapro)
- [ ] Main branch has all latest changes pushed

## Step 1: Deploy Frontend (Streamlit Cloud)

- [ ] Create Streamlit account at streamlit.io/cloud
- [ ] Click "New App"
- [ ] Select repository: adriel03-dp/clean-datapro
- [ ] Set main file: frontend/streamlit_app.py
- [ ] Wait for deployment (2-3 minutes)
- [ ] Copy your Streamlit URL (like: https://clean-datapro-xxx.streamlit.app)

## Step 2: Deploy Backend (Railway)

- [ ] Create Railway account at railway.app
- [ ] Click "New Project"
- [ ] Select "Deploy from GitHub repo"
- [ ] Select clean-datapro repo
- [ ] Wait for deployment
- [ ] Copy your Railway URL (like: https://clean-datapro-prod.up.railway.app)

## Step 3: Connect Them

- [ ] Go back to Streamlit Cloud
- [ ] Click your app
- [ ] Click menu (⋯) → Settings → Secrets
- [ ] Add: `CLEAN_DATAPRO_BACKEND="[your Railway URL]"`
- [ ] Click Save
- [ ] Reboot app

## Step 4: Test

- [ ] Visit your Streamlit URL
- [ ] Upload a CSV file
- [ ] Click "Process & Clean"
- [ ] Check if it works!

## All Done! 🎉

Your site is now live at: [Your Streamlit URL]
