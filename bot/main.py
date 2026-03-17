#!/usr/bin/env python
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from sqlalchemy import func
import os
from dotenv import load_dotenv


from bot.keyboards import (
    get_main_keyboard, get_genres_keyboard, get_rating_keyboard,
    get_movie_action_keyboard, get_rating_numbers_keyboard
)


load_dotenv()


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


from database.session import init_db, SessionLocal
from database.models import Base, User, Movie, UserRating, UserViewed
from services.recommender import MovieRecommender


try:
    logger.info("Инициализация базы данных...")
    init_db()
    logger.info("База данных инициализирована")
except Exception as e:
    logger.error(f"Ошибка инициализации БД: {e}")
    sys.exit(1)


bot = Bot(
    token=os.getenv("BOT_TOKEN"),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)


dp = Dispatcher(storage=MemoryStorage())


class MovieSelection(StatesGroup):
    choosing_genre = State()
    choosing_rating = State()
    showing_movie = State()
    waiting_for_rating = State()


GENRES_WITH_EMOJI = [
    "Комедия", "Боевик", "Драма", "Ужасы",
    "Фантастика", "Триллер", "Мелодрама", "Детектив",
    "Приключения", "Фэнтези", "Киберпанк", "Мюзикл"
]


GENRES = [g for g in GENRES_WITH_EMOJI]


async def get_or_create_user(telegram_id: int, username: str = None, first_name: str = None):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Новый пользователь: {telegram_id}")
        return user
    finally:
        db.close()


@dp.message(CommandStart())
@dp.message(Command("start"))
@dp.message(F.text.in_(["Начать", "/start"]))
async def cmd_start(message: Message, state: FSMContext):
    logger.info(f"START: User {message.from_user.id}")
    

    await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )
    
    await state.clear()
    
    welcome_text = """
<b>Добро пожаловать в Movie Night Bartender!</b>

Я помогу тебе выбрать идеальный фильм на вечер. 

<b>Как это работает:</b>
1. Выбираешь жанр
2. Указываешь минимальный рейтинг
3. Получаешь рекомендацию!

<b>Используй кнопки ниже для навигации:</b>
• <b>Выбрать фильм</b> - начать подбор
• <b>Моя статистика</b> - просмотренные фильмы и оценки
• <b>Топ фильмов</b> - лучшие фильмы по версии пользователей
• <b>Помощь</b> - список команд
    """
    
    await message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )


@dp.message(Command("select"))
@dp.message(F.text.in_(["Выбрать фильм", "/select"]))
async def cmd_select(message: Message, state: FSMContext):
    """Начало выбора фильма"""
    logger.info(f"SELECT: User {message.from_user.id}")
    
    await state.set_state(MovieSelection.choosing_genre)
    await message.answer(
        "<b>Выбери жанр фильма:</b>\n"
        "Используй кнопки ниже 👇",
        parse_mode="HTML",
        reply_markup=get_genres_keyboard()
    )


@dp.message(MovieSelection.choosing_genre)
async def process_genre(message: Message, state: FSMContext):
    genre_text = message.text
    
    if genre_text == "Отмена":
        await state.clear()
        await message.answer(
            "Выбор отменен. Используй кнопки меню:",
            reply_markup=get_main_keyboard()
        )
        return
    

    genre = genre_text
    

    if genre not in GENRES:
        await message.answer(
            "Пожалуйста, выбери жанр из списка 👇",
            reply_markup=get_genres_keyboard()
        )
        return
    
    await state.update_data(genre=genre)
    logger.info(f"User {message.from_user.id} выбрал жанр: {genre}")
    
    await state.set_state(MovieSelection.choosing_rating)
    await message.answer(
        f"Выбран жанр: {genre_text}\n\n"
        f"<b>Укажи минимальный рейтинг:</b>",
        parse_mode="HTML",
        reply_markup=get_rating_keyboard()
    )


@dp.message(MovieSelection.choosing_rating)
async def process_rating(message: Message, state: FSMContext):
    rating_text = message.text
    
    if rating_text == "Отмена":
        await state.clear()
        await message.answer(
            "Выбор отменен. Используй кнопки меню:",
            reply_markup=get_main_keyboard()
        )
        return
    
    if rating_text == "Любой":
        min_rating = 0.0
    else:
        try:
            min_rating = float(rating_text)
            if min_rating < 0 or min_rating > 10:
                raise ValueError
        except ValueError:
            await message.answer(
                "Пожалуйста, выбери значение из кнопок 👇",
                reply_markup=get_rating_keyboard()
            )
            return
    
    await state.update_data(min_rating=min_rating)
    data = await state.get_data()
    
    logger.info(f"User {message.from_user.id} выбрал рейтинг: {min_rating}")
    
    await message.answer(
        f"<b>Выбор завершен!</b>\n\n"
        f"• Жанр: {data['genre']}\n"
        f"• Мин. рейтинг: {min_rating if min_rating > 0 else 'Любой'}\n\n"
        f"<i>Ищу подходящий фильм...</i>",
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )
    

    await show_recommendation(message, state)


async def show_recommendation(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    

    db = SessionLocal()
    try:
        recommender = MovieRecommender(db)

        movie = recommender.get_recommendation(
            user_id=user_id,
            genre=data.get('genre'),
            min_rating=data.get('min_rating', 0)
        )
        
        if not movie:
            await message.answer(
                "<b>К сожалению, не нашлось фильмов по твоим критериям.</b>\n\n"
                "Попробуй изменить параметры: /select",
                parse_mode="HTML",
                reply_markup=get_main_keyboard()
            )
            await state.clear()
            return
        

        await state.update_data(current_movie_id=movie.id)
        await state.set_state(MovieSelection.showing_movie)
        

        rating_text = f"<b>Рейтинг IMDb:</b> {movie.imdb_rating:.1f}/10\n"
        
        movie_text = f"""
<b>{movie.title}</b> ({movie.year})
<b>Жанр:</b> {movie.genre}
<b>Режиссер:</b> {movie.director or 'Неизвестен'}
{rating_text}
<b>Описание:</b>
<i>{movie.description or 'Описание отсутствует'}</i>
        """
        

        if movie.poster_url and movie.poster_url.startswith(('http://', 'https://')):
            try:
                await message.answer_photo(
                    photo=movie.poster_url,
                    caption=movie_text,
                    reply_markup=get_movie_action_keyboard()
                )
            except Exception as e:
                logger.error(f"Ошибка отправки постера для {movie.title}: {e}")
                await message.answer(
                    movie_text,
                    reply_markup=get_movie_action_keyboard()
                )
        else:
            await message.answer(
                movie_text,
                reply_markup=get_movie_action_keyboard()
            )
            
    finally:
        db.close()


@dp.callback_query(lambda c: c.data in ['watch', 'next', 'reject'])
async def process_movie_action(callback: CallbackQuery, state: FSMContext):
    action = callback.data
    user_id = callback.from_user.id
    
    data = await state.get_data()
    movie_id = data.get('current_movie_id')
    
    if not movie_id:
        await callback.message.edit_text(
            "Что-то пошло не так. Начни заново: /select",
            reply_markup=None
        )
        await state.clear()
        return
    
    db = SessionLocal()
    try:
        recommender = MovieRecommender(db)
        
        if action == 'watch':

            try:
                if callback.message.photo:
                    await callback.message.edit_caption(
                        caption=callback.message.caption + "\n\n<b>Отличный выбор! Приятного просмотра!</b>",
                        parse_mode="HTML",
                        reply_markup=None
                    )
                else:
                    await callback.message.edit_text(
                        callback.message.text + "\n\n<b>Отличный выбор! Приятного просмотра!</b>",
                        parse_mode="HTML",
                        reply_markup=None
                    )
            except:

                await callback.message.answer(
                    "<b>Отличный выбор! Приятного просмотра!</b>",
                    parse_mode="HTML"
                )
            
            await state.set_state(MovieSelection.waiting_for_rating)
            await callback.message.answer(
                "<b>После просмотра не забудь оценить фильм!</b>\n"
                "Просто нажми кнопку ниже 👇",
                parse_mode="HTML",
                reply_markup=get_rating_numbers_keyboard()
            )
            
        elif action == 'next':

            recommender.mark_as_viewed(user_id, movie_id, 'skipped')
            try:
                if callback.message.photo:
                    await callback.message.edit_caption(
                        caption=callback.message.caption + "\n\n<i>Ищу другой фильм...</i>",
                        parse_mode="HTML",
                        reply_markup=None
                    )
                else:
                    await callback.message.edit_text(
                        callback.message.text + "\n\n<i>Ищу другой фильм...</i>",
                        parse_mode="HTML",
                        reply_markup=None
                    )
            except:
                await callback.message.answer("<i>Ищу другой фильм...</i>", parse_mode="HTML")
            
            await show_recommendation(callback.message, state)
            
        elif action == 'reject':

            recommender.mark_as_viewed(user_id, movie_id, 'rejected')
            try:
                if callback.message.photo:
                    await callback.message.edit_caption(
                        caption=callback.message.caption + "\n\n<i>Фильм отклонен. Ищу другой...</i>",
                        parse_mode="HTML",
                        reply_markup=None
                    )
                else:
                    await callback.message.edit_text(
                        callback.message.text + "\n\n<i>Фильм отклонен. Ищу другой...</i>",
                        parse_mode="HTML",
                        reply_markup=None
                    )
            except:
                await callback.message.answer("<i>Фильм отклонен. Ищу другой...</i>", parse_mode="HTML")
            
            await show_recommendation(callback.message, state)
            
    finally:
        db.close()
    
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith('rate_'))
async def process_rating(callback: CallbackQuery, state: FSMContext):
    rating = int(callback.data.split('_')[1])
    user_id = callback.from_user.id
    
    data = await state.get_data()
    movie_id = data.get('current_movie_id')
    
    db = SessionLocal()
    try:
        recommender = MovieRecommender(db)
        recommender.rate_movie(user_id, movie_id, rating)
        
        await callback.message.edit_text(
            f"<b>Спасибо за оценку {rating}/10!</b>\n\n"
            f"Хочешь посмотреть еще фильмы? Используй кнопку 'Выбрать фильм'",
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
    finally:
        db.close()
    
    await callback.answer()


@dp.callback_query(lambda c: c.data == 'skip_rating')
async def skip_rating(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "<b>Хорошего дня!</b>\n\n"
        "Если захочешь еще фильмов - нажми 'Выбрать фильм'",
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )
    await state.clear()
    await callback.answer()


@dp.message(F.text == "Моя статистика")
async def cmd_stats(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            await message.answer(
                "Ты еще не начал пользоваться ботом. Нажми /start",
                reply_markup=get_main_keyboard()
            )
            return
        

        watched_count = db.query(UserViewed).filter_by(
            user_id=user.id, status='watched'
        ).count()
        

        skipped_count = db.query(UserViewed).filter(
            UserViewed.user_id == user.id,
            UserViewed.status.in_(['skipped', 'rejected'])
        ).count()
        

        ratings_count = db.query(UserRating).filter_by(user_id=user.id).count()
        

        avg_rating = db.query(func.avg(UserRating.rating)).filter_by(
            user_id=user.id
        ).scalar() or 0
        

        total_movies = db.query(Movie).count()
        

        recommender = MovieRecommender(db)
        available = recommender.get_available_count(user_id)
        
        stats_text = f"""
<b>Твоя статистика:</b>

<b>Пользователь:</b> {message.from_user.first_name or 'Аноним'}
<b>Просмотрено:</b> {watched_count}
<b>Пропущено:</b> {skipped_count}
<b>Оценок:</b> {ratings_count}
<b>Средняя оценка:</b> {avg_rating:.1f}/10

<b>Всего фильмов в базе:</b> {total_movies}
<b>Доступно для тебя:</b> {available}
        """
        
        await message.answer(stats_text, parse_mode="HTML", reply_markup=get_main_keyboard())
        
    finally:
        db.close()


@dp.message(F.text == "Топ фильмов")
async def cmd_top(message: Message, state: FSMContext):
    db = SessionLocal()
    try:

        top_movies = db.query(Movie).filter(
            Movie.imdb_rating.isnot(None)
        ).order_by(Movie.imdb_rating.desc()).limit(10).all()
        
        text = "<b>Топ 10 фильмов по версии IMDb</b>\n\n"
        
        for i, movie in enumerate(top_movies, 1):
            text += f"{i}. {movie.title} ({movie.year}) — {movie.imdb_rating}/10\n"
        
        text += "\n<b>Топ по версии пользователей</b> скоро появится!"
        
        await message.answer(text, parse_mode="HTML", reply_markup=get_main_keyboard())
        
    finally:
        db.close()


@dp.message(F.text == "Моя история")
async def cmd_history(message: Message):
    user_id = message.from_user.id
    
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            await message.answer("Сначала начни пользоваться ботом: /start")
            return
        
        recommender = MovieRecommender(db)
        watched = recommender.get_watched_movies(user.id)
        
        if not watched:
            await message.answer("Ты еще не посмотрел ни одного фильма!")
            return
        
        text = "<b>Твоя история просмотров:</b>\n\n"
        for i, movie in enumerate(watched, 1):
            text += f"{i}. {movie.title} ({movie.year}) - {movie.imdb_rating}/10\n"
        
        await message.answer(text, parse_mode="HTML")
        
    finally:
        db.close()


@dp.message(F.text == "Помощь")
@dp.message(Command("help"))
async def cmd_help(message: Message):
    help_text = """
<b>Доступные команды:</b>

<b>/start</b> - Начать работу
<b>/select</b> - Выбрать фильм
<b>Моя статистика</b> - твои просмотры и оценки
<b>Топ фильмов</b> - лучшие фильмы
<b>/cancel</b> - отменить текущее действие
<b>/help</b> - показать эту справку

<b>Как пользоваться:</b>
1. Нажми "Выбрать фильм"
2. Выбери жанр из списка
3. Укажи минимальный рейтинг
4. Получи рекомендацию!

<b>После просмотра:</b>
Оцени фильм от 1 до 10 - это поможет другим пользователям!
    """
    
    await message.answer(help_text, parse_mode="HTML", reply_markup=get_main_keyboard())


@dp.message(Command("cancel"))
@dp.message(F.text == "Отмена")
async def cmd_cancel(message: Message, state: FSMContext):
    logger.info(f"cancel от {message.from_user.id}")
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(
            "Нет активного действия",
            reply_markup=get_main_keyboard()
        )
        return
    
    await state.clear()
    await message.answer(
        "Действие отменено. Используй кнопки меню:",
        reply_markup=get_main_keyboard()
    )


@dp.message()
async def echo_all(message: Message):
    logger.info(f"Неизвестная команда: '{message.text}' от {message.from_user.id}")
    await message.answer(
        "Я понимаю только команды из меню.\n"
        "Используй кнопки ниже 👇",
        reply_markup=get_main_keyboard()
    )


async def main():
    logger.info("=" * 50)
    logger.info("ЗАПУСК MOVIE NIGHT BARTENDER")
    logger.info("=" * 50)
    
    try:

        token = os.getenv("BOT_TOKEN")
        if not token:
            logger.error("BOT_TOKEN не найден в .env файле!")
            return
        

        me = await bot.get_me()
        logger.info(f"Бот @{me.username} запущен")
        
        logger.info("=" * 50)
        logger.info("Бот готов к работе!")
        logger.info("Команды: /start, /select, /help, /cancel")
        logger.info("=" * 50)
        
        await dp.start_polling(bot, skip_updates=True)
        
    except Exception as e:
        logger.error(f"Ошибка: {e}", exc_info=True)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")