import asyncio
import logging
from typing import List, Optional, Dict
from sqlalchemy.orm import Session

from database.session import SessionLocal
from database.models import Movie
from .imdb_playwright import IMDBPlaywrightParser
from .models import ParsedMovie

logger = logging.getLogger(__name__)

class MovieLoader:
    """Загрузчик фильмов из различных источников"""
    
    POPULAR_MOVIES = [
        "The Shawshank Redemption",
        "The Godfather",
        "The Godfather Part II",
        "The Dark Knight",
        "12 Angry Men",
        "Schindler's List",
        "The Lord of the Rings: The Return of the King",
        "Pulp Fiction",
        "The Good, the Bad and the Ugly",
        "Forrest Gump",
        "Fight Club",
        "Inception",
        "The Matrix",
        "Goodfellas",
        "One Flew Over the Cuckoo's Nest",
        "Se7en",
        "The Silence of the Lambs",
        "Saving Private Ryan",
        "The Green Mile",
        "Interstellar",
        "The Lion King",
        "Back to the Future",
        "Gladiator",
        "The Prestige",
        "The Departed",
        "Whiplash",
        "The Pianist",
        "Parasite",
        "The Wolf of Wall Street",
        "Django Unchained"
    ]
    
    async def load_popular_movies(self, limit: int = 30):
        """Загрузка популярных фильмов"""
        logger.info(f"🚀 Начинаем загрузку {limit} популярных фильмов...")
        
        parser = IMDBPlaywrightParser()
        loaded = 0
        failed = 0
        
        for i, movie_title in enumerate(self.POPULAR_MOVIES[:limit], 1):
            logger.info(f"[{i}/{limit}] Обработка: {movie_title}")
            
            try:
                # Ищем фильм
                results = await parser.search_movies(movie_title)
                if not results:
                    logger.warning(f"❌ Не найден: {movie_title}")
                    failed += 1
                    continue
                
                # Берем первый результат
                search_result = results[0]
                
                # Получаем детали
                details = await parser.get_movie_details(search_result.source_id)
                if not details:
                    logger.warning(f"❌ Нет деталей для: {movie_title}")
                    failed += 1
                    continue
                
                # Создаем объект для сохранения
                parsed_movie = ParsedMovie(
                    title=details.title,
                    title_original=details.title_original,
                    year=details.year,
                    genre=details.genre,
                    country=details.country,
                    director=details.director,
                    description=details.description,
                    poster_url=details.poster_url,
                    imdb_rating=details.imdb_rating,
                    imdb_votes=details.imdb_votes,
                    avg_rating=details.imdb_rating if details.imdb_rating else 0.0
                )
                
                # Сохраняем в БД
                if await self.save_movie(parsed_movie):
                    loaded += 1
                    logger.info(f"✅ [{i}/{limit}] Добавлен: {details.title}")
                else:
                    failed += 1
                
                # Задержка между запросами
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Ошибка при обработке {movie_title}: {e}")
                failed += 1
                continue
        
        logger.info("=" * 50)
        logger.info(f"📊 ИТОГИ ЗАГРУЗКИ:")
        logger.info(f"✅ Успешно загружено: {loaded}")
        logger.info(f"❌ Не удалось загрузить: {failed}")
        logger.info("=" * 50)
    
    async def save_movie(self, movie_data: ParsedMovie) -> bool:
        """Сохранение фильма в БД"""
        db = SessionLocal()
        try:
            # Проверяем, есть ли уже такой фильм
            existing = db.query(Movie).filter(
                Movie.title_original == movie_data.title_original
            ).first()
            
            if existing:
                # Обновляем существующий фильм
                for key, value in movie_data.dict().items():
                    if value is not None and hasattr(existing, key):
                        setattr(existing, key, value)
                logger.info(f"🔄 Обновлен фильм: {movie_data.title}")
            else:
                # Создаем новый фильм
                movie = Movie(
                    title=movie_data.title,
                    title_original=movie_data.title_original,
                    year=movie_data.year,
                    genre=movie_data.genre,
                    country=movie_data.country,
                    director=movie_data.director,
                    description=movie_data.description,
                    poster_url=movie_data.poster_url,
                    imdb_rating=movie_data.imdb_rating,
                    kinopoisk_rating=movie_data.kinopoisk_rating,
                    rotten_tomatoes_rating=movie_data.rotten_tomatoes_rating,
                    avg_rating=movie_data.avg_rating
                )
                db.add(movie)
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения в БД: {e}")
            db.rollback()
            return False
        finally:
            db.close()