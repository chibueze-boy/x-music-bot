# ============================================================
# RSS Listener — polls configured RSS feeds, generates tweet text,
# and records activity in an SQLite database.
# ============================================================

import time
import logging
import sqlite3
import re
import argparse
from datetime import datetime

import feedparser

from config import RSS_FEEDS, RSS_POLL_INTERVAL, SQLITE_DB, MAX_TWEET_LENGTH

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS rss_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_url TEXT,
    entry_id TEXT UNIQUE,
    title TEXT,
    link TEXT,
    summary TEXT,
    tweet_text TEXT,
    posted INTEGER DEFAULT 0,
    created_at TEXT
);
"""


def init_db(path: str):
    conn = sqlite3.connect(path)
    conn.execute(CREATE_TABLE_SQL)
    conn.commit()
    return conn


def clean_html(text: str) -> str:
    if not text:
        return ""
    # remove HTML tags
    clean = re.sub(r"<[^>]+>", "", text)
    # collapse whitespace
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def generate_tweet_text(title: str, summary: str, link: str) -> str:
    parts = [title]
    if summary:
        parts.append("—")
        parts.append(summary)
    parts.append(link)
    text = " ".join(parts)
    if len(text) > MAX_TWEET_LENGTH:
        # trim without cutting words
        allowed = MAX_TWEET_LENGTH - len(link) - 4
        summary_trim = summary[:allowed].rsplit(' ', 1)[0]
        text = f"{title} — {summary_trim}... {link}"
    return text


def process_feed_once(conn, feed_url: str):
    logger.info(f"Fetching feed: {feed_url}")
    d = feedparser.parse(feed_url)
    entries = d.get('entries', [])
    cur = conn.cursor()
    new_count = 0
    for entry in entries:
        entry_id = entry.get('id') or entry.get('guid') or entry.get('link')
        if not entry_id:
            continue
        # check if exists
        cur.execute("SELECT 1 FROM rss_posts WHERE entry_id = ?", (entry_id,))
        if cur.fetchone():
            continue
        title = entry.get('title', '').strip()
        summary = clean_html(entry.get('summary', '') or entry.get('description', ''))
        link = entry.get('link', '')
        # create short summary (first 200 chars)
        summary_short = (summary[:200].rsplit(' ', 1)[0] + '...') if len(summary) > 200 else summary
        tweet = generate_tweet_text(title, summary_short, link)
        now = datetime.utcnow().isoformat() + 'Z'
        cur.execute(
            """INSERT INTO rss_posts (feed_url, entry_id, title, link, summary, tweet_text, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (feed_url, entry_id, title, link, summary_short, tweet, now),
        )
        conn.commit()
        new_count += 1
        logger.info(f"New article recorded: {title}")
    return new_count


def main(loop: bool = True):
    conn = init_db(SQLITE_DB)
    try:
        while True:
            total_new = 0
            for feed in RSS_FEEDS:
                try:
                    new = process_feed_once(conn, feed)
                    total_new += new
                except Exception as e:
                    logger.warning(f"Failed to process feed {feed}: {e}")
            if total_new:
                logger.info(f"Fetched and recorded {total_new} new articles")
            else:
                logger.info("No new articles found")
            if not loop:
                break
            time.sleep(RSS_POLL_INTERVAL)
    finally:
        conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='RSS listener for music news')
    parser.add_argument('--once', action='store_true', help='Run a single poll and exit')
    args = parser.parse_args()
    main(loop=not args.once)
