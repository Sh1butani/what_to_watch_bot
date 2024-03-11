class HTTPRequestError(Exception):
    """Класс исключений для обработки ошибок http запросов."""

    def __init__(self, response):
        """Исключение при ошибке доступа к эндпоинту."""
        super().__init__(
            f'Эндпоинт {response.url} недоступен.'
            f'Код ответа API: {response.status_code} - {response.reason}'
        )
