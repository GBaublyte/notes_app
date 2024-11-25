from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, relationship


DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    notes = relationship("Note", back_populates="owner")


class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    note_name = Column(String, index=True)
    description = Column(Text)
    # status = Column(String, index=True, default="pending")
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="notes")
    # created_at = Column(DateTime, default=datetime.now)
    image_url = Column(String)
    # category_id = Column(Integer, ForeignKey("categories.id"))
    # category = relationship("Category", back_populates="notes")


# class Category(Base):
#     __tablename__ = "categories"
#     id = Column(Integer, primary_key=True, index=True)
#     category_name = Column(String, index=True)
#     notes = relationship("Note", back_populates="category")


Base.metadata.create_all(bind=engine)


