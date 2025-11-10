"""
Configuration for SII FAQ scraper
"""

# Base URLs
BASE_URL = "https://www.sii.cl/preguntas_frecuentes"
MAIN_FAQ_URL = f"{BASE_URL}/otros.html"

# Request configuration
REQUEST_TIMEOUT = 30
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds
