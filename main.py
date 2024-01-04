import logging
import requests
import os
import sys
import html

from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup
from telegram.ext import (
    Filters, CommandHandler, Updater, MessageHandler
)


load_dotenv("tokens.env")

KINOPOISK_TOKEN = os.getenv('KINOPOISK_TOKEN')
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

HELP_COMMAND = """
<b>/help</b> - <em>список команд</em>
<b>/start</b> - <em>запуск бота</em>
<b>/newfilm</b> - <em>найти новый фильм</em>"""

CONTENT_TYPES = {
    'animated-series': 'мультсериал',
    'anime': 'аниме',
    'cartoon': 'мультфильм',
    'movie': 'фильм',
    'tv-series': 'сериал'
}

HEADERS = {'X-API-KEY': f'{KINOPOISK_TOKEN}'}
URL = 'https://api.kinopoisk.dev/v1.4/movie/random?notNullFields=name&notNullFields=description&notNullFields=type&notNullFields=year&notNullFields=movieLength'


def start(update, context):
    """Выводит сообщение при команде /start."""
    name = update.message.chat.first_name
    chat = update.effective_chat
    buttons = ReplyKeyboardMarkup(
        [['/newfilm'], ['/help']],
        resize_keyboard=True)
    context.bot.send_message(
        chat_id=chat.id,
        text='Спасибо, что включили меня, {}! '
        'Чтобы узнать, что я умею, воспользуйтесь кнопкой /help'.format(name),
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


def translate_film_type(type):
    """Переводит английское значение типа на русское."""
    return CONTENT_TYPES.get(type, type)


def generate_film_info(film_data):
    """Генерирует информацию о фильме от API кинопоиска."""
    genre_names = [genre.get("name") for genre in film_data.get("genres", [])]
    film_info = (
        f'<b>{film_data.get("name")}</b>\n'
        '\n'
        f'Кинопоиск: {film_data.get("rating", {}).get("kp")}\n'
        f'IMDB: {film_data.get("rating", {}).get("imdb")}\n'
        '\n'
        f'<i>Тип:</i> {translate_film_type(film_data.get("type"))}\n'
        f'<i>Жанр:</i> {", ".join(genre_names)}\n'
        f'<i>Продолжительность:</i> {film_data.get("movieLength")} мин\n'
        f'<i>Год:</i> {film_data.get("year")}\n'
        '\n'
        f'{film_data.get("description")}\n'
    )
    return film_info


def get_new_film(update, context):
    """Отправляет пользователю сообщение с данными о фильме."""
    chat = update.effective_chat
    context.bot.send_message(
        chat_id=chat.id,
        text='Посмотри, какой фильм я тебе нашёл',
        )
    film_data = requests.get(URL, headers=HEADERS).json()

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


def echo(update, context):
    """Отвечает на любое текстовое сообщение пользователя."""
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Воспользуйтесь кнопкой "Возможности бота" для детальной информации.'
        )


def main():
    """Основная логика работы бота."""
    updater = Updater(token=TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', help)
    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    new_film_handler = CommandHandler('newfilm', get_new_film)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(echo_handler)
    dispatcher.add_handler(new_film_handler)

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
