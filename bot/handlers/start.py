from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
import logging


router = Router()
logger = logging.getLogger(__name__)

@router.message(CommandStart())
@router.message(Command("start"))
@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    logger.info(f"🔥 START: Пользователь {message.from_user.id}")
    
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