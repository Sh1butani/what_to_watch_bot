import datetime
import logging
import os
import re
import sys
import requests

from http import HTTPStatus
from dotenv import load_dotenv
from telegram import (
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
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

from utils.exceptions import HTTPRequestError
from utils.keyboards import (
    keyboard_film_genre,
    keyboard_film_type,
    keyboard_menu,
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


FIRST, SECOND, THIRD, FOURTH = range(4)


HEADERS = {'X-API-KEY': f'{KINOPOISK_TOKEN}'}
URL = ('https://api.kinopoisk.dev/v1.4/movie/random?notNullFields=name&'
       'notNullFields=description&notNullFields=type')


def check_tokens():
    """Проверяет доступность переменных окружения."""
    source = ("KINOPOISK_TOKEN", "TELEGRAM_TOKEN", "TELEGRAM_CHAT_ID")
    missing_tokens = [token for token in source if not globals()[token]]

    if missing_tokens:
        error_message = (
            'Отсутствуют обязательные переменные окружения:'
            f'{", ".join(missing_tokens)}'
        )
        logging.critical(error_message)
        exit(error_message)


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
    logging.info(f"Пользователь {name} запустил бота.")


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
    content_types = {
        'animated-series': 'мультсериал',
        'anime': 'аниме',
        'cartoon': 'мультфильм',
        'movie': 'фильм',
        'tv-series': 'сериал'
    }
    return content_types.get(type, type)


def generate_film_info(film_data):
    """Генерирует информацию о фильме от API кинопоиска."""
    genre_names = [
        genre.get("name") for genre in film_data.get("genres", [])
    ]
    kp_rating = film_data.get("rating", {}).get("kp")
    imdb_rating = film_data.get("rating", {}).get("imdb")
    kp_link = (
        f'<a href="https://www.kinopoisk.ru/film/{film_data.get("id")}">'
        f'Кинопоиск: {kp_rating}</a>\n' if film_data.get("id")
        else f'Кинопоиск: {kp_rating}\n'
    )
    imdb_link = (
        f'<a href="https://www.imdb.com/title/'
        f'{film_data.get("externalId").get("imdb")}">'
        f'IMDB: {imdb_rating}</a>\n' if film_data.get("externalId") and
        film_data.get("externalId").get("imdb")
        else f'IMDB: {imdb_rating}\n'
    )
    film_length = (
        f'<i>Продолжительность:</i> {film_data.get("movieLength")} мин\n'
        if film_data.get("movieLength") else ''
    )
    film_info = (
        f'<b>{film_data.get("name")}</b>\n'
        '\n'
        f'{kp_link}'
        f'{imdb_link}'
        '\n'
        f'<i>Тип:</i> {translate_film_type(film_data.get("type"))}\n'
        f'<i>Жанр:</i> {", ".join(genre_names)}\n'
        f'{film_length}'
        f'<i>Год:</i> {film_data.get("year")}\n'
        '\n'
        f'{film_data.get("description")}\n'
    )
    return film_info


def get_random_film(
        update, context, genre=None, type=None, year=None, rating=None
):
    """Отправляет пользователю сообщение с данными о рандомном фильме."""
    chat = update.effective_chat
    payload = {
        'type': type,
        'genres.name': genre,
        'year': year,
        'rating.kp': rating
    }

    try:
        response = requests.get(
            URL, params=payload if payload else None, headers=HEADERS
        )
        response.raise_for_status()
        film_data = response.json()

        if film_data:
            photo_url = film_data.get('poster', {}).get('previewUrl', None)
            film_info = generate_film_info(film_data)
            if photo_url:
                context.bot.send_photo(
                    chat.id, photo_url, caption=film_info, parse_mode='HTML'
                )
            else:
                context.bot.send_message(chat.id, film_info, parse_mode='HTML')
            logging.info(f"Отправлен запрос на {URL} с параметрами {payload}")
        else:
            context.bot.send_message(
                chat.id,
                'К сожалению, фильмов с такими параметрами не найдено.'
            )
            logging.warning("Фильмов с указанными параметрами не найдено.")

    except requests.exceptions.RequestException:
        ConnectionError(
            f'Ошибка при доступе к эндпоинту: {URL},'
            f'параметры запроса: {payload}.'
        )

        if response.status_code != HTTPStatus.OK:
            raise HTTPRequestError(response)
        return response.json()


def start_conversation(update, context):
    """Начинает разговор и спрашивает про тип запроса."""
    user = update.message.from_user
    logging.info(f'Пользователь {user.first_name} начал выбирать фильм.')
    reply_markup = InlineKeyboardMarkup(keyboard_film_type)
    update.message.reply_text(
        'Сейчас подберем тебе что-то интересное 😎\n'
        'Давай для начала выберем, что ты хочешь посмотреть:',
        reply_markup=reply_markup)
    return FIRST


def choose_genre(update, context):
    """Пользователь выбирает жанр и продолжает разговор."""
    query = update.callback_query
    query.answer()
    type = query.data
    context.user_data['type'] = type
    logging.info(f"Пользователь выбрал тип: {type}")
    reply_markup = InlineKeyboardMarkup(keyboard_film_genre)
    query.message.reply_text(
        'Отлично, теперь выбери жанр:',
        reply_markup=reply_markup
    )
    return SECOND


def choose_year(update, context):
    """Пользователь выбирает год и продолжает разговор."""
    query = update.callback_query
    query.answer()
    genre = query.data
    if genre == 'skip_genre':
        context.user_data['genre'] = None
    else:
        context.user_data['genre'] = genre
    logging.info(f"Пользователь выбрал жанр: {genre}")
    query.message.reply_text(
        'Теперь введи год выпуска(например: 2020 или 2020-2024):'
    )
    return THIRD


def choose_rating(update, context):
    """Пользователь выбирает рейтинг и продолжает разговор."""
    year = update.message.text
    logging.info(f"Пользователь ввел год: {year}")
    year_start_pattern = r"^(19[0-9]{2}|20[0-2][0-9])$"
    year_range_pattern = r"^(19[0-9]{2}|20[0-2][0-9])" + \
                         r"-(19[0-9]{2}|20[0-2][0-9])"
    pattern = "|".join([year_start_pattern, year_range_pattern])
    current_year = datetime.datetime.now().year

    if not re.match(pattern, year):
        update.message.reply_text(
            'Неверный формат года, введи год или диапазон годов через дефис'
            '(например: 2020 или 2020-2021).'
        )
        return THIRD

    if '-' in year:
        start_year, end_year = map(int, year.split('-'))
        if start_year > end_year:
            update.message.reply_text(
                'Год начала диапазона должен быть не больше года окончания!'
            )
            return THIRD
        if start_year > current_year or end_year > current_year:
            update.message.reply_text(
                'Год или диапазон годов не может быть позже текущего года!'
            )
            return THIRD
        context.user_data['year'] = year
    else:
        if int(year) > current_year:
            update.message.reply_text(
                'Введенный год не может быть позже текущего!'
            )
            return THIRD
        context.user_data['year'] = year

    update.message.reply_text(
        'Давай выберем рейтинг, введи диапазон чисел через дефис'
        '(например: 7-10).'
    )
    return FOURTH


def get_filtered_film(update, context):
    """Получает отфильтрованный фильм по рейтингу."""
    rating_text = update.message.text
    logging.info(f"Пользователь ввел рейтинг: {rating_text}")
    match = re.fullmatch(r'([1-9]|10)-([1-9]|10)', rating_text)

    if match is None:
        update.message.reply_text(
            'Пожалуйста, введи диапазон чисел, '
            'разделенных дефисом (например: 7-10).'
        )
        return FOURTH

    ratings = [float(rating) for rating in rating_text.split('-')]
    if len(ratings) == 2 and ratings[0] > ratings[1]:
        update.message.reply_text(
            'Нижняя граница диапазона не может быть больше верхней. '
            'Пожалуйста, введи корректный диапазон.'
        )
        return FOURTH

    try:
        context.user_data['rating'] = rating_text
        get_random_film(update=update,
                        context=context,
                        genre=context.user_data["genre"],
                        type=context.user_data["type"],
                        year=context.user_data['year'],
                        rating=context.user_data['rating'])
        reply_markup = ReplyKeyboardMarkup(
            keyboard_menu, resize_keyboard=True
        )
        update.message.reply_text(
            'Если не понравился, всегда можешь повторить свой запрос 😊',
            reply_markup=reply_markup
        )
        return ConversationHandler.END
    except ValueError:
        update.message.reply_text(
            'Пожалуйста, введи диапазон чисел, '
            'разделенных дефисом (например: 7-10).'
        )
        return FOURTH


def another_film(update, context):
    """Находит еще один фильм с таким же запросом."""
    try:
        get_random_film(update=update,
                        context=context,
                        genre=context.user_data["genre"],
                        type=context.user_data["type"],
                        year=context.user_data['year'],
                        rating=context.user_data['rating'])
        reply_markup = ReplyKeyboardMarkup(keyboard_menu, resize_keyboard=True)
        update.message.reply_text(
            'Если не понравился, всегда можешь повторить свой запрос 😊',
            reply_markup=reply_markup
        )
    except Exception as e:
        logging.error(f"Ошибка при поиске еще одного фильма: {e}")
        update.message.reply_text(
            'Возникла ошибка при поиске еще одного фильма. Попробуйте позже.'
        )


def cancel(update, context):
    """Завершает разговор и возвращает пользователя в главное меню."""
    user = update.message.from_user
    logging.info(f'Пользователь {user.first_name} отменил разговор.')
    update.message.reply_text(
        'Ты вернулся в главное меню', reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def main():
    """Основная логика работы бота."""
    updater = Updater(token=TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', help)
    random_film_handler = CommandHandler('randomfilm', get_random_film)
    main_menu_handler = RegexHandler('^Главное меню$', cancel)
    another_film_handler = RegexHandler('^Еще один$', another_film)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('findfilm', start_conversation),
                      RegexHandler('^Начать заново$', start_conversation)],
        states={
            FIRST: [
                CallbackQueryHandler(choose_genre, pass_user_data=True),
            ],
            SECOND: [
                CallbackQueryHandler(choose_year, pass_user_data=True)
            ],
            THIRD: [
                MessageHandler(Filters.text & ~Filters.command,
                               choose_rating, pass_user_data=True)
            ],
            FOURTH: [
                MessageHandler(Filters.text & ~Filters.command,
                               get_filtered_film, pass_user_data=True)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(random_film_handler)
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(main_menu_handler)
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
