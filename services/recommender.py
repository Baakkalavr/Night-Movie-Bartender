import random
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import not_, or_
from database.models import Movie, User, UserRating, UserViewed

logger = logging.getLogger(__name__)

class MovieRecommender:
    """Рекомендательный движок"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_recommendation(self, user_id: int, genre: str = None, min_rating: float = 0):
        """
        Получить рекомендацию фильма для пользователя
        """
        logger.info("=" * 60)
        logger.info(f"🔍 ПОИСК ФИЛЬМА: user_id={user_id}, genre={genre}, min_rating={min_rating}")
        

        viewed_subquery = self.db.query(UserViewed.movie_id).filter(
            UserViewed.user_id == user_id
        ).subquery()
        

        viewed_count = self.db.query(UserViewed).filter(UserViewed.user_id == user_id).count()
        logger.info(f"📊 Пользователь уже просмотрел/пропустил: {viewed_count} фильмов")
        

        query = self.db.query(Movie).filter(
            not_(Movie.id.in_(viewed_subquery))
        )
        

        total_movies = self.db.query(Movie).count()
        logger.info(f"📚 Всего фильмов в базе: {total_movies}")
        

        if genre and genre != "Любой":
            if genre == "Боевик":
                
                genre_conditions = [
                    Movie.genre == "Боевик",
                    Movie.genre == "Action",
                    Movie.genre.ilike('%боевик%'),
                    Movie.genre.ilike('%action%')
                ]
                query = query.filter(or_(*genre_conditions))
                logger.info(f"Поиск по жанру '{genre}': Боевик, Action")
                
            elif genre == "Фантастика":
                genre_conditions = [
                    Movie.genre == "Фантастика",
                    Movie.genre == "Sci-Fi",
                    Movie.genre == "Fantasy",
                    Movie.genre.ilike('%фантастика%'),
                    Movie.genre.ilike('%sci-fi%'),
                    Movie.genre.ilike('%fantasy%')
                ]
                query = query.filter(or_(*genre_conditions))
                logger.info(f"Поиск по жанру '{genre}': Фантастика, Sci-Fi, Fantasy")
                
            elif genre == "Драма":
                genre_conditions = [
                    Movie.genre == "Драма",
                    Movie.genre == "Drama",
                    Movie.genre.ilike('%драма%'),
                    Movie.genre.ilike('%drama%')
                ]
                query = query.filter(or_(*genre_conditions))
                logger.info(f"Поиск по жанру '{genre}': Драма, Drama")
                
            elif genre == "Комедия":
                genre_conditions = [
                    Movie.genre == "Комедия",
                    Movie.genre == "Comedy",
                    Movie.genre.ilike('%комедия%'),
                    Movie.genre.ilike('%comedy%')
                ]
                query = query.filter(or_(*genre_conditions))
                logger.info(f"Поиск по жанру '{genre}': Комедия, Comedy")
                
            else:
                
                query = query.filter(Movie.genre == genre)
                logger.info(f"Поиск по жанру '{genre}': {genre}")
        
        
        if min_rating and min_rating > 0:
            query = query.filter(Movie.imdb_rating >= min_rating)
            logger.info(f"Фильтр по рейтингу: >= {min_rating}")
        
       
        available_movies = query.all()
        logger.info(f"Найдено {len(available_movies)} доступных фильмов")
        
        
        if available_movies:
            movie_titles = [f"{m.title} ({m.genre})" for m in available_movies]
            logger.info(f"Найденные фильмы: {', '.join(movie_titles)}")
        else:
           
            total_genre_movies = self.db.query(Movie).filter(
                or_(
                    Movie.genre == "Боевик",
                    Movie.genre == "Action"
                )
            ).count()
            logger.warning(f"Всего фильмов жанра Боевик/Action в базе: {total_genre_movies}")
            
            if total_genre_movies > 0:
                
                all_genre_movies = self.db.query(Movie).filter(
                    or_(
                        Movie.genre == "Боевик",
                        Movie.genre == "Action"
                    )
                ).all()
                logger.info("Все фильмы этого жанра (без исключения просмотренных):")
                for m in all_genre_movies:
                    logger.info(f"  - {m.title} (ID: {m.id})")
        
        if not available_movies:
            logger.warning("Нет доступных фильмов!")
            return None
        

        selected_movie = random.choice(available_movies)
        logger.info(f"✅ Выбран фильм: {selected_movie.title} (жанр: {selected_movie.genre})")
        logger.info("=" * 60)
        
        return selected_movie
    
    def mark_as_viewed(self, user_id: int, movie_id: int, status: str = 'skipped'):
        """
        Отметить фильм как просмотренный/пропущенный (с защитой от дубликатов)
        """
        try:

            existing = self.db.query(UserViewed).filter_by(
                user_id=user_id,
                movie_id=movie_id
            ).first()
            
            if existing:
                existing.status = status
                existing.viewed_at = datetime.utcnow()
                logger.info(f"Пользователь {user_id} обновил статус фильма {movie_id} на {status}")
            else:
                viewed = UserViewed(
                    user_id=user_id,
                    movie_id=movie_id,
                    status=status
                )
                self.db.add(viewed)
                logger.info(f"Пользователь {user_id} {status} фильм {movie_id}")
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Ошибка при отметке фильма {movie_id}: {e}")
            self.db.rollback()
    
    def rate_movie(self, user_id: int, movie_id: int, rating: int):
        """
        Оценить фильм
        """
        try:
            existing = self.db.query(UserRating).filter_by(
                user_id=user_id, movie_id=movie_id
            ).first()
            
            if existing:
                existing.rating = rating
                logger.info(f"Пользователь {user_id} обновил оценку фильма {movie_id} на {rating}")
            else:
                rating_obj = UserRating(
                    user_id=user_id,
                    movie_id=movie_id,
                    rating=rating
                )
                self.db.add(rating_obj)
                logger.info(f"Пользователь {user_id} оценил фильм {movie_id} на {rating}")
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Ошибка при оценке фильма {movie_id}: {e}")
            self.db.rollback()
    
    def get_watched_movies(self, user_id: int, limit: int = 10):
        """
        Получить историю просмотренных фильмов пользователя
        """
        try:
            watched = self.db.query(Movie).join(
                UserViewed, Movie.id == UserViewed.movie_id
            ).filter(
                UserViewed.user_id == user_id,
                UserViewed.status == 'watched'
            ).order_by(
                UserViewed.viewed_at.desc()
            ).limit(limit).all()
            
            return watched
        except Exception as e:
            logger.error(f"Ошибка при получении истории: {e}")
            return []
    
    def get_available_count(self, user_id: int, genre: str = None):
        """
        Получить количество доступных фильмов для пользователя
        """
        viewed_subquery = self.db.query(UserViewed.movie_id).filter(
            UserViewed.user_id == user_id
        ).subquery()
        
        query = self.db.query(Movie).filter(
            not_(Movie.id.in_(viewed_subquery))
        )
        
        if genre and genre != "Любой":
            if genre == "Боевик":
                genre_conditions = [
                    Movie.genre == "Боевик",
                    Movie.genre == "Action"
                ]
                query = query.filter(or_(*genre_conditions))
            else:
                query = query.filter(Movie.genre == genre)
        
        return query.count()