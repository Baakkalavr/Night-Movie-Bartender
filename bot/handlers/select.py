from aiogram import Router, F
from aiogram.filters import Command
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

@router.message(Command("select"))
@router.message(F.text == "/select")
async def cmd_select(message: Message, state: FSMContext):
    
    logger.info(f"🎬 SELECT: Пользователь {message.from_user.id} начал выбор")
    
    await state.set_state(MovieSelection.choosing_genre)
    await message.answer(
        "🎭 Выбери жанр фильма:",
        reply_markup=get_genres_keyboard()
    )
