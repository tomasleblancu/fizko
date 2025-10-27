"""
Excepciones personalizadas para la integración de Kapso
"""


class KapsoAPIError(Exception):
    """Error base para la API de Kapso"""
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


class KapsoAuthenticationError(KapsoAPIError):
    """Error de autenticación con la API de Kapso"""
    pass


class KapsoValidationError(KapsoAPIError):
    """Error de validación de datos"""
    pass


class KapsoTimeoutError(KapsoAPIError):
    """Error de timeout en la API de Kapso"""
    pass


class KapsoNotFoundError(KapsoAPIError):
    """Recurso no encontrado"""
    pass
