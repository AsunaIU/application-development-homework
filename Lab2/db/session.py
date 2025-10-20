from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.base import Base

DATABASE_URL = "postgresql+psycopg2://user:superpass@localhost:5432/my_db"

engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
