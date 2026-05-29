# ============================================================
#  Scheduler — builds the 8am-5pm posting timetable
# ============================================================

import csv
import random
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from config import (
    POST_START_HOUR, POST_END_HOUR, POSTS_PER_DAY,
    TIMEZONE, OUTPUT_CSV
)

logger = logging.getLogger(__name__)


def build_schedule(date: datetime = None) -> list[datetime]:
    """
    Return a sorted list of POSTS_PER_DAY datetimes spread
    across POST_START_HOUR to POST_END_HOUR with natural jitter.
    """
    tz = ZoneInfo(TIMEZONE)
    if date is None:
        date = datetime.now(tz)

    start = date.replace(hour=POST_START_HOUR, minute=0, second=0, microsecond=0)
    end   = date.replace(hour=POST_END_HOUR,   minute=0, second=0, microsecond=0)

    # If the script is run late, adjust the start time to avoid scheduling in the past
    if start < datetime.now(tz):
        start = datetime.now(tz) + timedelta(minutes=5)
        # If the day's posting window is completely over, schedule for tomorrow instead
        if start >= end:
            start = date.replace(hour=POST_START_HOUR, minute=0, second=0, microsecond=0) + timedelta(days=1)
            end   = date.replace(hour=POST_END_HOUR,   minute=0, second=0, microsecond=0) + timedelta(days=1)

    window_seconds = int((end - start).total_seconds())
    base_interval  = window_seconds // POSTS_PER_DAY

    times = []
    for i in range(POSTS_PER_DAY):
        base = start + timedelta(seconds=i * base_interval)
        # Add ±90 second jitter so posts don't look robotic
        jitter = random.randint(-90, 90)
        post_time = base + timedelta(seconds=jitter)
        # Clamp to window
        post_time = max(start, min(end - timedelta(seconds=30), post_time))
        times.append(post_time)

    times.sort()
    return times


def attach_times(posts: list[dict], date: datetime = None) -> list[dict]:
    """Attach a scheduled datetime to each post."""
    schedule = build_schedule(date)
    # If fewer posts than slots, use as many slots as needed
    for i, post in enumerate(posts):
        slot = schedule[i] if i < len(schedule) else schedule[-1]
        post["scheduled_at"] = slot
    return posts


def save_to_csv(posts: list[dict], filepath: str = OUTPUT_CSV) -> None:
    """Export the scheduled posts to a CSV file."""
    fieldnames = [
        "scheduled_at", "topic", "tone", "subject",
        "text", "photo_path", "posted"
    ]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for post in posts:
            row = dict(post)
            row["scheduled_at"] = post["scheduled_at"].strftime("%Y-%m-%d %H:%M:%S %Z")
            row["posted"] = post.get("posted", False)
            writer.writerow(row)
    logger.info(f"Schedule saved to {filepath} ({len(posts)} posts)")


def load_from_csv(filepath: str = OUTPUT_CSV) -> list[dict]:
    """Load scheduled posts from CSV (for the poster to use)."""
    tz = ZoneInfo(TIMEZONE)
    posts = []
    try:
        with open(filepath, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                row["scheduled_at"] = datetime.strptime(
                    row["scheduled_at"], "%Y-%m-%d %H:%M:%S %Z"
                ).replace(tzinfo=tz)
                row["posted"] = row["posted"].lower() == "true"
                posts.append(row)
    except FileNotFoundError:
        logger.warning(f"No schedule file found at {filepath}")
    return posts


def mark_posted(filepath: str, post_index: int) -> None:
    """Mark a specific post as posted in the CSV."""
    posts = load_from_csv(filepath)
    if post_index < len(posts):
        posts[post_index]["posted"] = True
    save_to_csv(posts, filepath)
