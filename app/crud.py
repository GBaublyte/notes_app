from sqlalchemy.orm import Session
from app import schemas
from passlib.context import CryptContext

from app.database import User
from app.schemas import UserInDB

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# Functionality for Category
def create_category(db: Session, category: schemas.CategoryCreate, user_id: int):
    db_category = schemas.Category(**category.model_dump(), owner_id=user_id)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def get_category(db: Session, category_id: int):
    return db.query(schemas.Category).filter(schemas.Category.id == category_id).first()


def update_category(db: Session, category_id: int, category: schemas.CategoryCreate):
    db_category = get_category(db, category_id)
    for key, value in category.model_dump().items():
        setattr(db_category, key, value)
    db.commit()
    db.refresh(db_category)
    return db_category


def delete_category(db: Session, category_id: int):
    db_category = get_category(db, category_id)
    db.delete(db_category)
    db.commit()


# Functionality for Notes
def create_note(db: Session, note: schemas.NoteCreate, user_id: int):
    db_note = schemas.Note(**note.model_dump(), owner_id=user_id)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note


def get_note_by_id(db: Session, note_id: int):
    return db.query(schemas.Note).filter(schemas.Note.id == note_id).first()


def update_note(db: Session, note_id: int, note: schemas.NoteUpdate):
    db_note = get_note_by_id(db, note_id)
    for key, value in note.model_dump().items():
        setattr(db_note, key, value)
    db.commit()
    db.refresh(db_note)
    return db_note


def delete_note(db: Session, note_id: int):
    db_note = get_note_by_id(db, note_id)
    db.delete(db_note)
    db.commit()


def get_notes_by_title(db: Session, title: str, user_id: int):
    return db.query(schemas.Note).filter(schemas.Note.title.contains(title), schemas.Note.owner_id == user_id).all()


def get_notes_by_category(db: Session, category_id: int, user_id: int):
    return db.query(schemas.Note).filter(schemas.Note.category_id == category_id, schemas.Note.owner_id == user_id).all()