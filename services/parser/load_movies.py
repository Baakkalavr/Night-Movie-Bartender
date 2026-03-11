#!/usr/bin/env python
import asyncio
import logging
import argparse
from services.parser.movie_loader import MovieLoader

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    parser = argparse.ArgumentParser(description='Загрузчик фильмов')
    parser.add_argument('--popular', type=int, help='Загрузить популярные фильмы (укажи количество)', default=0)
    parser.add_argument('--search', type=str, help='Поиск и загрузка конкретного фильма')
    parser.add_argument('--update-ratings', action='store_true', help='Обновить рейтинги для всех фильмов')
    
    args = parser.parse_args()
    
    loader = MovieLoader()
    
    if args.popular > 0:
        await loader.load_popular_movies(limit=args.popular)
    
    if args.search:
        result = await loader.search_and_load(args.search)
        if result:
            logger.info(f"✅ Фильм загружен: {result['title']}")
        else:
            logger.error(f"❌ Не удалось загрузить фильм: {args.search}")
    
    if args.update_ratings:
        await loader.update_all_ratings()

if __name__ == "__main__":
    asyncio.run(main())