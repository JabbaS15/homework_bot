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


load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TOKENS = {'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
          'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
          'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
          }
RETRY_TIME = 1200
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
        message = f'Сбой при отправке сообщения: {error}'
        logging.error(message)
        raise TelegramError(message)


def get_api_answer(current_timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            message = 'API недоступен: status code is not 200'
            logging.error(message)
            raise HttpStatusCodeError(message)
        return response.json()
    except JSONDecodeError:
        message = 'Ошибка конвертации JSON:'
        logging.error(message)
        raise JSONDecodeError
    except requests.exceptions.RequestException:
        logging.error('Endpoint is unavailable')
        raise Exception('Endpoint is unavailable')


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
    else:
        verdict = HOMEWORK_STATUSES[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка доступности переменных окружения."""
    for name in TOKENS:
        token = globals()[name]
        # при испотльзовании TOKENS[name], автоматические тесты не проходят
        if not token:
            message = 'Отсутствие обязательных переменных окружения:'
            logging.error(message)
            return False
    return True


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit(1)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if not homework:
                message = 'Список homework пуст'
                logging.error(message)
            else:
                message = parse_status(homework[0])
                send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
        else:
            pass
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
