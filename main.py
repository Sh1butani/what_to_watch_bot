import logging
import os
import sys

import requests
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    Filters,
    MessageHandler,
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


FIRST, SECOND = range(2)


HEADERS = {'X-API-KEY': f'{KINOPOISK_TOKEN}'}
URL = 'https://api.kinopoisk.dev/v1.4/movie/random?notNullFields=name&notNullFields=description&notNullFields=type&notNullFields=year&notNullFields=movieLength'


def start(update, context):
    """Выводит сообщение при команде /start."""
    name = update.message.chat.first_name
    chat = update.effective_chat
    buttons = ReplyKeyboardMarkup(
        [['/findfilm'], ['/randomfilm'], ['/help']],
        resize_keyboard=True)
    context.bot.send_message(
        chat_id=chat.id,
        text='❤️ Спасибо, что включили меня, {} !\n'
        '❔ Чтобы узнать, что я умею, воспользуйтесь командой /help '.format(name),
        reply_markup=buttons
        )


def help(update, context):
    """Отправляет пользователю сообщение с информацией о возможностях бота."""
    chat = update.effective_chat
    context.bot.send_message(
        chat_id=chat.id,
        text=HELP_COMMAND,
        parse_mode='HTML'
    )


def echo(update, context):
    """Отвечает на любое текстовое сообщение пользователя."""
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Воспользуйтесь командой /help для детальной информации.'
        )


def translate_film_type(type):
    """Переводит английское значение типа на русское."""
    return CONTENT_TYPES.get(type, type)


def create_kinopoisk_link(type, genre):
    """Формирует ссылку кинопоиска в зависимости от запросов юзеров."""
    payload = {
        'type': type,
        'genres.name': genre,
    }
    return requests.get(URL, params=payload, headers=HEADERS).json()


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


def get_random_film(update, context, genre=None, type=None):
    """Отправляет пользователю сообщение с данными о рандомном фильме."""
    chat = update.effective_chat
    context.bot.send_message(
        chat_id=chat.id,
        text='Посмотри, какой фильм я тебе нашёл',
        )
    payload = {
        'type': type,
        'genres.name': genre,
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
            'Не удалось получить информацию о фильме. Попробуйте еще раз.'
        )


def start_conversation(update, context):
    """Начинает разговор и спрашивает про тип запроса к API."""
    user = update.message.from_user
    logging.info(f'Пользователь {user.first_name} начал беседу.')
    keyboard = [
        [
            InlineKeyboardButton('Фильм', callback_data='movie'),
            InlineKeyboardButton('Сериал', callback_data='tv-series'),
        ],
        [
            InlineKeyboardButton('Мультсериал', callback_data='animated-series'),
            InlineKeyboardButton('Мульфильм', callback_data='cartoon'),
            ],
        [
            InlineKeyboardButton('Аниме', callback_data='anime'),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        'Давай подберем тебе что-то интересное 😎, для начала выберем тип:',
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
            InlineKeyboardButton('Комедия', callback_data='комедия'),
            InlineKeyboardButton('Боевик', callback_data='боевик'),
        ],
        [
            InlineKeyboardButton('Вестерн', callback_data='вестерн'),
            InlineKeyboardButton('Детектив', callback_data='детектив'),
            ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.reply_text(
        'Отлично, теперь выберите жанр:',
        reply_markup=reply_markup
    )
    return SECOND


def get_filtered_film(update, context):
    query = update.callback_query
    query.answer()
    genre = query.data
    context.user_data['genre'] = genre
    get_random_film(update=update,
                    context=context,
                    genre=context.user_data["genre"],
                    type=context.user_data["type"])
    return ConversationHandler.END


def cancel(update, context):
    update.message.from_user
    update.message.reply_text('Bye! I hope we can talk again some day.')
    return ConversationHandler.END


def main():
    """Основная логика работы бота."""
    updater = Updater(token=TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', help)
    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    random_film_handler = CommandHandler('randomfilm', get_random_film)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('findfilm', start_conversation)],
        states={
            FIRST: [CallbackQueryHandler(choose_genre)],
            SECOND: [CallbackQueryHandler(get_filtered_film)]
        },
        fallbacks=[CommandHandler('findfilm', start_conversation)]
    )

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(echo_handler)
    dispatcher.add_handler(random_film_handler)
    dispatcher.add_handler(conv_handler)

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
