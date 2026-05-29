# ============================================================
#  Tweet Generator — Groq API with local human-style fallback
# ============================================================

import random
import json
import logging
import requests
from config import MAX_TWEET_LENGTH, TOPICS, TONES, GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You write tweets for a music and entertainment X (Twitter) page.

STRICT RULES:
- Sound exactly like a real passionate fan or music enthusiast — not a brand, not a bot
- Use casual, conversational language. Occasional slang and imperfect grammar are fine.
- Avoid polished, corporate, or promotional wording.
- Do NOT start the tweet with "I"
- Do NOT use hashtags unless they feel 100% natural (max 1, never forced)
- Do NOT mention AI, bots, automation, or writing tools.
- Do NOT use the phrases "as a fan", "to be honest", "honestly", "in my opinion" unless extremely natural.
- No corporate speak: never use "exciting", "thrilling", "amazing opportunity", "delighted"
- No em-dashes (—), no bullet points, no numbered lists
- Keep it under 260 characters
- Vary your structure — some posts are one punchy line, some are 2-3 short sentences
- Use a natural mix of personal feeling, opinion, or reaction to the subject
- Return ONLY the tweet text. No quotes around it. No explanation. Nothing else."""

TONE_INSTRUCTIONS = {
    "casual":      "Write in a laid-back, opinionated, everyday-fan voice. Like texting a friend about music.",
    "hype":        "Write with high energy and excitement. Enthusiastic but not fake — like you genuinely can't contain it.",
    "informative": "Share an interesting fact or observation, but frame it conversationally, not like a Wikipedia article.",
    "spicy":       "Drop a hot take or slightly controversial opinion. Confident, not aggressive. Never start with 'Unpopular opinion:'.",
    "nostalgic":   "Write with a warm, reflective tone. Music memories, feelings, nostalgia done naturally.",
}



TOPIC_SUBJECTS = {
    "new music drops": [
        "Kendrick's latest", "SZA's new record", "Tyler's new project",
        "Sabrina Carpenter's new single", "Tems' latest drop", "Rema's new EP",
        "Burna Boy's collab", "this new Asake record", "Wizkid's vault release",
        "Davido's latest", "the new Benson Boone album", "Chappell Roan's new track",
    ],
    "celebrity gossip entertainment": [
        "the Drake situation", "what's happening with Ye right now",
        "Taylor's whole era", "that Chris Brown interview", "the Nicki vs Cardi chapter",
        "what happened at that Met Gala",
    ],
    "concerts and music festivals": [
        "Coachella 2025", "Afrobeats festival season", "Glastonbury this year",
        "Rolling Loud", "Wireless Festival", "a Lagos concert last weekend",
        "the O2 Arena run this month", "Afronation Portugal",
    ],
    "music charts and streaming numbers": [
        "this week's Billboard Hot 100", "Spotify's current top 10",
        "the Afrobeats chart right now", "Apple Music flipping the script this week",
        "streaming numbers that don't add up to artist pay",
    ],
    "movies and TV series": [
        "that new Netflix music documentary", "Euphoria's soundtrack choices",
        "that A24 film everyone's talking about", "the new music biopic",
        "that HBO music series",
    ],
    "throwback music nostalgia": [
        "early 2000s R&B", "Fela Kuti's catalog", "classic Wizkid albums",
        "90s hip hop production", "peak Aaliyah era", "the D'Angelo Voodoo album",
        "old school Afrobeat", "early Kanye West",
    ],
    "behind the scenes music industry": [
        "how that album was recorded in secret", "the producer behind everyone's 2024 favorite",
        "the songwriting camp nobody knew about", "how labels treat streaming royalties",
        "what really goes into an album rollout",
    ],
    "award shows music": [
        "the Grammy snubs this cycle", "BET Awards performance of the night",
        "MOBO nominees this year", "Headies award picks", "MTV VMAs drama",
    ],
    "music beef and drama": [
        "the beef that nobody expected", "that diss track that changed the game",
        "how this feud started over something small", "the apology nobody believed",
    ],
    "afrobeats music": [
        "Afrobeats taking over global charts", "the new wave of Afro-fusion artists",
        "how Afrobeats changed the music industry", "Burna's global run right now",
        "Wizkid's influence on the genre", "the Lagos music scene right now",
    ],
    "hip hop and rap": [
        "the current state of hip hop", "drill music's evolution",
        "this generation of rappers vs the last", "the best rap album of the year so far",
        "conscious rap making a comeback",
    ],
    "pop music": [
        "pop music's identity crisis right now", "the new era of pop stars",
        "hyperpop going mainstream", "the best pop album nobody talked about",
        "pop production trends in 2025",
    ],
}


# No external LLM: use local Python templates and fallback generators only.


def get_random_topic() -> str:
    return random.choice(TOPICS)


def get_random_tone() -> str:
    return random.choice(TONES)


def get_subject(topic: str) -> str:
    pool = TOPIC_SUBJECTS.get(topic, ["music this week"])
    return random.choice(pool)

FALLBACK_TEMPLATES = {
    "casual": [
        "This one feels like it needs a replay. {subject} is low-key fire.",
        "Been stuck on {subject} all day, and it still hits.",
        "Not sure how {subject} isn’t already on everyone’s playlist.",
    ],
    "hype": [
        "Bruh, {subject} is straight heat. Can’t wait to blast this.",
        "Okay, {subject} just changed my mood. This one’s a vibe.",
        "If you’re not buzzing to {subject} yet, you’re sleeping.",
    ],
    "informative": [
        "Quick take: {subject} is the kind of drop that talks for itself.",
        "Feels like {subject} is the one people will mention tomorrow.",
        "This is the kind of music moment that actually matters right now.",
    ],
    "spicy": [
        "Call me crazy, but {subject} might be the best thing they’ve done in years.",
        "Not everyone will agree, but {subject} is the real one here.",
        "This is the kind of move that makes you rethink the whole scene.",
    ],
    "nostalgic": [
        "{subject} brings back that exact vibe I miss from old school playlists.",
        "This one sounds like a throwback even though it just dropped.",
        "I’m feeling all the nostalgia from {subject} right now.",
    ],
}


def fallback_tweet(subject: str, tone: str) -> str:
    template = random.choice(FALLBACK_TEMPLATES.get(tone, FALLBACK_TEMPLATES["casual"]))
    text = template.format(subject=subject)
    return sanitize_tweet(text)


def sanitize_tweet(text: str) -> str:
    text = text.strip()
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1].strip()
    if len(text) > MAX_TWEET_LENGTH:
        text = text[:MAX_TWEET_LENGTH].rsplit(' ', 1)[0]
    return text


def generate_tweet(topic: str = None, tone: str = None) -> dict:
    topic   = topic or get_random_topic()
    tone    = tone  or get_random_tone()
    subject = get_subject(topic)

    prompt = (
        f"{TONE_INSTRUCTIONS.get(tone, '')}\n\n"
        f"Write a tweet about: {subject}\n"
        f"Context/niche: {topic}"
    )

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 150
    }
    
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=20)
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"].strip()
        text = sanitize_tweet(text)
    except Exception as e:
        logger.warning(f"Groq API call failed: {e}, using fallback text")
        text = fallback_tweet(subject, tone)

    logger.info(f"Generated [{tone}][{topic}]: {text[:60]}...")
    return {"text": text, "topic": topic, "tone": tone, "subject": subject}


def generate_batch(count: int, topic: str = None, tone: str = None) -> list[dict]:
    posts = []
    for i in range(count):
        post = generate_tweet(topic=topic, tone=tone)
        posts.append(post)
        logger.info(f"  [{i+1}/{count}] done")
    return posts
