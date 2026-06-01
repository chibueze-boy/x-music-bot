# Deploying to Render

This guide explains how to deploy the X Music Bot to [Render](https://render.com).

## Prerequisites

- Render account (free tier works)
- GitHub repository with this code
- Buffer API key and Channel ID
- Groq API key

## Setup Steps

### 1. Connect GitHub to Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" and select "Background Worker"
3. Select "Build and deploy from a Git repository"
4. Connect your GitHub account and select this repository

### 2. Configure the Service

**Service Details:**
- **Name:** music-bot (or your preferred name)
- **Region:** Choose closest to your data center
- **Branch:** main (or your deployment branch)

**Build Settings:**
- **Runtime:** Python 3.11
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python daily_prep.py`

### 3. Set Environment Variables

In the Render dashboard, go to **Environment** and add:

```
BUFFER_API_KEY=<your_buffer_api_key>
BUFFER_CHANNEL_ID=<your_buffer_channel_id>
GROQ_API_KEY=<your_groq_api_key>
```

Get these from:
- **Buffer:** https://publish.buffer.com/settings/api
- **Groq:** https://console.groq.com/keys

### 4. File Structure for Deployment

Ensure these files exist in your repository:

```
Procfile              # Render uses this to run the worker
requirements.txt      # All Python dependencies
config.py             # Reads from environment variables
daily_prep.py         # Main entry point
```

## How It Works

- Render will run `python daily_prep.py` once on service startup
- The bot generates 90 posts and schedules them to Buffer
- Posts are automatically published by Buffer between 8am–5pm

## Scheduling Daily Runs

To run the bot every day at a specific time:

1. In Render dashboard, go to **Settings**
2. Under "Build Hooks", create a new hook
3. Use an external scheduler like [EasyCron](https://www.easycron.com/) or GitHub Actions to trigger the hook daily

**Example with GitHub Actions:**
Create `.github/workflows/daily-deploy.yml`:

```yaml
name: Daily Deploy

on:
  schedule:
    - cron: '0 7 * * *'  # 7am UTC daily

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Render Build Hook
        run: |
          curl -X POST https://api.render.com/deploy/YOUR_BUILD_HOOK_ID
```

Replace `YOUR_BUILD_HOOK_ID` with your actual hook ID from Render.

## Monitoring

- Check logs in Render dashboard: **Logs** tab
- Logs are saved locally to `logs/bot.log`
- CSV schedule saved to `output/scheduled_posts.csv`
- SQLite database for RSS tracking: `output/rss_posts.db`

## Troubleshooting

**Bot runs but posts don't appear:**
- Check that `BUFFER_API_KEY` and `BUFFER_CHANNEL_ID` are correct
- Verify Buffer API access at https://publish.buffer.com/settings/api

**Groq generation fails:**
- Verify `GROQ_API_KEY` is valid and has remaining quota
- Check Groq console: https://console.groq.com/

**Files not persisting:**
- Render's free tier has ephemeral storage. For persistent output:
  - Attach a PostgreSQL database, or
  - Save to external storage (AWS S3, etc.)

## Notes

- Each deploy runs the bot once
- For continuous 24/7 operation, pair with a job scheduler
- Render free tier may be sufficient for daily runs
- Upgrade to paid tier for guaranteed uptime if needed
