"""
Пакет для парсинга информации о фильмах с различных источников
"""

from .imdb_parser import IMDBParser
from .movie_loader import MovieLoader
from .models import MovieSearchResult, MovieDetails, ParsedMovie

__all__ = [
    'IMDBParser',
    'MovieLoader',
    'MovieSearchResult',
    'MovieDetails',
    'ParsedMovie'
]