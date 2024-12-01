import os
import shutil
from datetime import timedelta
from typing import Annotated, Optional

from fastapi import FastAPI, Depends, HTTPException, status, Form, Request, Query, Path, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.schemas import UserCreate, Token
from app.database import get_db, Note, User, Category  # Assume Category model is added
from app.auth import create_access_token, get_current_user, authenticate_user, ACCESS_TOKEN_EXPIRE_MINUTES, \
    get_password_hash
from werkzeug.utils import secure_filename

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static/"), name="static")
templates = Jinja2Templates(directory="app/templates")

UPLOAD_FOLDER = os.path.join("app", "static", "images")

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "base.html", {"request": request})


@app.get("/home", response_class=HTMLResponse)
async def get_home(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=307)

    # Fetch the current user's notes and categories
    try:
        notes = db.query(Note).filter(Note.owner_id == current_user.id).all()
        categories = db.query(Category).filter(Category.owner_id == current_user.id).all()
    except Exception as e:
        print(f"An error occurred while fetching notes: {e}")
        return templates.TemplateResponse(request, "error_page.html", {"request": request, "error": str(e)})

    # Pass the notes, categories, and user information to the template
    return templates.TemplateResponse(request, "base.html", {"request": request, "notes": notes, "user": current_user,
                                                    "categories": categories})


@app.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)  # changed to SQLAlchemy User model
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user  # returning the SQLAlchemy model instance directly


@app.get("/get-token", response_model=Token)
async def get_token(username: str = Query(...), password: str = Query(...), db: Session = Depends(get_db)):
    user = authenticate_user(db, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/token")
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(next(get_db()), form_data.username, form_data.password)  # Change here
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse(request, "login.html", {"request": request})


@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, username: str = Form(...), password: str = Form(...),
                     db: Session = Depends(get_db)):
    user = authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse(request, "login.html", {"request": request, "error": "Invalid credentials"})

    token = create_access_token(data={"sub": username})
    response = RedirectResponse("/notes", status_code=303)
    response.set_cookie(key="access_token", value=token, httponly=True)  # Store token in cookie
    return response


@app.post("/register", response_class=HTMLResponse)
async def register_post(request: Request, username: str = Form(...), password: str = Form(...),
                        db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        return templates.TemplateResponse(request, "login.html", {"request": request, "error": "Username already taken"})

    hashed_password = get_password_hash(password)
    new_user = User(username=username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(data={"sub": username})
    response = RedirectResponse("/notes", status_code=303)
    response.set_cookie(key="access_token", value=token, httponly=True)  # Store token in cookie
    return response


@app.get("/notes", response_class=HTMLResponse)
async def get_notes(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user is None:
        return RedirectResponse(url="/login")

    # Fetch the user's notes and categories
    notes = db.query(Note).filter(Note.owner_id == current_user.id).all()
    categories = db.query(Category).filter(Category.owner_id == current_user.id).all()

    # Pass the notes and categories to the template
    return templates.TemplateResponse(request, "base.html", {"request": request, "notes": notes, "categories": categories,
                                                    "user": current_user})


@app.get("/notes/get", response_class=HTMLResponse)
async def create_note_get(request: Request, db: Session = Depends(get_db),
                          current_user: User = Depends(get_current_user)):
    if current_user is None:
        return RedirectResponse(url="/login")

    # Fetch the user's categories
    categories = db.query(Category).filter(Category.owner_id == current_user.id).all()
    try:
        return templates.TemplateResponse(request, "base.html", {"request": request, "categories": categories})
    except Exception as e:
        print(f"Template rendering failed with error: {e}")
        return templates.TemplateResponse("error_page.html", {"request": request, "error": "Template not found"})


@app.post("/notes/post", response_class=HTMLResponse)
async def create_note_post(
        request: Request,
        note_name: str = Form(...),
        description: str = Form(...),
        image: Optional[UploadFile] = File(None),  # Allow the image field to be optional
        category_id: Optional[int] = Form(None),  # Make category_id optional
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    try:
        image_url = None
        if image is not None and image.filename != '':
            filename = secure_filename(image.filename)
            _, ext = os.path.splitext(filename)
            image_url = f"{filename}"
            image_path = os.path.join(UPLOAD_FOLDER, image_url)
            os.makedirs(os.path.dirname(image_path), exist_ok=True)  # Ensure the directory exists
            with open(os.path.join(UPLOAD_FOLDER, image_url), "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)

        new_note = Note(
            note_name=note_name,
            description=description,
            owner_id=current_user.id,
            image_url=image_url,  # Save the image path in the DB (can be None)
            category_id=category_id  # Assign category (can be None)
        )
        db.add(new_note)
        db.commit()
        db.refresh(new_note)

        # Fetch the updated list of notes for the user
        notes = db.query(Note).filter(Note.owner_id == current_user.id).all()
        categories = db.query(Category).filter(Category.owner_id == current_user.id).all()

        # Pass the notes, categories, and user information to the template
        return templates.TemplateResponse(request, "base.html", {"request": request, "notes": notes, "categories": categories,
                                                        "user": current_user,
                                                        "message": "Note created successfully"})
    except Exception as e:
        print(f"An error occurred: {e}")
        return templates.TemplateResponse(request, "error_page.html", {"request": request, "error": str(e)})


@app.get("/notes/edit/{note_id}", response_class=HTMLResponse)
async def edit_note_get(
        request: Request,
        note_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    note = db.query(Note).filter(Note.id == note_id, Note.owner_id == current_user.id).first()
    categories = db.query(Category).filter(Category.owner_id == current_user.id).all()
    if note is None:
        return templates.TemplateResponse(request, "error_page.html", {"request": request,
                                                              "error": "Note not found or not authorized to edit this note"})

    return templates.TemplateResponse(request, "edit_note.html", {"request": request, "note": note, "categories": categories})


@app.post("/notes/edit/{note_id}", response_class=HTMLResponse)
async def edit_note_post(
        request: Request,
        note_id: int,
        note_name: str = Form(...),
        description: str = Form(...),
        image: Optional[UploadFile] = File(None),  # Allow the image field to be optional
        category_id: Optional[str] = Form(None),  # Make category_id optional and accept it as a string
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    note = db.query(Note).filter(Note.id == note_id, Note.owner_id == current_user.id).first()
    if note is None:
        return templates.TemplateResponse(request, "error_page.html", {"request": request,
                                                              "error": "Note not found or not authorized to edit this note"})

    try:
        if image is not None and image.filename != '':
            filename = secure_filename(image.filename)
            _, ext = os.path.splitext(filename)
            image_url = f"{filename}"
            image_path = os.path.join(UPLOAD_FOLDER, image_url)
            os.makedirs(os.path.dirname(image_path), exist_ok=True)  # Ensure the directory exists
            with open(image_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
            note.image_url = image_url  # Update the image path in the DB

        # Convert category_id to int if not empty, otherwise set it to None
        if category_id:
            try:
                category_id = int(category_id)
            except ValueError:
                category_id = None
        else:
            category_id = None

        note.note_name = note_name
        note.description = description
        note.category_id = category_id  # Update category (can be None)

        db.commit()
        db.refresh(note)

        # Fetch the updated list of notes for the user
        notes = db.query(Note).filter(Note.owner_id == current_user.id).all()
        categories = db.query(Category).filter(Category.owner_id == current_user.id).all()

        # Pass the notes and categories to the template
        return templates.TemplateResponse(request, "base.html", {"request": request, "notes": notes, "categories": categories,
                                                        "user": current_user,
                                                        "message": "Note updated successfully"})
    except Exception as e:
        print(f"An error occurred: {e}")
        return templates.TemplateResponse(request, "error_page.html", {"request": request, "error": str(e)})


@app.post("/notes/delete/{note_id}", response_class=HTMLResponse)
async def delete_note(
        request: Request,
        note_id: int = Path(..., description="The ID of the note to delete"),
        method: str = Form(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # Check the method override
    if method.lower() == "delete":
        note = db.query(Note).filter(Note.id == note_id, Note.owner_id == current_user.id).first()

        if note is None:
            raise HTTPException(status_code=404, detail="Note not found or not authorized to delete this note")

        # Delete the note
        db.delete(note)
        db.commit()

    # Fetch the remaining notes
    notes = db.query(Note).filter(Note.owner_id == current_user.id).all()
    categories = db.query(Category).filter(Category.owner_id == current_user.id).all()
    # Pass the remaining notes, categories, and user information to the template
    return templates.TemplateResponse(request, "base.html", {"request": request, "notes": notes, "categories": categories,
                                                    "user": current_user,
                                                    "message": "Note deleted successfully"})

@app.get("/notes/category/{category_id}", response_class=HTMLResponse)
async def get_notes_by_category(
        request: Request,
        category_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    try:
        # Fetch notes by category for the current user
        notes = db.query(Note).filter(Note.owner_id == current_user.id, Note.category_id == category_id).all()
        categories = db.query(Category).filter(Category.owner_id == current_user.id).all()

        # Render the template with the filtered notes
        return templates.TemplateResponse(request, "base.html", {"request": request, "notes": notes, "categories": categories,
                                                        "user": current_user,
                                                        "message": "Notes filtered by category"})
    except Exception as e:
        print(f"An error occurred: {e}")
        return templates.TemplateResponse(request, "error_page.html", {"request": request, "error": str(e)})


@app.get("/categories", response_class=HTMLResponse)
async def get_categories(request: Request, db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    if current_user is None:
        return RedirectResponse(url="/login")

    # Fetch the user's categories
    categories = db.query(Category).filter(Category.owner_id == current_user.id).all()

    # Pass the categories to the template
    return templates.TemplateResponse(request, "categories.html",
                                      {"request": request, "categories": categories, "user": current_user})


@app.post("/categories/create", response_class=HTMLResponse)
async def create_category(
        request: Request,
        name: str = Form(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if current_user is None:
        return RedirectResponse(url="/login")
    try:
        # Create a new category
        new_category = Category(
            name=name,
            owner_id=current_user.id
        )
        db.add(new_category)
        db.commit()
        db.refresh(new_category)

        # Get current list of categories and notes for the user
        categories = db.query(Category).filter(Category.owner_id == current_user.id).all()
        notes = db.query(Note).filter(Note.owner_id == current_user.id).all()

        # Render the template with updated categories
        return templates.TemplateResponse(request, "base.html", {"request": request, "notes": notes, "categories": categories,
                                                        "user": current_user,
                                                        "message": "Category created successfully"})
    except Exception as e:
        print(f"An error occurred: {e}")
        return templates.TemplateResponse(request, "error_page.html", {"request": request, "error": str(e)})

@app.get("/categories/edit/{category_id}", response_class=HTMLResponse)
async def edit_category_get(
        request: Request,
        category_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    category = db.query(Category).filter(Category.id == category_id, Category.owner_id == current_user.id).first()
    if category is None:
        return templates.TemplateResponse(request, "error_page.html", {"request": request,
                                                              "error": "Category not found or not authorized to edit this category"})

    return templates.TemplateResponse(request, "edit_category.html", {"request": request, "category": category})


@app.post("/categories/edit/{category_id}", response_class=HTMLResponse)
async def update_category(
        request: Request,
        category_id: int,
        category_name: str = Form(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    try:
        # Fetch the category by ID
        category = db.query(Category).filter(Category.id == category_id, Category.owner_id == current_user.id).first()

        # Update the category name
        if category:
            category.name = category_name
            db.commit()
            db.refresh(category)
            message = "Category updated successfully"
        else:
            message = "Category not found"

        # Render the home page or another page after updating
        categories = db.query(Category).filter(Category.owner_id == current_user.id).all()
        notes = db.query(Note).filter(Note.owner_id == current_user.id).all()

        return templates.TemplateResponse(request, "base.html", {"request": request, "notes": notes, "categories": categories,
                                                        "user": current_user, "message": message})
    except Exception as e:
        print(f"An error occurred: {e}")
        return templates.TemplateResponse(request, "error_page.html", {"request": request, "error": str(e)})


@app.post("/categories/delete/{category_id}", response_class=HTMLResponse)
async def delete_category(
        request: Request,
        category_id: int = Path(..., description="The ID of the category to delete"),
        method: str = Form(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # Check the method override
    if method.lower() == "delete":
        category = db.query(Category).filter(Category.id == category_id, Category.owner_id == current_user.id).first()

        if category is None:
            raise HTTPException(status_code=404, detail="Category not found or not authorized to delete this category")

        # Delete the category
        db.delete(category)
        db.commit()

    # Fetch the remaining categories
    categories = db.query(Category).filter(Category.owner_id == current_user.id).all()
    # Pass the remaining categories and user information to the template
    return templates.TemplateResponse(request, "categories.html",
                                      {"request": request, "categories": categories, "user": current_user,
                                       "message": "Category deleted successfully"})


@app.get("/logout", response_class=HTMLResponse)
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="access_token")
    return response


@app.get("/notes/search", response_class=HTMLResponse)
async def search_notes(request: Request, query: str = Query(...), db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    if current_user is None:
        return RedirectResponse(url="/login")

    # Search for notes by title
    notes = db.query(Note).filter(Note.owner_id == current_user.id, Note.note_name.contains(query)).all()
    categories = db.query(Category).filter(Category.owner_id == current_user.id).all()

    # Pass the search results to the template
    return templates.TemplateResponse(request, "base.html", {"request": request, "notes": notes, "categories": categories,
                                                    "user": current_user, "search_query": query,
                                                    "message": "Search results for: " + query})
