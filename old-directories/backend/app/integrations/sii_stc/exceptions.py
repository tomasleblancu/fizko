"""
Excepciones para SII STC Integration
"""


class STCException(Exception):
    """Excepción base para errores de STC"""
    pass


class STCRecaptchaError(STCException):
    """Error al resolver reCAPTCHA"""
    pass


class STCQueryError(STCException):
    """Error al realizar consulta"""
    pass


class STCTimeoutError(STCException):
    """Timeout al esperar respuesta"""
    pass
