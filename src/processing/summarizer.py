import os
from src.api_caller import APICaller
from src.database.models import SessionLocal, Article
from src.config.settings import OPENAI_GPT_API_KEY

class Summarizer:
    def __init__(self, summary_folder='data/summaries'):
        """
        Инициализация класса Summarizer.
        """
        self.api_caller = APICaller(api_key=OPENAI_GPT_API_KEY)
        self.summary_folder = summary_folder
        if not os.path.exists(self.summary_folder):
            os.makedirs(self.summary_folder)

    def summarize_article(self, article):
        """
        Генерация суммаризации для переданной статьи.
        """
        system_prompt = "Ты помощник для суммаризации научных статей."
        user_prompt = f"Суммаризируй следующую статью: {article.title}"
        try:
            print(f"🔍 Генерация суммаризации для статьи: {article.title}")
            summary = self.api_caller.call_gpt35_turbo(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=300,
                temperature=0.7
            )
            return summary
        except Exception as e:
            print(f"❌ Ошибка суммаризации для статьи '{article.title}': {e}")
            return None

    def save_summary_to_file(self, article, summary):
        """
        Сохраняет суммаризацию статьи в текстовый файл.
        """
        safe_title = "".join(c if c.isalnum() else "_" for c in article.title[:50])
        filename = f"{safe_title}_{article.id}.txt"
        file_path = os.path.join(self.summary_folder, filename)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(summary)
            print(f"✅ Суммаризация сохранена: {file_path}")
            return file_path
        except Exception as e:
            print(f"❌ Ошибка сохранения суммаризации для статьи '{article.title}': {e}")
            return None

    def process_all(self):
        """
        Генерация и сохранение суммаризаций для всех статей без суммаризации.
        """
        session = SessionLocal()
        articles = session.query(Article).filter(Article.summary == None).all()
        print(f"⏳ Найдено статей для обработки: {len(articles)}")
        for article in articles:
            summary = self.summarize_article(article)
            if summary:
                summary_path = self.save_summary_to_file(article, summary)
                if summary_path:
                    article.summary = summary
                    article.summary_path = summary_path
                    session.commit()
                    print(f"✅ Суммаризация завершена для статьи: {article.title}")
        session.close()