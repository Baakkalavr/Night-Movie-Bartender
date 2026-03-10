from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
import logging

logger = logging.getLogger(__name__)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_dir = os.path.join(BASE_DIR, 'data')
db_path = os.path.join(db_dir, 'movies.db')


try:
    os.makedirs(db_dir, exist_ok=True)
    logger.info(f"📁 Папка для БД: {db_dir}")
    logger.info(f"📄 Файл БД: {db_path}")
except Exception as e:
    logger.error(f"❌ Ошибка создания папки: {e}")

DATABASE_URL = f'sqlite:///{db_path}'
logger.info(f"🔗 URL БД: {DATABASE_URL}")

engine = create_engine(DATABASE_URL, echo=True)


SessionLocal = sessionmaker(bind=engine)


Base = declarative_base()

def init_db():
    """Инициализация БД - создание всех таблиц"""

    from database.models import User, Movie, UserRating, UserViewed
    
    logger.info("=" * 50)
    logger.info("СОЗДАНИЕ ТАБЛИЦ В БАЗЕ ДАННЫХ")
    logger.info("=" * 50)
    
    try:

        Base.metadata.create_all(bind=engine)
        logger.info("✅ Команда create_all выполнена")
        

        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"📊 Таблицы в БД после создания: {tables}")
        
        if not tables:
            logger.error("❌ Таблицы не создались!")
            

            logger.info("Пробуем создать таблицы через сырой SQL...")
            with engine.connect() as conn:

                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        telegram_id BIGINT UNIQUE NOT NULL,
                        username VARCHAR,
                        first_name VARCHAR,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_active DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """))

                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS movies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title VARCHAR NOT NULL,
                        title_original VARCHAR,
                        year INTEGER,
                        genre VARCHAR,
                        country VARCHAR,
                        director VARCHAR,
                        description TEXT,
                        poster_url VARCHAR,
                        imdb_rating FLOAT,
                        kinopoisk_rating FLOAT,
                        rotten_tomatoes_rating FLOAT,
                        avg_rating FLOAT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS user_ratings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        movie_id INTEGER,
                        rating INTEGER,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                        FOREIGN KEY(movie_id) REFERENCES movies(id) ON DELETE CASCADE
                    )
                """))
                

                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS user_viewed (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        movie_id INTEGER,
                        viewed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        status VARCHAR,
                        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                        FOREIGN KEY(movie_id) REFERENCES movies(id) ON DELETE CASCADE
                    )
                """))
                
                conn.commit()

            tables = inspector.get_table_names()
            logger.info(f"📊 Таблицы после ручного создания: {tables}")
        else:
            logger.info(f"✅ Таблицы созданы успешно: {tables}")
            

            for table in tables:
                columns = inspector.get_columns(table)
                logger.info(f"  📋 {table}: {[col['name'] for col in columns]}")
                
    except Exception as e:
        logger.error(f"❌ Ошибка при создании таблиц: {e}")
        raise