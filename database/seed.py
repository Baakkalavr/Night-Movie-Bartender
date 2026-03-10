from database.session import SessionLocal
from database.models import Movie
import logging
from sqlalchemy import inspect

logger = logging.getLogger(__name__)

SAMPLE_MOVIES = [
    {
        "title": "Побег из Шоушенка",
        "title_original": "The Shawshank Redemption",
        "year": 1994,
        "genre": "Драма",
        "country": "США",
        "director": "Фрэнк Дарабонт",
        "description": "Бухгалтер Энди Дюфрейн обвинён в убийстве собственной жены и её любовника. Оказавшись в тюрьме под названием Шоушенк, он сталкивается с жестокостью и несправедливостью, окружающими заключённых.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BNDE3ODcxYzMtY2YzZC00NmNlLWJiNDMtZDViZWM2MzIxZDYwXkEyXkFqcGdeQXVyNjAwNDUxODI@._V1_.jpg",
        "imdb_rating": 9.3,
        "kinopoisk_rating": 9.1,
        "rotten_tomatoes_rating": 91,
        "avg_rating": 9.2
    },
    {
        "title": "Крёстный отец",
        "title_original": "The Godfather",
        "year": 1972,
        "genre": "Драма",
        "country": "США",
        "director": "Фрэнсис Форд Коппола",
        "description": "Криминальная сага, повествующая о нью-йоркской сицилийской мафиозной семье Корлеоне. Дон Вито Корлеоне вынужден передать дела своему сыну Майклу.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BM2MyNjYxNmUtYTAwNi00MTYxLWJmNWYtYzZlODY3ZTk3OTFlXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_.jpg",
        "imdb_rating": 9.2,
        "kinopoisk_rating": 8.9,
        "rotten_tomatoes_rating": 98,
        "avg_rating": 9.3
    },
    {
        "title": "Тёмный рыцарь",
        "title_original": "The Dark Knight",
        "year": 2008,
        "genre": "Боевик",
        "country": "США",
        "director": "Кристофер Нолан",
        "description": "Бэтмен поднимает ставки в войне с преступностью. С помощью лейтенанта Джима Гордона и прокурора Харви Дента он намерен очистить улицы Готэма от преступности.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BMTMxNTMwODM0NF5BMl5BanBnXkFtZTcwODAyMTk2Mw@@._V1_.jpg",
        "imdb_rating": 9.0,
        "kinopoisk_rating": 8.7,
        "rotten_tomatoes_rating": 94,
        "avg_rating": 9.0
    },
    {
        "title": "Криминальное чтиво",
        "title_original": "Pulp Fiction",
        "year": 1994,
        "genre": "Триллер",
        "country": "США",
        "director": "Квентин Тарантино",
        "description": "Несколько связанных историй из жизни бандитов, таинственных чемоданов и гамбургеров.",
        "poster_url": "https://m.media-amazon.com/images/M/MV5BNGNhMDIzZTUtNTBlZi00MTRlLWFjM2ItYzViMjE3YzI5MjljXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_.jpg",
        "imdb_rating": 8.9,
        "kinopoisk_rating": 8.7,
        "rotten_tomatoes_rating": 92,
        "avg_rating": 8.9
    },
    {
        "title": "Брат",
        "title_original": "Brat",
        "year": 1997,
        "genre": "Боевик",
        "country": "Россия",
        "director": "Алексей Балабанов",
        "description": "Демобилизованный из армии Данила Багров возвращается в родной город и узнаёт, что его старший брат работает наёмным убийцей.",
        "poster_url": "https://avatars.mds.yandex.net/get-kinopoisk-image/1599028/1b1f5d3f-1f4b-4b5c-8f5a-5c5d5b5a5c5e/orig",
        "imdb_rating": 7.8,
        "kinopoisk_rating": 8.2,
        "rotten_tomatoes_rating": 75,
        "avg_rating": 7.8
    },
    {
        "title": "Ирония судьбы",
        "title_original": "Ironiya sudby",
        "year": 1975,
        "genre": "Комедия",
        "country": "Россия",
        "director": "Эльдар Рязанов",
        "description": "Под Новый год компания друзей отправляется в баню. По традиции, после бани все едут в Москву, но Женю случайно отправляют в Ленинград.",
        "poster_url": "https://avatars.mds.yandex.net/get-kinopoisk-image/1599028/1b1f5d3f-1f4b-4b5c-8f5a-5c5d5b5a5c5e/orig",
        "imdb_rating": 7.9,
        "kinopoisk_rating": 8.0,
        "rotten_tomatoes_rating": 80,
        "avg_rating": 8.0
    }
]

def seed_movies():
    """Заполняет базу тестовыми фильмами (оптимизированная версия)"""
    logger.info("=" * 50)
    logger.info("ЗАГРУЗКА ТЕСТОВЫХ ДАННЫХ")
    logger.info("=" * 50)
    
    db = SessionLocal()
    try:

        inspector = inspect(db.bind)
        if 'movies' not in inspector.get_table_names():
            logger.error("❌ Таблица movies не существует!")
            return
        

        count = db.query(Movie).count()
        logger.info(f"Текущее количество фильмов в БД: {count}")
        
        if count > 0:
            logger.info(f"В базе уже есть {count} фильмов. Пропускаем заполнение.")
            return
        

        movies = [Movie(**movie_data) for movie_data in SAMPLE_MOVIES]
        db.bulk_save_objects(movies)
        db.commit()
        
        logger.info(f"✅ Добавлено {len(SAMPLE_MOVIES)} тестовых фильмов")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при заполнении БД: {e}")
        db.rollback()
    finally:
        db.close()