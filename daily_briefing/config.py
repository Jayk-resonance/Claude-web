import os

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

RECIPIENT_EMAIL = "jupiter@sk.com"
SENDER_EMAIL = "kjwgv1442@gmail.com"

HAIKU_MODEL = "claude-haiku-4-5-20251001"
SONNET_MODEL = "claude-sonnet-4-6"

NEWS_QUERY = (
    '("EV battery" OR "electric vehicle battery" OR "battery" OR "배터리" OR '
    '"energy storage" OR "ESS" OR "grid storage" OR "stationary storage") AND '
    '("SK On" OR "CATL" OR "LG Energy" OR "Samsung SDI" OR "Panasonic" OR '
    '"lithium" OR "nickel" OR "cobalt" OR "IRA" OR '
    '"Ford" OR "GM" OR "Hyundai" OR "Tesla" OR "BYD")'
)

CATEGORIES = [
    "EV Maker",
    "EV 배터리 기술/산업",
    "SK온/배터리 경쟁사",
    "에너지 정책/규제",
    "배터리 광물/공급망",
    "ESS/에너지저장",
]

MAX_ARTICLES = 15
