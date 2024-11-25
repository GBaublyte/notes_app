from sqlalchemy import Column, Integer, String, ForeignKey
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
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    # Relationship with notes
    notes = relationship("Note", back_populates="owner")

    # Relationship with categories
    categories = relationship("Category", back_populates="owner")


class Note(Base):
    __tablename__ = 'notes'
    id = Column(Integer, primary_key=True, index=True)
    note_name = Column(String, index=True)
    description = Column(String)
    owner_id = Column(Integer, ForeignKey('users.id'))
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True)  # Make category_id nullable
    image_url = Column(String, nullable=True)

    # Relationship with user
    owner = relationship("User", back_populates="notes")

    # Relationship with category
    category = relationship("Category", back_populates="notes", uselist=False)  # Single category per note


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey('users.id'))

    # Relationship with user
    owner = relationship("User", back_populates="categories")

    # Relationship with notes
    notes = relationship("Note", back_populates="category", cascade="all, delete-orphan")


# Drop all tables (warning: this will delete all your data)
# Base.metadata.drop_all(bind=engine)
# Create all tables
Base.metadata.create_all(bind=engine)