# Channel configuration for @a.storyof.two

import os

INSTAGRAM_HANDLE = "a.storyof.two"
INSTAGRAM_URL = "https://www.instagram.com/a.storyof.two/"

APIFY_API_KEY = os.getenv("APIFY_API_KEY", "")
APIFY_USER_ID = os.getenv("APIFY_USER_ID", "")

APIFY_ACTORS = {
    "profile_scraper": "apify/instagram-profile-scraper",
    "post_scraper":    "apify/instagram-scraper",
}

# Content pillars for theme classification
CONTENT_PILLARS = [
    "travel",
    "relationship_milestones",
    "daily_life",
    "shared_experiences",
    "reflections",
    "celebrations",
    "food",
    "home",
]

# Emotional tone categories for analysis
EMOTIONAL_TONES = [
    "warm",
    "nostalgic",
    "playful",
    "celebratory",
    "intimate",
    "reflective",
    "adventurous",
    "grateful",
]

# Hashtag clusters to track
HASHTAG_CLUSTERS = {
    "couple": ["couplegoals", "couplestories", "couplephotography", "lovestory"],
    "travel": ["travel", "wanderlust", "travelcouple", "coupletravel"],
    "india":  ["india", "incredibleindia", "indiancouple"],
    "life":   ["everydaymoments", "lifestory", "togetherness"],
}

# Scrape config
DEFAULT_SCRAPE_LIMIT = 50   # posts per run
MAX_SCRAPE_LIMIT = 200      # max historical pull
