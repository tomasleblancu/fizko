"""
Core components for STC integration
"""

from .driver import STCDriver
from .recaptcha_interceptor import RecaptchaInterceptor

__all__ = ['STCDriver', 'RecaptchaInterceptor']
