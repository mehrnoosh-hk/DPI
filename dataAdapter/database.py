from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, Session
from config import db_config

URI = "postgresql://postgres:Fx9TZJtmPowv9ZVX@services.irn1.chabokan.net:38266/peggy"
Base = declarative_base()
engine = create_engine(URI)


def get_db():
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()