# ============================================================
#  run_poster.py — NOT needed when using Buffer!
#
#  Buffer handles all posting automatically at the scheduled
#  times you set during daily_prep.py.
#
#  This file is kept only as a utility to:
#    1. Check today's scheduled posts on Buffer
#    2. Manually trigger a single post if needed
# ============================================================

import logging
import os
import requests
from config import BUFFER_API_KEY, BUFFER_CHANNEL_ID, BUFFER_API_URL, LOG_FILE

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("run_poster")

HEADERS = {
    "Authorization": f"Bearer {BUFFER_API_KEY}",
    "Content-Type": "application/json",
}

QUERY_SCHEDULED = """
query GetScheduledPosts($channelId: String!) {
  posts(
    first: 60,
    input: {
      filter: {
        status: [scheduled],
        channelIds: [$channelId]
      }
    }
  ) {
    edges {
      node {
        id
        text
        dueAt
        status
      }
    }
    pageInfo { hasNextPage }
  }
}
"""


def check_scheduled():
    """Print all posts currently queued in Buffer for your channel."""
    try:
        r = requests.post(
            BUFFER_API_URL,
            json={"query": QUERY_SCHEDULED, "variables": {"channelId": BUFFER_CHANNEL_ID}},
            headers=HEADERS,
            timeout=15,
        )
        r.raise_for_status()
        edges = r.json().get("data", {}).get("posts", {}).get("edges", [])
        logger.info(f"Found {len(edges)} scheduled posts in Buffer:")
        for e in edges:
            node = e["node"]
            logger.info(f"  [{node['dueAt']}] {node['text'][:70]}...")
        return edges
    except Exception as e:
        logger.error(f"Failed to fetch scheduled posts: {e}")
        return []


if __name__ == "__main__":
    print("\n=== Buffer Auto-Post Mode ===")
    print("Buffer handles posting automatically — no runner needed!")
    print("Checking your scheduled queue...\n")
    posts = check_scheduled()
    print(f"\nTotal queued: {len(posts)} posts")
    print("Buffer will publish them at their scheduled times automatically.")
