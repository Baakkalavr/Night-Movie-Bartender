import random
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, not_, func
from database.models import Movie, User, UserRating, UserViewed

logger = logging.getLogger(__name__)

class MovieRecommender:
    """Оптимизированный рекомендательный движок"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_recommendation(self, user_id: int, genre: str = None, country: str = None, min_rating: float = 0):
        """
        Получить рекомендацию фильма для пользователя (оптимизированная версия)
        """
       
        viewed_subquery = self.db.query(UserViewed.movie_id).filter(
            UserViewed.user_id == user_id
        ).subquery()
        
        
        query = self.db.query(Movie).filter(
            not_(Movie.id.in_(viewed_subquery.select()))
        )
        
        
        if genre and genre != "Не важно" and genre != "Другая":
            query = query.filter(Movie.genre == genre)
        
        if country and country != "Не важно" and country != "Другая":
            query = query.filter(Movie.country == country)
        
        if min_rating and min_rating > 0:
            query = query.filter(Movie.avg_rating >= min_rating)
        
    
        count = query.count()
        
        if count == 0:
            return None
        

        random_offset = random.randint(0, count - 1)
        movie = query.offset(random_offset).limit(1).first()
        
        return movie
    
    def get_popular_movies(self, limit: int = 10):
        """Получить популярные фильмы (по рейтингу)"""
        return self.db.query(Movie).order_by(
            Movie.avg_rating.desc()
        ).limit(limit).all()
    
    def get_recommendations_by_similar_users(self, user_id: int, limit: int = 5):
        """
        Рекомендации на основе похожих пользователей
        """

        similar_users = self.db.query(UserRating.user_id).filter(
            UserRating.movie_id.in_(
                self.db.query(UserRating.movie_id).filter(UserRating.user_id == user_id)
            ),
            UserRating.user_id != user_id
        ).group_by(UserRating.user_id).order_by(
            func.count().desc()
        ).limit(10).subquery()
        

        recommendations = self.db.query(Movie).join(
            UserRating, Movie.id == UserRating.movie_id
        ).filter(
            UserRating.user_id.in_(similar_users),
            UserRating.rating >= 7,
            not_(Movie.id.in_(
                self.db.query(UserViewed.movie_id).filter(UserViewed.user_id == user_id)
            ))
        ).group_by(Movie.id).order_by(
            func.avg(UserRating.rating).desc()
        ).limit(limit).all()
        
        return recommendations
    
    def mark_as_viewed(self, user_id: int, movie_id: int, status: str = 'skipped'):
        """Отметить фильм как просмотренный/пропущенный"""
        viewed = UserViewed(
            user_id=user_id,
            movie_id=movie_id,
            status=status
        )
        self.db.add(viewed)
        self.db.commit()
        logger.info(f"Пользователь {user_id} {status} фильм {movie_id}")
    
    def rate_movie(self, user_id: int, movie_id: int, rating: int):
        """Оценить фильм"""

        existing = self.db.query(UserRating).filter_by(
            user_id=user_id, movie_id=movie_id
        ).first()
        
        if existing:
            existing.rating = rating
        else:
            rating_obj = UserRating(
                user_id=user_id,
                movie_id=movie_id,
                rating=rating
            )
            self.db.add(rating_obj)
        
        self.db.commit()
        logger.info(f"Пользователь {user_id} оценил фильм {movie_id} на {rating}")