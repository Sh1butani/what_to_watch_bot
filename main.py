import logging
import os
import re
import sys

import requests
from dotenv import load_dotenv
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    Filters,
    MessageHandler,
    RegexHandler,
    Updater,
)

load_dotenv("tokens.env")

KINOPOISK_TOKEN = os.getenv('KINOPOISK_TOKEN')
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

HELP_COMMAND = """
<b>/start</b> - <em>Запуск бота</em>
<b>/help</b> - <em>Список команд</em>
<b>/findfilm</b> - <em>Найти фильм или сериал исходя из ваших предпочтений</em>
<b>/randomfilm</b> - <em>Абсолютно рандомный фильм</em>
"""

CONTENT_TYPES = {
    'animated-series': 'мультсериал',
    'anime': 'аниме',
    'cartoon': 'мультфильм',
    'movie': 'фильм',
    'tv-series': 'сериал'
}


FIRST, SECOND, THIRD, FOURTH = range(4)


HEADERS = {'X-API-KEY': f'{KINOPOISK_TOKEN}'}
URL = 'https://api.kinopoisk.dev/v1.4/movie/random?notNullFields=name&notNullFields=description&notNullFields=type&notNullFields=year&notNullFields=movieLength'


def start(update, context):
    """Выводит сообщение при команде /start."""
    name = update.message.chat.first_name
    chat = update.effective_chat
    context.bot.send_message(
        chat_id=chat.id,
        text=f'❤️ Спасибо, что включил меня, {name} !\n'
        '❔ Чтобы узнать, что я умею, воспользуйся командой /help\n'
        '⬇ Для начала воспользуйся кнопкой меню.'
    )


def help(update, context):
    """Отправляет пользователю сообщение с информацией о возможностях бота."""
    chat = update.effective_chat
    context.bot.send_message(
        chat_id=chat.id,
        text=HELP_COMMAND,
        parse_mode='HTML'
    )


def translate_film_type(type):
    """Переводит английское значение типа на русское."""
    return CONTENT_TYPES.get(type, type)


def generate_film_info(film_data):
    """Генерирует информацию о фильме от API кинопоиска."""
    genre_names = [genre.get("name") for genre in film_data.get("genres", [])]
    kp_rating = film_data.get("rating", {}).get("kp")
    imdb_rating = film_data.get("rating", {}).get("imdb")
    imdb_id = film_data.get("externalId").get("imdb") if "imdb" in film_data.get("externalId") else None
    film_info = (
        f'<b>{film_data.get("name")}</b>\n'
        '\n'
        f'<a href="https://www.kinopoisk.ru/film/{film_data.get("id")}">Кинопоиск: {kp_rating}</a>\n'
        f'<a href="https://www.imdb.com/title/{film_data.get("externalId").get("imdb")}">IMDB: {imdb_rating}</a>\n'
        '\n'
        f'<i>Тип:</i> {translate_film_type(film_data.get("type"))}\n'
        f'<i>Жанр:</i> {", ".join(genre_names)}\n'
        f'<i>Продолжительность:</i> {film_data.get("movieLength")} мин\n'
        f'<i>Год:</i> {film_data.get("year")}\n'
        '\n'
        f'{film_data.get("description")}\n'
    )
    return film_info


def get_random_film(
        update, context, genre=None, type=None, country=None, rating=None
        ):
    """Отправляет пользователю сообщение с данными о рандомном фильме."""
    chat = update.effective_chat
    payload = {
        'type': type,
        'genres.name': genre,
        'countries.name': country,
        'rating.kp': rating
    }
    film_data = requests.get(
        URL, params=payload if payload else None, headers=HEADERS
        ).json()

    if film_data:
        photo_url = film_data.get('poster', {}).get('previewUrl', None)
        film_info = generate_film_info(film_data)
        if photo_url:
            context.bot.send_photo(
                chat.id, photo_url, caption=film_info, parse_mode='HTML'
            )
        else:
            context.bot.send_message(chat.id, film_info, parse_mode='HTML')
    else:
        context.bot.send_message(
            chat.id,
            'К сожалению, фильмов с такими параметрами не найдено.'
        )


def start_conversation(update, context):
    """Начинает разговор и спрашивает про тип запроса к API."""
    user = update.message.from_user
    logging.info(f'Пользователь {user.first_name} начал беседу.')
    keyboard = [
        [
            InlineKeyboardButton('Фильм 🎥', callback_data='movie'),
            InlineKeyboardButton('Сериал 📺', callback_data='tv-series'),
        ],
        [
            InlineKeyboardButton('Мультсериал 👧🏻', callback_data='animated-series'),
            InlineKeyboardButton('Мульфильм 👶', callback_data='cartoon'),
            ],
        [
            InlineKeyboardButton('Аниме 🍜', callback_data='anime'),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        'Сейчас подберем тебе что-то интересное 😎\n'
        'Для начала давай выберем, что ты хочешь посмотреть:',
        reply_markup=reply_markup)
    return FIRST


def choose_genre(update, context):
    """Пользователь выбирает жанр и продолжает разговор."""
    query = update.callback_query
    query.answer()
    type = query.data
    context.user_data['type'] = type
    keyboard = [
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
            InlineKeyboardButton('Фентези 🧙‍♂️', callback_data='фентези')
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
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.reply_text(
        'Отлично, теперь выбери жанр:',
        reply_markup=reply_markup
    )
    return SECOND


def choose_country(update, context):
    """Пользователь выбирает страну и продолжает разговор."""
    query = update.callback_query
    query.answer()
    genre = query.data
    if genre == 'skip_genre':
        context.user_data['genre'] = None
    else:
        context.user_data['genre'] = genre
    query.message.reply_text('Теперь введи название страны:')
    return THIRD


def choose_rating(update, context):
    """Пользователь выбирает рейтинг и продолжает разговор."""
    country = update.message.text
    context.user_data['country'] = country
    update.message.reply_text(
        'Давай выберем рейтинг, введи диапазон чисел через дефис, '
        '(например: 7.2-10).')
    return FOURTH


def get_filtered_film(update, context):
    """Получает отфильтрвванный фильм по рейтингу."""
    try:
        rating_text = update.message.text
        match = re.fullmatch(
            r'(10|[1-9](\.[0-9]+)?)(-(10|[1-9](\.[0-9]+)?))?', rating_text
            )
        if match is not None:
            ratings = [float(rating) for rating in rating_text.split('-')]
            if len(ratings) == 2 and ratings[0] > ratings[1]:
                update.message.reply_text(
                    'Нижняя граница диапазона не может быть больше верхней. '
                    'Пожалуйста, введи корректный диапазон.'
                    )
                return FOURTH
            context.user_data['rating'] = rating_text
            get_random_film(update=update,
                            context=context,
                            genre=context.user_data["genre"],
                            type=context.user_data["type"],
                            country=context.user_data['country'],
                            rating=context.user_data['rating'])
            keyboard = [
                [
                    KeyboardButton("Еще один"),
                    KeyboardButton("Начать заново"),
                    KeyboardButton("Главное меню"),
                ]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            update.message.reply_text(
                'Если не понравился, всегда можешь повторить свой запрос 😊',
                reply_markup=reply_markup
            )
            return ConversationHandler.END
        else:
            update.message.reply_text(
                'Пожалуйста, введи число от 1 до 10 или диапазон чисел, '
                'разделенных дефисом (пример: 7, 10, 7.2-10).'
                )
            return FOURTH
    except ValueError:
        update.message.reply_text(
            'Пожалуйста, введи число от 1 до 10 или диапазон чисел, '
            'разделенных дефисом (пример: 7, 10, 7.2-10).'
            )
        return FOURTH


def another_film(update, context):
    """Находит еще один фильм с таким же запросом."""
    get_random_film(update=update,
                    context=context,
                    genre=context.user_data["genre"],
                    type=context.user_data["type"],
                    country=context.user_data['country'],
                    rating=context.user_data['rating'])
    keyboard = [
        [
            KeyboardButton("Еще один"),
            KeyboardButton("Начать заново"),
            KeyboardButton("Главное меню"),
        ]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text(
        'Если не понравился, всегда можешь повторить свой запрос 😊',
        reply_markup=reply_markup
    )


def restart(update, context):
    """Начинает поиск заново."""
    start_conversation(update, context)


def cancel(update, context):
    """Завершает разговор и возвращает пользователя в главное меню."""
    user = update.message.from_user
    logging.info(f'Пользователь {user.first_name} отменил разговор.')
    update.message.reply_text('Ты вернулся в главное меню')
    return ConversationHandler.END


def main():
    """Основная логика работы бота."""
    updater = Updater(token=TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', help)
    random_film_handler = CommandHandler('randomfilm', get_random_film)
    main_menu_handler = RegexHandler('^Главное меню$', cancel)
    restart_handler = RegexHandler('^Начать заново$', restart)
    another_film_handler = RegexHandler('^Еще один$', another_film)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('findfilm', start_conversation)],
        states={
            FIRST: [
                CallbackQueryHandler(choose_genre, pass_user_data=True)
                ],
            SECOND: [
                CallbackQueryHandler(choose_country, pass_user_data=True)
                ],
            THIRD: [
                MessageHandler(Filters.text & ~Filters.command,
                               choose_rating, pass_user_data=True)
                               ],
            FOURTH: [
                MessageHandler(Filters.text & ~Filters.command,
                               get_filtered_film, pass_user_data=True)
                               ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(random_film_handler)
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(main_menu_handler)
    dispatcher.add_handler(restart_handler)
    dispatcher.add_handler(another_film_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s ['
        '%(filename)s:%(lineno)d - %(funcName)s]',
        level=logging.DEBUG,
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    main()
