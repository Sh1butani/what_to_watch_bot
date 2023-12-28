import logging
import requests
import os
import sys

from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup
from telegram.ext import (
    Filters, CommandHandler, Updater, MessageHandler
)


load_dotenv("tokens.env")

KINOPOISK_TOKEN = os.getenv('KINOPOISK_TOKEN')
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

HEADERS = {'X-API-KEY': f'{KINOPOISK_TOKEN}'}
URL = 'https://api.kinopoisk.dev/v1.4/movie/random?type='


def get_new_film():
    """Выводит id рандомного фильма."""
    response = requests.get(URL, headers=HEADERS).json()
    random_film = response.get('names')
    return random_film


def start(update, context):
    """Выводит сообщение при команде /start."""
    name = update.message.chat.first_name
    chat = update.effective_chat
    context.bot.send_message(
        chat_id=chat.id,
        text='Спасибо, что вы включили меня, {}!'.format(name),
        )


def new_film(update, context):
    chat = update.effective_chat
    buttons = ReplyKeyboardMarkup(
        [['Найти фильм'], ['Возможности бота']],
        resize_keyboard=True)
    context.bot.send_message(
        chat_id=chat.id,
        text='Привет, посмотри, какой фильм я тебе нашёл',
        reply_markup=buttons
        )
    context.bot.send_message(chat.id, get_new_film())




def echo(update, context):
    """Отвечает на любое текстовое сообщение пользователя."""
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Привет, я Bot!'
        )


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s ['
        '%(filename)s:%(lineno)d - %(funcName)s]',
        level=logging.DEBUG,
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    updater = Updater(token=TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    film_handler = CommandHandler('newfilm', new_film)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(echo_handler)
    dispatcher.add_handler(film_handler)

    updater.start_polling()
    updater.idle()
