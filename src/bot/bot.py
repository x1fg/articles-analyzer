import asyncio
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message
from datetime import datetime, timedelta
from sqlalchemy import func
from src.database.models import SessionLocal, Article
from src.config.settings import TELEGRAM_API_KEY

bot = Bot(token=TELEGRAM_API_KEY)
dp = Dispatcher()
router = Router()

dp.include_router(router)

async def start_bot():
    """Функция запуска Telegram-бота."""
    print("Бот запущен...")
    await dp.start_polling(bot)

def get_article_count_by_period(days=None):
    """Получить количество статей за указанный период."""
    session = SessionLocal()
    query = session.query(func.count(Article.id))
    if days:
        since_date = datetime.now() - timedelta(days=days)
        query = query.filter(Article.published_date >= since_date)
    count = query.scalar()
    session.close()
    return count

def get_articles_by_period(days=None):
    """Получить список статей за указанный период."""
    session = SessionLocal()
    query = session.query(Article)
    if days:
        since_date = datetime.now() - timedelta(days=days)
        query = query.filter(Article.published_date >= since_date)
    articles = query.order_by(Article.published_date.desc()).all()
    session.close()
    return articles

def search_article_by_title(title):
    """Поиск статьи по названию."""
    session = SessionLocal()
    article = session.query(Article).filter(Article.title.ilike(f"%{title}%")).first()
    session.close()
    return article

@router.message(Command("start"))
async def start_command(message: Message):
    """Обработчик команды /start."""
    await message.answer(
        "Привет! Я бот для работы с научными статьями. Вот что я могу:\n"
        "/stats — статистика статей\n"
        "/list — список статей за месяц\n"
        "/search <название> — поиск статьи\n"
        "\nПопробуйте, например, `/stats` или `/search machine learning`"
    )

@router.message(Command("stats"))
async def stats_command(message: Message):
    """Обработчик команды /stats."""
    today_count = get_article_count_by_period(days=1)
    week_count = get_article_count_by_period(days=7)
    month_count = get_article_count_by_period(days=30)
    year_count = get_article_count_by_period(days=365)

    await message.answer(
        f"📊 Статистика статей:\n"
        f"Сегодня: {today_count}\n"
        f"За неделю: {week_count}\n"
        f"За месяц: {month_count}\n"
        f"За год: {year_count}"
    )

@router.message(Command("list"))
async def list_command(message: Message):
    """Обработчик команды /list."""
    query = message.text[len("/list "):].strip()
    if not query:
        await message.answer(
            "❌ Укажите ключевое слово для фильтрации статей.\n"
            "Например: `/list LLM`",
            parse_mode="Markdown"
        )
        return

    session = SessionLocal()
    since_date = datetime.now() - timedelta(days=30)
    articles = session.query(Article).filter(
        Article.published_date >= since_date,
        Article.title.ilike(f"%{query}%")
    ).order_by(Article.published_date.desc()).all()
    session.close()

    if not articles:
        await message.answer(f"❌ Нет статей, содержащих ключевое слово '{query}' за последний месяц.")
        return

    response = f"📋 Список статей за последний месяц по ключевому слову '{query}':\n"
    for article in articles[:10]:
        summary_link = f"[Краткое содержание]({article.summary_path})" if article.summary_path else "Суммаризация отсутствует"
        response += (
            f"- {article.title} (Дата: {article.published_date.date()})\n"
            f"  🔗 [Оригинал статьи]({article.pdf_url}) | {summary_link}\n"
        )

    await message.answer(response, parse_mode="Markdown")

@router.message(Command("search"))
async def search_command(message: Message):
    """Обработчик команды /search."""
    query = message.text[len("/search "):].strip()
    if not query:
        await message.answer("🔍 Укажите название статьи после команды.")
        return

    article = search_article_by_title(query)
    if not article:
        await message.answer(f"Статья с названием '{query}' не найдена.")
        return

    response = (
        f"📄 Найдена статья:\n"
        f"Название: {article.title}\n"
        f"Дата публикации: {article.published_date.date()}\n"
        f"🔗 [Скачать PDF]({article.file_path})\n"
        f"🔗 [Оригинал статьи]({article.pdf_url})\n"
        f"\nСуммаризация: {article.summary if article.summary else 'Отсутствует'}"
    )
    await message.answer(response, parse_mode="Markdown")

async def main():
    """Основная функция запуска Telegram-бота."""
    print("Бот запущен...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
