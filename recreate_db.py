#!/usr/bin/env python
import os
import logging
from database.session import init_db, SessionLocal
from database.models import Base
from database.seed import seed_movies

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recreate_database():
    """Пересоздание БД с оптимизированной структурой"""
    logger.info("=" * 50)
    logger.info("ПЕРЕСОЗДАНИЕ БАЗЫ ДАННЫХ")
    logger.info("=" * 50)
    
 
    db_path = 'data/movies.db'
    if os.path.exists(db_path):
        os.remove(db_path)
        logger.info(f"✅ Удалена старая БД: {db_path}")
    

    logger.info("🔄 Создание новой БД с индексами...")
    init_db()
    

    logger.info("🔄 Заполнение тестовыми данными...")
    seed_movies()
    
    logger.info("=" * 50)
    logger.info("✅ БД успешно пересоздана и оптимизирована!")
    logger.info("=" * 50)

if __name__ == "__main__":
    recreate_database()