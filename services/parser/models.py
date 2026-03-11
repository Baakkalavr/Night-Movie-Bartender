from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class MovieSearchResult(BaseModel):
    """Результат поиска фильма"""
    source: str  
    source_id: str  
    title: str
    title_original: str
    year: Optional[int] = None
    url: str
    poster_url: Optional[str] = None

class MovieDetails(BaseModel):
    """Детальная информация о фильме"""
    title: str
    title_original: str
    year: Optional[int] = None
    genre: Optional[str] = None
    country: Optional[str] = None
    director: Optional[str] = None
    description: Optional[str] = None
    poster_url: Optional[str] = None
    duration: Optional[int] = None  
    
  
    imdb_rating: Optional[float] = None
    imdb_votes: Optional[int] = None
    kinopoisk_rating: Optional[float] = None
    metacritic_rating: Optional[int] = None
    rotten_tomatoes_rating: Optional[int] = None  
    
    actors: List[str] = Field(default_factory=list)
    writers: List[str] = Field(default_factory=list)
    
class ParsedMovie(BaseModel):
    """Полный объект фильма для сохранения в БД"""
    title: str
    title_original: str
    year: Optional[int] = None
    genre: Optional[str] = None
    country: Optional[str] = None
    director: Optional[str] = None
    description: Optional[str] = None
    poster_url: Optional[str] = None
    
    imdb_rating: Optional[float] = None
    imdb_votes: Optional[int] = None
    kinopoisk_rating: Optional[float] = None
    rotten_tomatoes_rating: Optional[float] = None
    
    avg_rating: Optional[float] = None
    
    def calculate_avg_rating(self) -> float:
        """Вычисляет средний рейтинг из доступных источников"""
        ratings = []
        if self.imdb_rating:
            ratings.append(self.imdb_rating)
        if self.kinopoisk_rating:
            ratings.append(self.kinopoisk_rating)
        if self.rotten_tomatoes_rating:
            ratings.append(self.rotten_tomatoes_rating / 10)  
        
        if ratings:
            return sum(ratings) / len(ratings)
        return 0.0