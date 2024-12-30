import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from src.database.models import Article, SessionLocal

class ArxivParser:
    def __init__(self, queries, max_results=50, timeout=10):
        """
        Инициализация парсера arXiv.
        """
        self.queries = queries
        self.max_results = max_results
        self.timeout = timeout
        self.base_url = 'http://export.arxiv.org/api/query'
        self.one_month_ago = datetime.now() - timedelta(days=30)

    def fetch_articles(self, query):
        """
        Загружает статьи по запросу с arXiv API.
        """
        params = {
            'search_query': query,
            'start': 0,
            'max_results': self.max_results,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        try:
            response = requests.get(self.base_url, params=params, timeout=self.timeout)
            if response.status_code != 200:
                print(f"Ошибка API: {response.status_code}")
                return []
        except requests.exceptions.RequestException as e:
            print(f"Ошибка подключения: {e}")
            return []

        root = ET.fromstring(response.content)
        articles = []
        for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
            title = entry.find('{http://www.w3.org/2005/Atom}title').text
            published = entry.find('{http://www.w3.org/2005/Atom}published').text
            link = entry.find('{http://www.w3.org/2005/Atom}link[@type="application/pdf"]')
            pdf_url = link.attrib['href'] if link is not None else None
            articles.append({
                'title': title.strip(),
                'published_date': published,
                'pdf_url': pdf_url
            })
        return articles

    def filter_recent_articles(self, articles):
        """
        Фильтрует статьи, опубликованные за последний месяц.
        """
        return [
            article for article in articles
            if datetime.strptime(article['published_date'], '%Y-%m-%dT%H:%M:%SZ') >= self.one_month_ago
        ]

    def save_articles_to_db(self, articles):
        """
        Сохраняет статьи в базу данных.
        """
        session = SessionLocal()
        try:
            for article in articles:
                if not session.query(Article).filter(Article.pdf_url == article['pdf_url']).first():
                    new_article = Article(
                        title=article['title'],
                        published_date=datetime.strptime(article['published_date'], '%Y-%m-%dT%H:%M:%SZ'),
                        pdf_url=article['pdf_url']
                    )
                    session.add(new_article)
                    print(f"Статья добавлена в базу: {article['title']}")
            session.commit()
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
        finally:
            session.close()

    def run(self):
        """
        Основной метод для выполнения парсинга.
        """
        for query in self.queries:
            print(f"\n🔍 Поиск статей по запросу: {query}")
            articles = self.fetch_articles(query)
            recent_articles = self.filter_recent_articles(articles)
            self.save_articles_to_db(recent_articles)