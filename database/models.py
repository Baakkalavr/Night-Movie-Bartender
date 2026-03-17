from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, BigInteger, Text, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from database.session import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)  
    username = Column(String, nullable=True, index=True)  
    first_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)  
    
    ratings = relationship("UserRating", back_populates="user", cascade="all, delete-orphan")
    viewed = relationship("UserViewed", back_populates="user", cascade="all, delete-orphan")

class Movie(Base):
    __tablename__ = 'movies'
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False, index=True)  
    title_original = Column(String, nullable=True)
    year = Column(Integer, nullable=True, index=True)  
    genre = Column(String, nullable=True, index=True)  
    country = Column(String, nullable=True, index=True)  
    director = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    poster_url = Column(String, nullable=True)

    imdb_rating = Column(Float, nullable=True)
    kinopoisk_rating = Column(Float, nullable=True)
    rotten_tomatoes_rating = Column(Float, nullable=True)

    avg_rating = Column(Float, nullable=True, index=True)  
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)  
    

    __table_args__ = (
        Index('idx_movie_genre_country_rating', 'genre', 'country', 'avg_rating'),
    )
    
    ratings = relationship("UserRating", back_populates="movie", cascade="all, delete-orphan")
    viewed = relationship("UserViewed", back_populates="movie", cascade="all, delete-orphan")

class UserRating(Base):
    __tablename__ = 'user_ratings'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False, index=True)  
    movie_id = Column(Integer, ForeignKey('movies.id', ondelete="CASCADE"), nullable=False, index=True)  
    rating = Column(Integer, nullable=False, index=True)  
    created_at = Column(DateTime, default=datetime.utcnow, index=True)  
    
    __table_args__ = (
        Index('idx_user_rating_user_movie', 'user_id', 'movie_id', unique=True),
    )
    

    user = relationship("User", back_populates="ratings")
    movie = relationship("Movie", back_populates="ratings")

class UserViewed(Base):
    __tablename__ = 'user_viewed'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False, index=True)  
    movie_id = Column(Integer, ForeignKey('movies.id', ondelete="CASCADE"), nullable=False, index=True)  
    viewed_at = Column(DateTime, default=datetime.utcnow, index=True)  
    status = Column(String, nullable=False, index=True)  
    

    __table_args__ = (
        Index('idx_user_viewed_user_movie', 'user_id', 'movie_id', unique=True),
        Index('idx_user_viewed_user_status', 'user_id', 'status'),
    )
    

    user = relationship("User", back_populates="viewed")
    movie = relationship("Movie", back_populates="viewed")