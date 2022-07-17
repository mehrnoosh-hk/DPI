from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, Session
from config import db_config


Base = declarative_base()
engine = create_engine(db_config['URI'])


def get_db():
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()