from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_keyboard():
    """Главная клавиатура с основными командами"""
    buttons = [
        [KeyboardButton(text="Начать"), KeyboardButton(text="Выбрать фильм")],
        [KeyboardButton(text="Моя статистика"), KeyboardButton(text="Моя история")],
        [KeyboardButton(text="Топ фильмов"), KeyboardButton(text="Помощь")],
        [KeyboardButton(text="Отмена")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_genres_keyboard():
    """Клавиатура с жанрами"""
    genres = [
        "Комедия", "Боевик", "Драма", "Ужасы",
        "Фантастика", "Триллер", "Мелодрама", "Детектив",
        "Приключения", "Фэнтези", "Киберпанк", "Мюзикл"
    ]

    buttons = []
    for i in range(0, len(genres), 2):
        row = [KeyboardButton(text=genres[i])]
        if i + 1 < len(genres):
            row.append(KeyboardButton(text=genres[i + 1]))
        buttons.append(row)
    buttons.append([KeyboardButton(text="Отмена")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_rating_keyboard():
    """Клавиатура с рейтингом"""
    buttons = [
        [KeyboardButton(text="Любой"), KeyboardButton(text="7.0"), KeyboardButton(text="8.0")],
        [KeyboardButton(text="8.5"), KeyboardButton(text="9.0"), KeyboardButton(text="Отмена")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_movie_action_keyboard():
    """Inline клавиатура для действий с фильмом"""
    buttons = [
        [InlineKeyboardButton(text="Буду смотреть", callback_data="watch")],
        [InlineKeyboardButton(text="Другой фильм", callback_data="next")],
        [InlineKeyboardButton(text="Не интересно", callback_data="reject")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_rating_numbers_keyboard():
    """Inline клавиатура для оценки фильма"""
    buttons = []

    row1 = [InlineKeyboardButton(text=str(i), callback_data=f"rate_{i}") for i in range(1, 6)]
    row2 = [InlineKeyboardButton(text=str(i), callback_data=f"rate_{i}") for i in range(6, 11)]
    buttons.append(row1)
    buttons.append(row2)
    buttons.append([InlineKeyboardButton(text="Пропустить", callback_data="skip_rating")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_back_keyboard():
    """Клавиатура с кнопкой 'Назад' (на всякий случай)"""
    buttons = [[KeyboardButton(text="Назад"), KeyboardButton(text="Отмена")]]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)