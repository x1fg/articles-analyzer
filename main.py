import argparse
import asyncio
from src.bot.bot import start_bot
from src.api.arxiv_client import ArxivParser
from src.database.models import init_db
from src.config.settings import ARXIV_QUERIES
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def run_parser():
    """Функция запуска парсинга статей."""
    print("Инициализация базы данных...")
    init_db()
    print("База данных готова!")

    print("Запуск парсинга статей...")
    parser = ArxivParser(queries=ARXIV_QUERIES)
    parser.run()
    print("Парсинг завершен!")


def run_bot():
    """Функция запуска Telegram-бота."""
    print("Запуск Telegram-бота...")
    asyncio.run(start_bot())  # Используем asyncio.run для запуска асинхронной функции


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Управление проектом")
    parser.add_argument(
        "action",
        choices=["bot", "parser"],
        help="Укажите, что запустить: bot (Telegram-бот) или parser (парсер статей)",
        nargs="?",  # Делает аргумент необязательным
        default="bot",  # Значение по умолчанию
    )
    args = parser.parse_args()

    if args.action == "bot":
        run_bot()
    elif args.action == "parser":
        run_parser()