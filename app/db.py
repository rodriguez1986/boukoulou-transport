import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
URL=os.getenv("DATABASE_URL","sqlite:///./boukoulou.db")
kwargs={"check_same_thread":False} if URL.startswith("sqlite") else {}
engine=create_engine(URL,pool_pre_ping=True,connect_args=kwargs)
SessionLocal=sessionmaker(bind=engine,autoflush=False,autocommit=False,expire_on_commit=False)
class Base(DeclarativeBase): pass
def get_db():
    s=SessionLocal()
    try: yield s
    finally: s.close()
