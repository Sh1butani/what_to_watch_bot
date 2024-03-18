# Что посмотреть?
Это бот для поиска фильмов/сериалов/мультфильмов/аниме. Работает на основе API Кинопоиска.
Поддерживаются следующие команды:

- `/start`, `/help` выводят справочную информацию
- `/randomfilm` отправляет пользователю абсолютно рандомный фильм
- `/findfilm` эта команда позволяет вам найти фильм по заданным критериям

Бот доступен в телеграмме [What_towatch_bot](https://t.me/What_towatch_bot)

### Возможнсти:
1. Поиск фильма:
Бот позволяет пользователям найти фильмы по различным критериям, таким как жанр, год выпуска и рейтинг. Пользователи могут указать свои предпочтения, а бот предоставит информацию о случайно выбранном фильме, соответствующем их запросу.

2. Просмотр информации о фильмах:
Пользователи могут получить подробную информацию о фильмах, включая рейтинги на Кинопоиске и IMDb и ссылки на них, жанр, продолжительность, год выпуска и описание.

3. Поиск по рейтингу:
Бот позволяет пользователям найти фильмы в заданном диапазоне рейтинга, чтобы найти фильмы с высокими оценками или отфильтровать фильмы с низкими оценками.

4. Поиск по жанру:
Пользователи могут искать фильмы определенного жанра, чтобы найти фильмы, соответствующие их интересам или настроению.

### Технологии:

**Языки программирования, библиотеки и модули:**

[![Python](https://img.shields.io/badge/Python-3.9.10%20-blue?logo=python)](https://www.python.org/)
![python-telegram-bot](https://img.shields.io/badge/python--telegram--bot-13.7-blue)

### Как локально запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone git@github.com:Sh1butani/what_to_watch_bot.git
```

```
cd what_to_watch_bot
```

Cоздать и активировать виртуальное окружение:

```
python -m venv venv
```

```
source venv/Scripts/activate
```

Установить зависимости из файла requirements.txt:

```
python -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Создать и добавить в файл .env:
```python
KINOPOISK_TOKEN='Токен кинопоиска'
TG_TOKEN='Токен телеграм-бота'
TELEGRAM_CHAT_ID='@Id чата'
```

### Доработка:
Планирую добавить еще несколько фильтров, написать тесты, скорректировать в некоторых местах клавиаутры, настроить  GitHub Actions.


### Автор:
[David Pilosyan](https://t.me/Shibutani)