from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, BigInteger, Text
from database.session import Base

class User(Base):
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Movie(Base):
    
    __tablename__ = "movies"
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    title_original = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    genre = Column(String, nullable=True)
    country = Column(String, nullable=True)
    director = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    poster_url = Column(String, nullable=True)
    
    imdb_rating = Column(Float, nullable=True)
    kinopoisk_rating = Column(Float, nullable=True)
    rotten_tomatoes_rating = Column(Float, nullable=True)
    avg_rating = Column(Float, nullable=True)

class UserSelection(Base):
    
    __tablename__ = "user_selections"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    genre = Column(String, nullable=True)
    country = Column(String, nullable=True)
    min_rating = Column(Float, default=7.0)
    created_at = Column(DateTime, default=datetime.utcnow)