import argparse
import asyncio
import sys
import os

# Добавление корня проекта в PYTHONPATH
#sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.bot.bot import start_bot
from src.api.arxiv_client import ArxivParser
from src.processing.summarizer import Summarizer
from src.database.models import init_db
from src.config.settings import ARXIV_QUERIES

def run_parser():
    """Функция запуска парсинга статей."""
    print("Инициализация базы данных...")
    init_db()
    print("База данных готова!")

    print("Запуск парсинга статей...")
    parser = ArxivParser(queries=ARXIV_QUERIES)
    parser.run()
    print("Парсинг завершен!")

def run_summarizer():
    """Функция запуска суммаризации статей."""
    print("Инициализация базы данных...")
    init_db()
    print("База данных готова!")

    print("Запуск генерации суммаризаций...")
    summarizer = Summarizer(summary_folder="summaries", )
    summarizer.process_all()
    print("Суммаризации успешно созданы!")

def run_bot():
    """Функция запуска Telegram-бота."""
    print("Запуск Telegram-бота...")
    asyncio.run(start_bot())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Управление проектом")
    parser.add_argument(
        "action",
        choices=["bot", "parser", "summarizer"],
        help="Укажите, что запустить: bot (Telegram-бот), parser (парсер статей) или summarizer (генерация суммаризаций)",
        nargs="?",
        default="bot",
    )
    args = parser.parse_args()

    if args.action == "bot":
        run_bot()
    elif args.action == "parser":
        run_parser()
    elif args.action == "summarizer":
        run_summarizer()