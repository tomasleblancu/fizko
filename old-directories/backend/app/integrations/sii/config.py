"""
Configuración simplificada de RPA v3
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Configuración global de RPA v3"""

    # Driver
    headless: bool = True
    timeout: int = 15
    long_timeout: int = 30
    window_size: str = "1280,720"

    # Sesiones
    session_expiry_hours: int = 8

    # Chrome
    chrome_binary: Optional[str] = None
    chromedriver_path: Optional[str] = None

    # Logging
    log_level: str = "INFO"

    @classmethod
    def from_django_settings(cls):
        """Carga configuración desde Django settings"""
        try:
            from django.conf import settings
            return cls(
                headless=getattr(settings, 'RPA_HEADLESS', True),
                chrome_binary=getattr(settings, 'CHROME_BINARY_PATH', None),
                chromedriver_path=getattr(settings, 'CHROME_DRIVER_PATH', None),
            )
        except ImportError:
            return cls()


# Instancia global
config = Config.from_django_settings()
