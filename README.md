# Telegram bot на python.
[![Python](https://img.shields.io/badge/-Python_3.10-464646?style=flat&logo=Python&logoColor=ffffff&color=013220)](https://www.python.org/)

## Описание проекта:
Отслеживает отправленное домашнее задание на ревью.  

Имеет три статуса отслеживания:
- Работа взята на проверку ревьюером.
- Работа проверена: у ревьюера есть замечания.
- Работа проверена: ревьюеру всё понравилось. Ура!



## Инструкция по развёртыванию:
1. Загрузите проект:
```bash
git clone https://github.com/JabbaS15/homework_bot.git
```
2. Установите и активируйте виртуальное окружение:
```bash
python -m venv venv
source venv/Scripts/activate
python3 -m pip install --upgrade pip
```
3. Установите зависимости:
```bash
pip install -r requirements.txt
```
4. Создать файл настроек окружения .env и заполнить его:
```bash
touch .env
```
```bash
PRACTICUM_TOKEN = 'PRACTICUM_TOKEN'
TELEGRAM_TOKEN = 'TELEGRAM_TOKEN'
TELEGRAM_CHAT_ID = 'TELEGRAM_CHAT_ID'
```
5. В папке с файлом homework.py выполните команду запуска:
```bash
python homework.py
```

### Автор проекта:
[Шведков Роман](https://github.com/JabbaS15)
