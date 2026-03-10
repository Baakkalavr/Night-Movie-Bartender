from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging


router = Router()
logger = logging.getLogger(__name__)


class MovieSelection(StatesGroup):
    choosing_genre = State()
    choosing_country = State()
    choosing_rating = State()


GENRES = [
    "Комедия", "Боевик", "Драма", "Ужасы", 
    "Фантастика", "Триллер", "Мелодрама", "Детектив"
]


def get_genres_keyboard():
    buttons = [[KeyboardButton(text=genre)] for genre in GENRES]
    buttons.append([KeyboardButton(text="❌ Отмена")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


@router.message(CommandStart())
@router.message(Command("start"))
@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    logger.info(f"🔥 START сработал! User: {message.from_user.id}")
    await state.clear()
    
    welcome_text = """
🎬 <b>Добро пожаловать в Movie Night Bartender!</b>

Я помогу тебе выбрать идеальный фильм на вечер. 

<b>Как это работает:</b>
1️⃣ Ты выбираешь жанр фильма
2️⃣ Выбираешь страну производства
3️⃣ Указываешь минимальный рейтинг
4️⃣ Я предлагаю тебе фильм с учетом рейтингов

<b>Чтобы начать подбор, нажми /select</b>
    """
    
    await message.answer(welcome_text, parse_mode="HTML")


@router.message(Command("select"))
@router.message(F.text == "/select")
async def cmd_select(message: Message, state: FSMContext):
    """Начало выбора фильма"""
    logger.info(f"🎬 SELECT сработал! User: {message.from_user.id}")
    
    await state.set_state(MovieSelection.choosing_genre)
    await message.answer(
        "🎭 Выбери жанр фильма:",
        reply_markup=get_genres_keyboard()
    )


@router.message(MovieSelection.choosing_genre)
async def process_genre(message: Message, state: FSMContext):
    """Обработка выбора жанра"""
    genre = message.text
    logger.debug(f"process_genre вызван с текстом: {genre}")
    
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
    logger.info(f"🎭 Пользователь {message.from_user.id} выбрал жанр: {genre}")
    
    await state.set_state(MovieSelection.choosing_country)
    
    countries_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="США"), KeyboardButton(text="Россия")],
            [KeyboardButton(text="Великобритания"), KeyboardButton(text="Франция")],
            [KeyboardButton(text="Другая"), KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        f"✅ Выбран жанр: {genre}\n\n🌍 Теперь выбери страну производства:",
        reply_markup=countries_keyboard
    )


@router.message(MovieSelection.choosing_country)
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
    
    await state.update_data(country=country)
    logger.info(f"🌍 Пользователь {message.from_user.id} выбрал страну: {country}")
    
    await state.set_state(MovieSelection.choosing_rating)
    
    rating_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="7.0"), KeyboardButton(text="7.5")],
            [KeyboardButton(text="8.0"), KeyboardButton(text="8.5")],
            [KeyboardButton(text="Не важно"), KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )
    
    data = await state.get_data()
    await message.answer(
        f"✅ Выбрано:\n• Жанр: {data['genre']}\n• Страна: {country}\n\n⭐ Укажи минимальный рейтинг (от 1 до 10):",
        reply_markup=rating_keyboard
    )


@router.message(MovieSelection.choosing_rating)
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
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="7.0"), KeyboardButton(text="8.0")],
                             [KeyboardButton(text="Не важно"), KeyboardButton(text="❌ Отмена")]],
                    resize_keyboard=True
                )
            )
            return
    
    await state.update_data(min_rating=min_rating)
    data = await state.get_data()
    
    logger.info(f"⭐ Пользователь {message.from_user.id} выбрал рейтинг: {min_rating}")
    
    await state.clear()
    
    await message.answer(
        f"✅ <b>Выбор завершен!</b>\n\n"
        f"• Жанр: {data['genre']}\n"
        f"• Страна: {data['country']}\n"
        f"• Мин. рейтинг: {min_rating if min_rating > 0 else 'Не важно'}\n\n"
        f"🔍 Ищу подходящий фильм...",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="/start")]], resize_keyboard=True)
    )
    
    await message.answer(
        "🎬 Пока это демо-версия. В следующем обновлении здесь будет реальный поиск фильмов!\n\n"
        "А пока можешь попробовать выбрать другие параметры: /select"
    )