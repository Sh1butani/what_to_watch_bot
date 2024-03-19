from telegram import InlineKeyboardButton, KeyboardButton


keyboard_film_type = [
    [
        InlineKeyboardButton('Фильм 🎥', callback_data='movie'),
        InlineKeyboardButton('Сериал 📺', callback_data='tv-series'),
    ],
    [
        InlineKeyboardButton(
            'Мультсериал 👧🏻', callback_data='animated-series'
        ),
        InlineKeyboardButton('Мульфильм 👶', callback_data='cartoon'),
    ],
    [
        InlineKeyboardButton('Аниме 🍜', callback_data='anime'),
    ],
]

keyboard_film_genre = [
    [
        InlineKeyboardButton('Комедия 😂', callback_data='комедия'),
        InlineKeyboardButton('Боевик 🔫', callback_data='боевик'),
        InlineKeyboardButton('Драма 😢', callback_data='драма')
    ],
    [
        InlineKeyboardButton('Ужасы 😱', callback_data='ужасы'),
        InlineKeyboardButton('Детектив 🕵️‍♂️', callback_data='детектив'),
        InlineKeyboardButton('Фантастика 👽', callback_data='фантастика')
    ],
    [
        InlineKeyboardButton('Вестерн 🤠', callback_data='вестерн'),
        InlineKeyboardButton('Военный 🎖️', callback_data='военный'),
        InlineKeyboardButton('Фэнтези 🧙‍♂️', callback_data='фэнтези')
    ],
    [
        InlineKeyboardButton('История 🏰', callback_data='история'),
        InlineKeyboardButton('Мелодрама ❤️', callback_data='мелодрама'),
        InlineKeyboardButton('Криминал 🚔', callback_data='криминал')
    ],
    [
        InlineKeyboardButton('Пропустить ⏩', callback_data='skip_genre'),
    ]
]

keyboard_menu = [
    [
        KeyboardButton("Еще один"),
        KeyboardButton("Начать заново"),
        KeyboardButton("Главное меню"),
    ]
]
