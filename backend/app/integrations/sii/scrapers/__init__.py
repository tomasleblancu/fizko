"""
Modulo de scrapers especializados para el SII
"""
from .base_scraper import BaseScraper
from .f29_scraper import F29Scraper
from .boletas_honorario_scraper import BoletasHonorarioScraper

__all__ = [
    'BaseScraper',
    'F29Scraper',
    'BoletasHonorarioScraper',
]
