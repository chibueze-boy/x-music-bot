# ============================================================
#  Daily Prep — generates all posts and schedules them to Buffer
#  Run once each morning BEFORE the posting window opens.
#  e.g. cron: 0 7 * * * python /path/to/x_music_bot/daily_prep.py
# ============================================================

import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from config import POSTS_PER_DAY as _RAW_PPD, TIMEZONE, LOG_FILE, OUTPUT_CSV

# Hard cap — keep the daily total below Buffer free-plan limits
MAX_POSTS_PER_DAY = 99
POSTS_PER_DAY = min(_RAW_PPD, MAX_POSTS_PER_DAY)
from generator import generate_batch
from scheduler import attach_times, save_to_csv
from buffer_poster import schedule_batch, list_channels

os.makedirs("logs", exist_ok=True)
os.makedirs("output", exist_ok=True)
os.makedirs("media", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("daily_prep")


def run():
    tz = ZoneInfo(TIMEZONE)
    today = datetime.now(tz)
    logger.info(f"=== Daily prep started for {today.strftime('%A %d %B %Y')} ===")
    logger.info(f"Target: {POSTS_PER_DAY} posts from 8am–5pm via Buffer")

    # 0. Optional: list connected Buffer channels on first run
    # Uncomment below to print your channel IDs (run once to find BUFFER_CHANNEL_ID)
    list_channels()

    # 1. Generate tweet texts via Groq
    logger.info("Step 1/4 — Generating tweet content with Groq...")
    posts = generate_batch(count=POSTS_PER_DAY)
    for i, p in enumerate(posts):
        p["id"] = i

    # 2. Build schedule
    logger.info("Step 2/3 — Building posting schedule (8am–5pm)...")
    posts = attach_times(posts, date=today)

    # 3. Send everything to Buffer
    logger.info("Step 3/3 — Scheduling all posts to Buffer...")
    success, fail = schedule_batch(posts)

    # 5. Save local CSV backup
    save_to_csv(posts, OUTPUT_CSV)

    logger.info(f"=== Done! {success} posts scheduled on Buffer, {fail} failed ===")
    logger.info(f"Local backup saved to {OUTPUT_CSV}")
    if fail > 0:
        logger.warning(f"{fail} posts failed — check logs and re-run for those slots.")


if __name__ == "__main__":
    run()
