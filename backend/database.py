"""
Database models para Supabase PostgreSQL
"""
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ARRAY, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import JSONB
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("DATABASE_URL no configurado en .env")

engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Generator para FastAPI dependencies"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =====================================================
# MODELOS
# =====================================================

class HPEProduct(Base):
    """Catálogo de productos HPE"""
    __tablename__ = "hpe_products"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String(50), unique=True, nullable=False)
    nombre = Column(String(200), nullable=False)
    categoria = Column(String(100))
    descripcion = Column(Text)
    trigger_keywords = Column(ARRAY(String))
    casos_uso = Column(ARRAY(String))
    ventaja_vs_competencia = Column(JSONB)
    speech_hook = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class CompanyAnalysis(Base):
    """Historial de análisis"""
    __tablename__ = "company_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(200), nullable=False)
    industry = Column(String(100))
    fit_score = Column(Integer, CheckConstraint('fit_score >= 0 AND fit_score <= 100'))
    tech_stack = Column(JSONB)
    triggers = Column(JSONB)
    competitors_detected = Column(JSONB)
    hpe_solution_recommended = Column(String(200))
    speech_generated = Column(Text)
    target_role = Column(String(50))
    sources = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)


# =====================================================
# HELPERS
# =====================================================

def init_db():
    """Crear tablas"""
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas")


if __name__ == "__main__":
    print("🔌 Conectando a Supabase PostgreSQL...")
    try:
        init_db()
        print("✅ Conexión exitosa")
    except Exception as e:
        print(f"❌ Error: {e}")
