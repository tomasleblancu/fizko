"""
Configuración para SII STC Integration
"""

# URLs del SII para consultas sin autenticación
STC_PORTAL_URL = "https://www2.sii.cl/stc/noauthz/"
STC_API_URL = "https://www2.sii.cl/app/stc/recurso/v1/consulta/getConsultaData/"

# reCAPTCHA configuration
RECAPTCHA_SITE_KEY = "6Lc_DPAqAAAAAB7QWxHsaPDNxLLOUj9VkiuAXRYP"
RECAPTCHA_RELOAD_URL = "https://www.google.com/recaptcha/enterprise/reload"

# Timeouts
DEFAULT_PAGE_LOAD_TIMEOUT = 30
DEFAULT_RECAPTCHA_WAIT_TIMEOUT = 10
DEFAULT_QUERY_TIMEOUT = 15

# Selenium configuration
DEFAULT_WINDOW_SIZE = "1920,1080"
