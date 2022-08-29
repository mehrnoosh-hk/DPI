from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, Session
from sqlalchemy import types

URI = "postgresql://postgres:Fx9TZJtmPowv9ZVX@services.irn1.chabokan.net:38266/peggy"
Base = declarative_base()
engine = create_engine(URI)


def get_db():
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()

class MyFile(types.TypeDecorator):
    impl = types.String

    def get_col_spec(self, **kw):
        return "MyFile"

    def process_bind_param(self, value, dialect) -> None:
        return "PREFIX:" + value

    def process_result_value(self, value, dialect) -> None:
        return value[7:]
