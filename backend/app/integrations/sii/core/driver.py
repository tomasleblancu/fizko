"""
Selenium WebDriver wrapper - Usa implementación interna de v3
"""
from .selenium_driver import SeleniumDriver as InternalDriver, DriverConfig
from ..config import config as v3_config


class SeleniumDriver(InternalDriver):
    """
    Wrapper de Selenium - Configuración adaptada a v3
    """

    def __init__(self, custom_config=None):
        """
        Inicializa el driver con configuración de v3

        Args:
            custom_config: Configuración personalizada (opcional)
        """
        # Adaptar config v3 a DriverConfig
        driver_config = DriverConfig(
            DEFAULT_TIMEOUT=custom_config.get('timeout', v3_config.timeout) if custom_config else v3_config.timeout,
            LONG_TIMEOUT=custom_config.get('long_timeout', v3_config.long_timeout) if custom_config else v3_config.long_timeout,
            HEADLESS=custom_config.get('headless', v3_config.headless) if custom_config else v3_config.headless,
            CHROME_BINARY_PATH=v3_config.chrome_binary,
            CHROME_DRIVER_PATH=v3_config.chromedriver_path,
            WINDOW_SIZE=v3_config.window_size,
        )

        # Inicializar con config interna
        super().__init__(config=driver_config)
