"""
Excepciones específicas de RPA v3
"""


class RPAException(Exception):
    """Excepción base para RPA v3"""
    pass


class AuthenticationError(RPAException):
    """Error de autenticación con el SII"""

    def __init__(self, message: str, tax_id: str = None):
        self.tax_id = tax_id
        super().__init__(message)


class ExtractionError(RPAException):
    """Error en extracción de datos"""

    def __init__(self, message: str, resource: str = None):
        self.resource = resource
        super().__init__(message)


class SessionError(RPAException):
    """Error de gestión de sesión"""

    def __init__(self, message: str, session_id: str = None):
        self.session_id = session_id
        super().__init__(message)


class ValidationError(RPAException):
    """Error de validación de datos"""

    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message)


class DriverNotStartedException(RPAException):
    """Error cuando se intenta usar el driver antes de iniciarlo"""
    pass


class DriverTimeoutException(RPAException):
    """Error de timeout del driver"""
    pass


class ElementNotFoundException(RPAException):
    """Error cuando no se encuentra un elemento en la página"""
    pass


class AuthenticationException(RPAException):
    """Excepción genérica de autenticación"""
    pass


class InvalidCredentialsException(RPAException):
    """Credenciales inválidas"""
    pass


class SIIUnavailableException(RPAException):
    """SII no disponible temporalmente"""

    def __init__(self, message: str, retry_after: int = None):
        self.retry_after = retry_after
        super().__init__(message)


class PageNotLoadedException(RPAException):
    """Página no se cargó correctamente"""
    pass


class UnexpectedRedirectException(RPAException):
    """Redirección inesperada durante autenticación"""
    pass


class ScrapingException(RPAException):
    """Error durante scraping de datos"""
    pass
