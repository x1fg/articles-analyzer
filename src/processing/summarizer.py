import os
from database.models import SessionLocal, Article
from openai import OpenAI
from src.config.settings import OPENAI_API_KEY

class Summarizer:
    def __init__(self, summary_folder='data/summaries'):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.summary_folder = summary_folder
        if not os.path.exists(self.summary_folder):
            os.makedirs(self.summary_folder)

    def summarize_article(self, article):
        prompt = f"Суммаризируй научную статью:\n\n{article.title}"
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Ты помощник для суммаризации статей."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            summary = response.choices[0].message.content.strip()
            return summary
        except Exception as e:
            print(f"Ошибка суммаризации: {e}")
            return None

    def process_all(self):
        session = SessionLocal()
        articles = session.query(Article).filter(Article.summary == None).all()
        for article in articles:
            print(f"Суммаризация статьи: {article.title}")
            summary = self.summarize_article(article)
            if summary:
                article.summary = summary
                session.commit()
                print(f"Суммаризация сохранена: {article.title}")
        session.close()