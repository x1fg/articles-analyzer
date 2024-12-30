from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.config.settings import DATABASE_URL

Base = declarative_base()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Article(Base):
    __tablename__ = 'articles'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    published_date = Column(DateTime, nullable=False)
    pdf_url = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    summary = Column(Text, nullable=True)

def init_db():
    Base.metadata.create_all(bind=engine)