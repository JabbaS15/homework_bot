import logging
import os
import sys
import time
from logging.handlers import RotatingFileHandler

import telegram
import requests

from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TOKENS = ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']
RETRY_TIME = 600
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
                              maxBytes=50000000, backupCount=5)
logger.addHandler(handler)


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        logger.info('Сообщение отправлено')
        return bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        message = f'Сбой при отправке сообщения: {error}'
        logging.error(message)
        raise Exception(message)


def get_api_answer(current_timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != 200:
            message = 'API недоступен: status code is not 200'
            logging.error(message)
            raise Exception(message)
        return response.json()
    except Exception as error:
        message = f'Ошибка обращения к API: {error}'
        logging.error(message)
        raise Exception(message)


def check_response(response):
    """Проверяет ответ API на корректность."""
    if not isinstance(response, dict):
        logger.error('Переменная "response" не является словарем')
        raise TypeError('Переменная "response" не является словарем')
    if 'homeworks' not in response:
        logger.error('В словаре не найден ключ homeworks')
        raise KeyError('В словаре не найден ключ homeworks')
    try:
        homework = response.get('homeworks')
        if not isinstance(homework, list):
            logger.error('Переменная "response" не является списком')
            raise TypeError('Переменная "response" не является списком')
        return homework
    except Exception as error:
        message = f'Ошибка при проверки API на корректность: {error}'
        logging.error(message)
        raise Exception(message)


def parse_status(homework):
    """Извлекает из информации статус домашней работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка доступности переменных окружения."""
    tokens = []
    for name in TOKENS:
        token = globals()[name]
        if token is None or token == '':
            tokens.append(token)
            message = f'Отсутствие обязательных переменных окружения: {token}'
            logging.critical(message)
    if len(tokens) == 0:
        return True
    return False


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit(1)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 1642676085

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            message = parse_status(homework[0])
            send_message(bot, message)
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            send_message(bot, message)
            time.sleep(RETRY_TIME)
        else:
            print('Критический сбой')
            logging.exception('Критический сбой')
            break


if __name__ == '__main__':
    main()
