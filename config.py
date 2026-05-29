# ============================================================
#  X Music & Entertainment Bot — Configuration (OSS Edition)
# ============================================================

# --- Buffer API (only non-OSS component) ---
# Get your API key from: https://publish.buffer.com/settings/api
BUFFER_API_KEY    = "drRoxqoMOmf-qnMSfMRS-SSi00lP5eRyniGGskW2ZDA"
BUFFER_CHANNEL_ID = "6a143acec687a22dd42438a7"
BUFFER_API_URL    = "https://api.buffer.com/1/graphql"

# --- Groq LLM API ---
# Get your API key from: https://console.groq.com/keys
GROQ_API_KEY = "os.getenv("GROQ_API_KEY")"
GROQ_MODEL   = "llama-3.3-70b-versatile"

# --- Posting Schedule ---
POST_START_HOUR   = 8       # 8:00 AM
POST_END_HOUR     = 17      # 5:00 PM
POSTS_PER_DAY     = 90      # ⚠️ Keep below 100 to meet Buffer free plan limits
TIMEZONE          = "Africa/Lagos"

# --- Content Settings ---
MAX_TWEET_LENGTH  = 270

# --- Topics ---
TOPICS = [
    "new music drops",
    "celebrity gossip entertainment",
    "concerts and music festivals",
    "music charts and streaming numbers",
    "movies and TV series",
    "throwback music nostalgia",
    "behind the scenes music industry",
    "award shows music",
    "music beef and drama",
    "afrobeats music",
    "hip hop and rap",
    "pop music",
]


# --- Voice / Tone options ---
TONES = ["casual", "hype", "informative", "spicy", "nostalgic"]

# --- Output / Logging ---
LOG_FILE   = "logs/bot.log"
OUTPUT_CSV = "output/scheduled_posts.csv"
MEDIA_DIR  = "media"

# --- RSS listener settings ---
# Configure RSS feed URLs to poll for music news
RSS_FEEDS = [
    "https://pitchfork.com/rss/news/",
    "https://www.rollingstone.com/music/music-news/feed/",
]
# Poll interval in seconds (default: 15 minutes)
RSS_POLL_INTERVAL = 900
# SQLite database file to record seen entries and posting activity
SQLITE_DB = "output/rss_posts.db"
