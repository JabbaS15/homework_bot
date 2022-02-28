import logging
import os
import sys
import time
from http import HTTPStatus
from logging.handlers import RotatingFileHandler

import telegram
import requests

from dotenv import load_dotenv
from telegram import TelegramError
from json.decoder import JSONDecodeError


class HttpStatusCodeError(Exception):
    """Исключение вызывающие при status code != 200."""

    pass


class EndpointIsUnavailable(Exception):
    """Исключение вызывающие когда ENDPOINT недоступен."""

    pass


class FailedToSendMessages(Exception):
    """Исключение вызывающие когда сообщение не было отправлено."""

    pass


load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
RETRY_TIME = 60
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.INFO,
    filename='main.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler('main.log',
                              maxBytes=50_000_000, backupCount=5)
logger.addHandler(handler)


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        logger.info('Сообщение отправлено')
        return bot.send_message(TELEGRAM_CHAT_ID, message)
    except TelegramError as error:
        error_message = f'Сбой при отправке сообщения: {error}'
        logging.error(error_message)
        raise FailedToSendMessages(error_message) from error


def get_api_answer(current_timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            error_message = 'API недоступен: status code is not 200'
            logging.error(error_message)
            raise HttpStatusCodeError(error_message)
        return response.json()
    except JSONDecodeError:
        logging.error('Ошибка конвертации JSON:')
        raise JSONDecodeError
    except requests.exceptions.RequestException:
        logging.error('Endpoint is unavailable')
        raise EndpointIsUnavailable('Endpoint is unavailable')


def check_response(response):
    """Проверяет ответ API на корректность."""
    if not isinstance(response, dict):
        logger.error('Переменная "response" не является словарем')
        raise TypeError('Переменная "response" не является словарем')
    if 'homeworks' not in response:
        logger.error('В словаре не найден ключ homeworks')
        raise KeyError('В словаре не найден ключ homeworks')
    homework = response.get('homeworks')
    if not isinstance(homework, list):
        logger.error('Переменная "response" не является списком')
        raise TypeError('Переменная "response" не является списком')
    return homework


def parse_status(homework):
    """Извлекает из информации статус домашней работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_STATUSES:
        raise KeyError(f'Ошибка ключа {homework_status}')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка доступности переменных окружения."""
    tokens_env = {'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
                  'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
                  'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
                  }
    tokens = []
    for name in tokens_env:
        token = tokens_env[name]
        if not token:
            tokens.append(token)
            error_message = (f'Отсутствие обязательных переменных окружения:'
                             f' {token}')
            logging.critical(error_message)
        if not tokens:
            return True
        return False


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit(1)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    error_book = []
    status = []
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if not homework:
                error_message = 'list_homework_empty'
                logging.error(error_message)
                if error_message not in status:
                    send_message(bot,
                                 'Работа ожидает поступления на проверку ')
                    status.append(error_message)
            else:
                message = parse_status(homework[0])
                send_message(bot, message)
                status.clear()
        except Exception as error:
            error_message = f'Сбой в работе программы: {error}'
            logging.error(error_message)
            if error_message not in error_book:
                send_message(bot, error_message)
                error_book.append(error_message)
        time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
