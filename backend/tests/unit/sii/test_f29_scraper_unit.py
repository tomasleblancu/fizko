"""
Unit tests for F29 scraper functionality.

Tests the F29Scraper class with mocked Selenium WebDriver to verify:
- Loading GIF wait logic
- Button disabled state handling
- codInt extraction
- Screenshot capture on errors
- Callback triggering
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, call
import time
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    TimeoutException,
    WebDriverException
)
from selenium.webdriver.common.by import By

# Import the scraper
from app.integrations.sii.scrapers.f29_scraper import F29Scraper
from app.integrations.sii.exceptions import ScrapingException


@pytest.fixture
def mock_driver():
    """Mock SeleniumDriver with common WebDriver behaviors"""
    driver = Mock()

    # Mock driver.driver (the actual WebDriver)
    driver.driver = Mock()
    driver.driver.current_url = "https://www4.sii.cl/sifmConsultaInternet/index.html"
    driver.driver.window_handles = ["window1"]
    driver.driver.page_source = "<html>Mock page</html>"

    # Mock navigation
    driver.navigate_to = Mock()

    # Mock element finding
    driver.wait_for_element = Mock()
    driver.wait_for_elements = Mock()
    driver.wait_for_clickable = Mock()

    # Mock option selection
    driver.select_option_by_value = Mock()

    # Mock cookies
    driver.get_cookies = Mock(return_value=[])

    return driver


@pytest.fixture
def mock_formulario_button():
    """Mock button element for 'Formulario Compacto'"""
    button = Mock()
    button.click = Mock()
    button.get_attribute = Mock(side_effect=lambda attr: None if attr == "disabled" else "")
    return button


@pytest.fixture
def f29_scraper(mock_driver):
    """F29Scraper instance with mocked driver"""
    scraper = F29Scraper(mock_driver)
    return scraper


class TestF29ScraperBasic:
    """Basic functionality tests for F29Scraper"""

    @pytest.mark.unit
    def test_scraper_initialization(self, f29_scraper):
        """Test scraper initializes with correct attributes"""
        assert f29_scraper.FORM_CODE == "29"
        assert "sii.cl" in f29_scraper.SEARCH_URL

    @pytest.mark.unit
    def test_validar_parametros_sin_anio_ni_folio(self, f29_scraper):
        """Test validation fails when no año or folio provided"""
        with pytest.raises(ValueError, match="Debe especificar ano o folio"):
            f29_scraper._validar_parametros(anio=None, folio=None)

    @pytest.mark.unit
    def test_validar_parametros_anio_invalido(self, f29_scraper):
        """Test validation fails with invalid year format"""
        with pytest.raises(ValueError, match="debe ser un numero de 4 digitos"):
            f29_scraper._validar_parametros(anio="24", folio=None)

    @pytest.mark.unit
    def test_validar_parametros_validos(self, f29_scraper):
        """Test validation passes with valid parameters"""
        # Should not raise
        f29_scraper._validar_parametros(anio="2024", folio=None)
        f29_scraper._validar_parametros(anio=None, folio="123456")


class TestF29ScraperCodIntExtraction:
    """Tests for codInt extraction with loading GIF scenarios"""

    @pytest.mark.unit
    @patch('app.integrations.sii.scrapers.f29_scraper.WebDriverWait')
    def test_extraer_codint_success(self, mock_wait, f29_scraper, mock_formulario_button):
        """Test successful codInt extraction from URL"""
        folio = "8510019316"

        # Mock: Button found
        f29_scraper.driver.driver.find_element = Mock(return_value=mock_formulario_button)

        # Mock: Window handles before/after click
        f29_scraper.driver.driver.window_handles = ["window1"]

        def side_effect_click():
            # Simulate new window opening after click
            f29_scraper.driver.driver.window_handles = ["window1", "window2"]

        mock_formulario_button.click.side_effect = side_effect_click

        # Mock: New window with codInt in URL
        f29_scraper.driver.driver.current_url = "https://www4.sii.cl/...?codInt=775148628"

        # Mock: Close and switch back
        f29_scraper.driver.driver.close = Mock()
        f29_scraper.driver.driver.switch_to = Mock()
        f29_scraper.driver.driver.switch_to.window = Mock()

        # Execute
        result = f29_scraper._extraer_codint_from_formulario_compacto(folio)

        # Assert
        assert result == "775148628"
        mock_formulario_button.click.assert_called_once()

    @pytest.mark.unit
    @patch('app.integrations.sii.scrapers.f29_scraper.time.sleep')
    def test_extraer_codint_button_disabled_initially(
        self,
        mock_sleep,
        f29_scraper,
        mock_formulario_button
    ):
        """Test extraction when button is disabled initially"""
        folio = "8510019316"

        # Mock: Button starts disabled, becomes enabled after wait
        disabled_button = Mock()
        disabled_button.get_attribute = Mock(return_value="true")
        disabled_button.click = Mock(side_effect=ElementClickInterceptedException(
            "Element is not clickable"
        ))

        enabled_button = mock_formulario_button

        # First call returns disabled button, second call returns enabled
        f29_scraper.driver.driver.find_element = Mock(
            side_effect=[disabled_button, enabled_button]
        )

        # Mock window handles
        f29_scraper.driver.driver.window_handles = ["window1"]

        def side_effect_click():
            f29_scraper.driver.driver.window_handles = ["window1", "window2"]

        enabled_button.click.side_effect = side_effect_click

        # Mock new window URL
        f29_scraper.driver.driver.current_url = "https://www4.sii.cl/...?codInt=775148628"
        f29_scraper.driver.driver.close = Mock()
        f29_scraper.driver.driver.switch_to = Mock()
        f29_scraper.driver.driver.switch_to.window = Mock()

        # Execute
        result = f29_scraper._extraer_codint_from_formulario_compacto(folio)

        # Assert
        assert result == "775148628"

    @pytest.mark.unit
    def test_extraer_codint_no_new_window(self, f29_scraper, mock_formulario_button):
        """Test when no new window opens after click"""
        folio = "8510019316"

        f29_scraper.driver.driver.find_element = Mock(return_value=mock_formulario_button)
        f29_scraper.driver.driver.window_handles = ["window1"]

        # No new window opens
        mock_formulario_button.click = Mock()

        result = f29_scraper._extraer_codint_from_formulario_compacto(folio)

        assert result is None

    @pytest.mark.unit
    def test_extraer_codint_no_codint_in_url(self, f29_scraper, mock_formulario_button):
        """Test when URL doesn't contain codInt parameter"""
        folio = "8510019316"

        f29_scraper.driver.driver.find_element = Mock(return_value=mock_formulario_button)
        f29_scraper.driver.driver.window_handles = ["window1"]

        def side_effect_click():
            f29_scraper.driver.driver.window_handles = ["window1", "window2"]

        mock_formulario_button.click.side_effect = side_effect_click

        # URL without codInt
        f29_scraper.driver.driver.current_url = "https://www4.sii.cl/some/page"
        f29_scraper.driver.driver.close = Mock()
        f29_scraper.driver.driver.switch_to = Mock()
        f29_scraper.driver.driver.switch_to.window = Mock()

        result = f29_scraper._extraer_codint_from_formulario_compacto(folio)

        assert result is None


class TestF29ScraperErrorHandling:
    """Tests for error handling and screenshots"""

    @pytest.mark.unit
    @patch('app.integrations.sii.scrapers.f29_scraper.F29Scraper._take_debug_screenshot')
    def test_extraer_codint_webdriver_exception(
        self,
        mock_screenshot,
        f29_scraper,
        mock_formulario_button
    ):
        """Test WebDriverException triggers screenshot"""
        folio = "8578993776"

        f29_scraper.driver.driver.find_element = Mock(return_value=mock_formulario_button)
        f29_scraper.driver.driver.window_handles = ["window1"]

        # Mock click raises WebDriverException
        mock_formulario_button.click = Mock(
            side_effect=WebDriverException("Chrome crashed")
        )

        result = f29_scraper._extraer_codint_from_formulario_compacto(folio)

        assert result is None
        mock_screenshot.assert_called_once_with("webdriver_codint", folio)

    @pytest.mark.unit
    @patch('app.integrations.sii.scrapers.f29_scraper.F29Scraper._take_debug_screenshot')
    def test_extraer_codint_click_intercepted(
        self,
        mock_screenshot,
        f29_scraper,
        mock_formulario_button
    ):
        """Test ElementClickInterceptedException triggers screenshot"""
        folio = "8578993776"

        f29_scraper.driver.driver.find_element = Mock(return_value=mock_formulario_button)

        # Mock: click intercepted by loading GIF
        mock_formulario_button.click = Mock(
            side_effect=ElementClickInterceptedException(
                "Element intercepted by <img src='pleasewait.gif'>"
            )
        )

        result = f29_scraper._extraer_codint_from_formulario_compacto(folio)

        assert result is None
        # Screenshot should be taken
        assert mock_screenshot.called


class TestF29ScraperCallback:
    """Tests for save callback functionality"""

    @pytest.mark.unit
    def test_buscar_formularios_triggers_callback(self, f29_scraper):
        """Test that save_callback is triggered for each formulario"""
        callback_mock = Mock()

        # Mock navigation and form selection
        f29_scraper._navegar_a_busqueda = Mock()
        f29_scraper._click_buscar_formulario = Mock()
        f29_scraper._seleccionar_tipo_formulario = Mock()
        f29_scraper._configurar_criterios_busqueda = Mock()
        f29_scraper._ejecutar_consulta = Mock(return_value="")

        # Mock table extraction - return 3 formularios
        mock_formularios = [
            {"folio": "F1", "period": "2024-01", "amount": 100, "id_interno_sii": "123"},
            {"folio": "F2", "period": "2024-02", "amount": 200, "id_interno_sii": "456"},
            {"folio": "F3", "period": "2024-03", "amount": 300, "id_interno_sii": "789"},
        ]
        f29_scraper._extraer_resultados = Mock(return_value=mock_formularios)

        # Execute
        result = f29_scraper.buscar_formularios(
            anio="2024",
            save_callback=callback_mock
        )

        # Assert callback called for each formulario
        assert callback_mock.call_count == 3
        assert result == mock_formularios

    @pytest.mark.unit
    def test_buscar_formularios_callback_receives_formulario(self, f29_scraper):
        """Test that callback receives formulario dict with correct structure"""
        received_formularios = []

        def capture_callback(formulario):
            received_formularios.append(formulario)

        # Mock scraper methods
        f29_scraper._navegar_a_busqueda = Mock()
        f29_scraper._click_buscar_formulario = Mock()
        f29_scraper._seleccionar_tipo_formulario = Mock()
        f29_scraper._configurar_criterios_busqueda = Mock()
        f29_scraper._ejecutar_consulta = Mock(return_value="")

        mock_formulario = {
            "folio": "8510019316",
            "period": "2025-01",
            "contributor": "77794858-K",
            "submission_date": "09/05/2024",
            "status": "Vigente",
            "amount": 42443,
            "id_interno_sii": "775148628"
        }
        f29_scraper._extraer_resultados = Mock(return_value=[mock_formulario])

        # Execute
        f29_scraper.buscar_formularios(
            anio="2025",
            save_callback=capture_callback
        )

        # Assert
        assert len(received_formularios) == 1
        received = received_formularios[0]
        assert received["folio"] == "8510019316"
        assert received["id_interno_sii"] == "775148628"
        assert "period" in received
        assert "amount" in received


class TestF29ScraperSessionValidation:
    """Tests for session validation logic"""

    @pytest.mark.unit
    def test_check_session_valid_success(self, f29_scraper):
        """Test session validation when session is valid"""
        # Mock valid session
        f29_scraper.driver.driver.current_url = "https://www4.sii.cl/page"
        f29_scraper.driver.driver.window_handles = ["window1"]

        result = f29_scraper._check_session_valid()

        assert result is True

    @pytest.mark.unit
    def test_check_session_valid_invalid_session(self, f29_scraper):
        """Test session validation when session is invalid"""
        from selenium.common.exceptions import InvalidSessionIdException

        # Mock invalid session
        f29_scraper.driver.driver.current_url = Mock(
            side_effect=InvalidSessionIdException("Session invalid")
        )

        result = f29_scraper._check_session_valid()

        assert result is False

    @pytest.mark.unit
    def test_check_session_valid_webdriver_error(self, f29_scraper):
        """Test session validation with WebDriver error"""
        # Mock WebDriver error
        f29_scraper.driver.driver.current_url = Mock(
            side_effect=WebDriverException("Connection lost")
        )

        result = f29_scraper._check_session_valid()

        assert result is False
