import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///arxiv.db")
OPENAI_GPT_API_KEY = os.getenv("OPENAI_GPT_API_KEY")
TELEGRAM_API_KEY=os.getenv("TELEGRAM_API_KEY", "")
ARXIV_QUERIES = os.getenv("ARXIV_QUERIES", "LLM,Multi agent systems, MAS, GPT").split(',')