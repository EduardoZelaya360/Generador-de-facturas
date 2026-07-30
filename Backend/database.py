import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Subimos dos niveles para llegar a la raíz del proyecto donde está el .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, ".env"))

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_DSN = os.getenv("DB_DSN")

if not DB_USER or not DB_PASSWORD or not DB_DSN:
    raise ValueError("Faltan credenciales en el archivo .env")

# URL base para oracle+oracledb manejando conexiones seguras (tcps)
SQLALCHEMY_DATABASE_URL = f"oracle+oracledb://{DB_USER}:{DB_PASSWORD}@"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"dsn": DB_DSN},
    echo=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()