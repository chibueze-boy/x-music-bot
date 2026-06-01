# ============================================================
#  Buffer Poster — schedules posts via Buffer's GraphQL API
#  Uses image URLs (now sourced via Sanity/GROQ)
# ============================================================

import logging
import requests
from datetime import datetime, timezone
from config import BUFFER_API_KEY, BUFFER_CHANNEL_ID, BUFFER_API_URL

logger = logging.getLogger(__name__)
HEADERS = {
    "Authorization": f"Bearer {BUFFER_API_KEY}",
    "Content-Type": "application/json",
}

MUTATION_TEXT = """
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    ... on PostActionSuccess {
      post { id text dueAt status }
    }
    ... on MutationError {
      message
    }
  }
}
"""

QUERY_CHANNELS = """
query {
  account {
    organizations {
      channels {
        id
        name
        service
      }
    }
  }
}
"""


def _run_query(query: str, variables: dict = None) -> dict:
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    r = requests.post(BUFFER_API_URL, json=payload, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()


def list_channels() -> list[dict]:
    """Print all Buffer-connected channels and their IDs."""
    try:
        data = _run_query(QUERY_CHANNELS)
        organizations = data.get("data", {}).get("account", {}).get("organizations", [])
        channels = []
        for org in organizations:
            for c in org.get("channels", []):
                channels.append(c)
                line = f"Channel: {c.get('service')} | {c.get('name')} | id={c.get('id')}"
                logger.info(line)
                print(line)
        return channels
    except Exception as e:
        logger.error(f"Failed to list channels: {e}")
        print(f"Failed to list channels: {e}")
        return []


def schedule_post(post: dict) -> bool:
    """
    Schedule a single post to Buffer.
    Expects `post['photo_path']` to be a public image URL (no upload step).
    """
    text = post.get("text", "")
    scheduled_at: datetime = post.get("scheduled_at")
    photo_path = post.get("photo_path")

    due_at = scheduled_at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    post_input = {
        "text": text,
        "channelId": BUFFER_CHANNEL_ID,
        "schedulingType": "automatic",
        "mode": "customScheduled",
        "dueAt": due_at,
    }

    if photo_path:
        # photo_path is expected to already be a public URL (Sanity CDN)
        post_input["assets"] = [{"image": {"url": photo_path}}]
        logger.info(f"Photo attached: {photo_path}")

    try:
        result = _run_query(MUTATION_TEXT, {"input": post_input})
        data = result.get("data") or {}
        payload = data.get("createPost", {})

        if "post" in payload:
            pid = payload["post"]["id"]
            logger.info(f"✓ Scheduled on Buffer — id={pid} | dueAt={due_at} | {text[:60]}...")
            return True
        elif "message" in payload:
            logger.error(f"Buffer error: {payload['message']}")
            return False
        elif "errors" in result:
            logger.error(f"Buffer API error: {result['errors'][0].get('message', 'Unknown error')}")
            return False
        else:
            logger.error(f"Unexpected Buffer response: {result}")
            return False

    except Exception as e:
        logger.error(f"Buffer API request failed: {e}")
        return False


def schedule_batch(posts: list[dict]) -> tuple[int, int]:
    """Schedule all posts to Buffer. Returns (success_count, fail_count)."""
    success, fail = 0, 0
    for post in posts:
        if schedule_post(post):
            success += 1
        else:
            fail += 1
    logger.info(f"Batch complete — {success} scheduled, {fail} failed")
    return success, fail


if __name__ == "__main__":
    list_channels()
