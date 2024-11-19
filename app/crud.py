from sqlalchemy.orm import Session
from app import models, schemas
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# Functionality for Category
def create_category(db: Session, category: schemas.CategoryCreate, user_id: int):
    db_category = models.Category(**category.model_dump(), owner_id=user_id)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def get_category(db: Session, category_id: int):
    return db.query(models.Category).filter(models.Category.id == category_id).first()


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
    db_note = models.Note(**note.model_dump(), owner_id=user_id)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note


def get_note_by_id(db: Session, note_id: int):
    return db.query(models.Note).filter(models.Note.id == note_id).first()


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
    return db.query(models.Note).filter(models.Note.title.contains(title), models.Note.owner_id == user_id).all()


def get_notes_by_category(db: Session, category_id: int, user_id: int):
    return db.query(models.Note).filter(models.Note.category_id == category_id, models.Note.owner_id == user_id).all()