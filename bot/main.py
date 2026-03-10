#!/usr/bin/env python
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


from database.session import init_db, SessionLocal
from database.models import Base


from database.models import User, Movie, UserRating, UserViewed


try:
    logger.info("🔄 Инициализация базы данных...")
    init_db()
    logger.info("✅ База данных инициализирована")
except Exception as e:
    logger.error(f"❌ Ошибка инициализации БД: {e}")
    sys.exit(1)


try:
    from database.seed import seed_movies
    logger.info("🔄 Загрузка тестовых данных...")
    seed_movies()
    logger.info("✅ Тестовые данные загружены")
except Exception as e:
    logger.error(f"❌ Ошибка загрузки тестовых данных: {e}")


from services.recommender import MovieRecommender


bot = Bot(
    token=os.getenv("BOT_TOKEN"),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher(storage=MemoryStorage())


class MovieSelection(StatesGroup):
    choosing_genre = State()
    choosing_country = State()
    choosing_rating = State()
    showing_movie = State()
    waiting_for_rating = State()


GENRES = [
    "Комедия", "Боевик", "Драма", "Ужасы", 
    "Фантастика", "Триллер", "Мелодрама", "Детектив"
]


COUNTRIES = ["США", "Россия", "Великобритания", "Франция", "Другая"]

def get_genres_keyboard():
    """Клавиатура с жанрами"""
    buttons = [[KeyboardButton(text=genre)] for genre in GENRES]
    buttons.append([KeyboardButton(text="❌ Отмена")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_countries_keyboard():
    """Клавиатура со странами"""
    buttons = [[KeyboardButton(text=country)] for country in COUNTRIES]
    buttons.append([KeyboardButton(text="❌ Отмена")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_rating_keyboard():
    """Клавиатура с рейтингом"""
    buttons = [
        [KeyboardButton(text="7.0"), KeyboardButton(text="7.5")],
        [KeyboardButton(text="8.0"), KeyboardButton(text="8.5")],
        [KeyboardButton(text="Не важно"), KeyboardButton(text="❌ Отмена")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_movie_action_keyboard():
    """Клавиатура для действий с фильмом"""
    buttons = [
        [InlineKeyboardButton(text="✅ Буду смотреть", callback_data="watch")],
        [InlineKeyboardButton(text="🔄 Другой фильм", callback_data="next")],
        [InlineKeyboardButton(text="❌ Не интересно", callback_data="reject")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_rating_numbers_keyboard():
    """Клавиатура для оценки фильма"""
    buttons = []
    row1 = [InlineKeyboardButton(text=str(i), callback_data=f"rate_{i}") for i in range(1, 6)]
    row2 = [InlineKeyboardButton(text=str(i), callback_data=f"rate_{i}") for i in range(6, 11)]
    buttons.append(row1)
    buttons.append(row2)
    buttons.append([InlineKeyboardButton(text="❌ Пропустить", callback_data="skip_rating")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def get_or_create_user(telegram_id: int, username: str = None, first_name: str = None):
    """Получить или создать пользователя в БД"""
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
            logger.info(f"👤 Новый пользователь: {telegram_id}")
        return user
    finally:
        db.close()


@dp.message(CommandStart())
@dp.message(Command("start"))
@dp.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    logger.info(f"🔥 START: User {message.from_user.id}")
    
    await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )
    
    await state.clear()
    
    welcome_text = """
🎬 <b>Добро пожаловать в Movie Night Bartender!</b>

Я помогу тебе выбрать идеальный фильм на вечер. 

<b>Как это работает:</b>
1️⃣ Ты выбираешь жанр фильма
2️⃣ Выбираешь страну производства
3️⃣ Указываешь минимальный рейтинг
4️⃣ Я предлагаю тебе фильм с учетом рейтингов
5️⃣ Ты решаешь - смотреть или искать другой
6️⃣ После просмотра оцениваешь фильм

<b>Чтобы начать подбор, нажми /select</b>
    """
    
    await message.answer(welcome_text, parse_mode="HTML")


@dp.message(Command("select"))
@dp.message(F.text == "/select")
async def cmd_select(message: Message, state: FSMContext):
    """Начало выбора фильма"""
    logger.info(f"🎬 SELECT: User {message.from_user.id}")
    
    await state.set_state(MovieSelection.choosing_genre)
    await message.answer(
        "🎭 Выбери жанр фильма:",
        reply_markup=get_genres_keyboard()
    )


@dp.message(MovieSelection.choosing_genre)
async def process_genre(message: Message, state: FSMContext):
    """Обработка выбора жанра"""
    genre = message.text
    
    if genre == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ Выбор отменен. Чтобы начать заново, нажми /select",
            reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="/start")]], resize_keyboard=True)
        )
        return
    
    if genre not in GENRES:
        await message.answer(
            "Пожалуйста, выбери жанр из списка или нажми 'Отмена'",
            reply_markup=get_genres_keyboard()
        )
        return
    
    await state.update_data(genre=genre)
    logger.info(f"🎭 User {message.from_user.id} выбрал жанр: {genre}")
    
    await state.set_state(MovieSelection.choosing_country)
    await message.answer(
        f"✅ Выбран жанр: {genre}\n\n🌍 Теперь выбери страну производства:",
        reply_markup=get_countries_keyboard()
    )


@dp.message(MovieSelection.choosing_country)
async def process_country(message: Message, state: FSMContext):
    """Обработка выбора страны"""
    country = message.text
    
    if country == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ Выбор отменен. Чтобы начать заново, нажми /select",
            reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="/start")]], resize_keyboard=True)
        )
        return
    
    if country not in COUNTRIES:
        await message.answer(
            "Пожалуйста, выбери страну из списка или нажми 'Отмена'",
            reply_markup=get_countries_keyboard()
        )
        return
    
    await state.update_data(country=country)
    logger.info(f"🌍 User {message.from_user.id} выбрал страну: {country}")
    
    await state.set_state(MovieSelection.choosing_rating)
    
    data = await state.get_data()
    await message.answer(
        f"✅ Выбрано:\n• Жанр: {data['genre']}\n• Страна: {country}\n\n⭐ Укажи минимальный рейтинг (от 1 до 10):",
        reply_markup=get_rating_keyboard()
    )


@dp.message(MovieSelection.choosing_rating)
async def process_rating(message: Message, state: FSMContext):
    """Обработка выбора рейтинга"""
    rating_text = message.text
    
    if rating_text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ Выбор отменен. Чтобы начать заново, нажми /select",
            reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="/start")]], resize_keyboard=True)
        )
        return
    
    if rating_text == "Не важно":
        min_rating = 0.0
    else:
        try:
            min_rating = float(rating_text)
            if min_rating < 0 or min_rating > 10:
                raise ValueError
        except ValueError:
            await message.answer(
                "Пожалуйста, введи число от 0 до 10 или выбери 'Не важно'",
                reply_markup=get_rating_keyboard()
            )
            return
    
    await state.update_data(min_rating=min_rating)
    data = await state.get_data()
    
    logger.info(f"⭐ User {message.from_user.id} выбрал рейтинг: {min_rating}")
    
    await message.answer(
        f"✅ <b>Выбор завершен!</b>\n\n"
        f"• Жанр: {data['genre']}\n"
        f"• Страна: {data['country']}\n"
        f"• Мин. рейтинг: {min_rating if min_rating > 0 else 'Не важно'}\n\n"
        f"🔍 Ищу подходящий фильм...",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="/start")]], resize_keyboard=True)
    )
    

    await show_recommendation(message, state)

async def show_recommendation(message: Message, state: FSMContext):
    """Показать рекомендацию фильма"""
    data = await state.get_data()
    user_id = message.from_user.id
    
    db = SessionLocal()
    try:
        recommender = MovieRecommender(db)
        movie = recommender.get_recommendation(
            user_id=user_id,
            genre=data.get('genre'),
            country=data.get('country'),
            min_rating=data.get('min_rating', 0)
        )
        
        if not movie:
            await message.answer(
                "😕 К сожалению, не нашлось фильмов по твоим критериям.\n"
                "Попробуй изменить параметры: /select"
            )
            await state.clear()
            return
        
        await state.update_data(current_movie_id=movie.id)
        await state.set_state(MovieSelection.showing_movie)
        
        rating_text = f"⭐ <b>Рейтинг:</b> {movie.avg_rating:.1f}/10\n"
        if movie.imdb_rating:
            rating_text += f"   • IMDB: {movie.imdb_rating}\n"
        if movie.kinopoisk_rating:
            rating_text += f"   • Кинопоиск: {movie.kinopoisk_rating}\n"
        if movie.rotten_tomatoes_rating:
            rating_text += f"   • Rotten Tomatoes: {movie.rotten_tomatoes_rating}%\n"
        
        movie_text = f"""
🎬 <b>{movie.title}</b> ({movie.year})
🎭 <b>Жанр:</b> {movie.genre}
🌍 <b>Страна:</b> {movie.country}
🎪 <b>Режиссер:</b> {movie.director}
{rating_text}
📝 <b>Описание:</b>
{movie.description}
        """
        
        if movie.poster_url:
            await message.answer_photo(
                photo=movie.poster_url,
                caption=movie_text,
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
    """Обработка действий с фильмом"""
    action = callback.data
    user_id = callback.from_user.id
    
    data = await state.get_data()
    movie_id = data.get('current_movie_id')
    
    if not movie_id:
        await callback.message.edit_text("❌ Что-то пошло не так. Начни заново: /select")
        await state.clear()
        return
    
    db = SessionLocal()
    try:
        recommender = MovieRecommender(db)
        
        if action == 'watch':
            if callback.message.photo:
                await callback.message.edit_caption(
                    caption=callback.message.caption + "\n\n✅ Отличный выбор! Приятного просмотра!",
                    reply_markup=None
                )
            else:
                await callback.message.edit_text(
                    callback.message.text + "\n\n✅ Отличный выбор! Приятного просмотра!",
                    reply_markup=None
                )
            await state.set_state(MovieSelection.waiting_for_rating)
            
        elif action == 'next':
            
            recommender.mark_as_viewed(user_id, movie_id, 'skipped')
            if callback.message.photo:
                await callback.message.edit_caption(
                    caption=callback.message.caption + "\n\n🔄 Ищу другой фильм...",
                    reply_markup=None
                )
            else:
                await callback.message.edit_text(
                    callback.message.text + "\n\n🔄 Ищу другой фильм...",
                    reply_markup=None
                )
            await show_recommendation(callback.message, state)
            
        elif action == 'reject':
            
            recommender.mark_as_viewed(user_id, movie_id, 'rejected')
            if callback.message.photo:
                await callback.message.edit_caption(
                    caption=callback.message.caption + "\n\n❌ Фильм отклонен. Ищу другой...",
                    reply_markup=None
                )
            else:
                await callback.message.edit_text(
                    callback.message.text + "\n\n❌ Фильм отклонен. Ищу другой...",
                    reply_markup=None
                )
            await show_recommendation(callback.message, state)
            
    finally:
        db.close()
    
    await callback.answer()

@dp.message(MovieSelection.waiting_for_rating)
async def request_rating(message: Message, state: FSMContext):
    """Запрос оценки после просмотра"""
    await message.answer(
        "🍿 Как тебе фильм? Оцени его от 1 до 10:",
        reply_markup=get_rating_numbers_keyboard()
    )

@dp.callback_query(lambda c: c.data.startswith('rate_'))
async def process_rating(callback: CallbackQuery, state: FSMContext):
    """Обработка оценки фильма"""
    rating = int(callback.data.split('_')[1])
    user_id = callback.from_user.id
    
    data = await state.get_data()
    movie_id = data.get('current_movie_id')
    
    db = SessionLocal()
    try:
        recommender = MovieRecommender(db)
        recommender.rate_movie(user_id, movie_id, rating)
        
        await callback.message.edit_text(
            f"✅ Спасибо за оценку {rating}/10!\n\n"
            f"Хочешь посмотреть еще фильмы? Нажми /select"
        )
        await state.clear()
    finally:
        db.close()
    
    await callback.answer()

@dp.callback_query(lambda c: c.data == 'skip_rating')
async def skip_rating(callback: CallbackQuery, state: FSMContext):
    """Пропустить оценку"""
    await callback.message.edit_text(
        "👋 Хорошего дня! Если захочешь еще фильмов - нажми /select"
    )
    await state.clear()
    await callback.answer()


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    logger.info(f"📨 help от {message.from_user.id}")
    await message.answer(
        "📋 <b>Доступные команды:</b>\n\n"
        "/start - Начать работу\n"
        "/select - Выбрать фильм\n"
        "/help - Показать эту справку\n"
        "/cancel - Отменить текущее действие\n"
        "/stats - Моя статистика (скоро)\n"
        "/top - Топ фильмов (скоро)"
    )

@dp.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Отмена текущего действия"""
    logger.info(f"📨 cancel от {message.from_user.id}")
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("❌ Нет активного действия")
        return
    
    await state.clear()
    await message.answer(
        "❌ Действие отменено. Чтобы начать заново, нажми /select",
        reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="/start")]], resize_keyboard=True)
    )

@dp.message()
async def echo_all(message: Message):
    """Обработчик всех остальных сообщений"""
    logger.info(f"❌ Неизвестная команда: '{message.text}' от {message.from_user.id}")
    await message.answer(
        "❌ Я понимаю только команды.\n"
        "Используй /help для списка команд."
    )

async def main():
    """Главная функция запуска бота"""
    logger.info("=" * 50)
    logger.info("🚀 ЗАПУСК MOVIE NIGHT BARTENDER")
    logger.info("=" * 50)
    
    try:

        token = os.getenv("BOT_TOKEN")
        if not token:
            logger.error("❌ BOT_TOKEN не найден в .env файле!")
            return
        

        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"🔄 Попытка подключения {attempt + 1}/{max_retries}...")
                me = await bot.get_me()
                logger.info(f"✅ Бот @{me.username} запущен")
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"❌ Не удалось подключиться после {max_retries} попыток: {e}")
                    return
                logger.warning(f"⚠️ Ошибка подключения, повтор через 5 секунд...")
                await asyncio.sleep(5)
        
        logger.info("=" * 50)
        logger.info("🤖 Бот готов к работе!")
        logger.info("📝 Команды: /start, /select, /help, /cancel")
        logger.info("=" * 50)
        
        await dp.start_polling(bot, skip_updates=True)
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}", exc_info=True)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")