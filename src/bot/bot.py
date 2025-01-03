import asyncio
import re
import torch
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message
from datetime import datetime, timedelta
from sqlalchemy import func
from sentence_transformers import SentenceTransformer, util
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from src.database.models import SessionLocal, Article
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
        "/list <ключевое слово> — список статей за месяц по ключевому слову\n"
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

def escape_markdown(text):
    """Экранирует специальные символы для Markdown."""
    return re.sub(r"([_\*\[\]\(\)~`>#+\-=|{}\.!])", r"\\\1", text)

model = SentenceTransformer('all-MiniLM-L6-v2')

@router.message(Command("list"))
async def list_command(message: Message):
    """Команда /list с проверкой ссылок."""
    session: Session = SessionLocal()
    try:
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.answer("❌ Укажите ключевое слово для поиска, например:\n`/list machine learning`", parse_mode="Markdown")
            return

        keyword = args[1].strip()
        if not keyword:
            await message.answer("❌ Ключевое слово не может быть пустым.")
            return

        articles = (
            session.query(Article)
            .filter(Article.published_date >= datetime.now() - timedelta(days=30))
            .limit(50)
            .all()
        )

        if not articles:
            await message.answer("❌ Нет доступных статей.")
            return

        article_titles = [article.title for article in articles]
        query_embedding = model.encode(keyword, convert_to_tensor=True)
        title_embeddings = model.encode(article_titles, convert_to_tensor=True)

        similarities = util.cos_sim(query_embedding, title_embeddings)
        sorted_indices = torch.argsort(similarities[0], descending=True).tolist()

        response = f"📋 Результаты поиска по запросу: `{escape_markdown(keyword)}`\n"
        found = False
        for idx in sorted_indices:
            article = articles[idx]
            similarity = similarities[0, idx].item()
            if similarity < 0.2: 
                continue

            found = True
            title = escape_markdown(article.title)
            original_url = article.pdf_url or "Оригинал недоступен"
            summary_command = escape_markdown(f"/summary_{article.id}")

            response += (
                f"- {title} (Дата: {article.published_date.date()})\n"
                f"  🔗 [{escape_markdown('Оригинал статьи')}]({original_url}) | "
                f"{summary_command}\n"
            )

        if not found:
            response = f"❌ Нет релевантных статей для запроса: `{escape_markdown(keyword)}`"

        for chunk in split_message(response):
            await message.answer(chunk, parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        await message.answer("❌ Произошла ошибка при выполнении команды.")
        print(f"Ошибка в обработчике /list: {e}")
    finally:
        session.close()

def split_message(text, max_length=4096):
    """Разделяет длинное сообщение на части для Telegram."""
    lines = text.splitlines()
    chunks = []
    current_chunk = ""

    for line in lines:
        if len(current_chunk) + len(line) + 1 > max_length:
            chunks.append(current_chunk)
            current_chunk = line + "\n"
        else:
            current_chunk += line + "\n"

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

@router.message(lambda message: message.text.startswith("/summary"))
async def show_summary(message: Message):
    """Обработка команды для показа краткого содержания."""
    session = SessionLocal()
    try:
        article_id = message.text[len("/summary"):].lstrip("_")
        
        if not article_id.isdigit():
            await message.answer("❌ Некорректный формат команды.")
            return
        
        article_id = int(article_id)
        article = session.query(Article).filter(Article.id == article_id).first()

        if not article:
            await message.answer("❌ Статья не найдена.")
        elif not article.summary:
            await message.answer("❌ Краткое содержание отсутствует.")
        else:
            await message.answer(f"📄 Краткое содержание статьи:\n{article.summary}")
    except Exception as e:
        await message.answer("❌ Произошла ошибка.")
        print(f"Ошибка в обработчике команды /summary: {e}")
    finally:
        session.close()

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
