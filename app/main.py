from datetime import timedelta
from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException, status, Form, Request, Query, Path
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.schemas import UserCreate, Token, UserBase
from app.database import get_db, Note, User
from app.auth import create_access_token, get_current_user, authenticate_user, \
    ACCESS_TOKEN_EXPIRE_MINUTES, get_password_hash

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static/"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("base.html", {"request": request})


@app.post("/users", response_model=UserCreate, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    hashed_password = get_password_hash(user.password)
    db_user = UserBase(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


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
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, username: str = Form(...), password: str = Form(...),
                     db: Session = Depends(get_db)):
    user = authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

    token = create_access_token(data={"sub": username})
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(key="access_token", value=token, httponly=True)  # Store token in cookie
    return response

@app.get("/notes/get", response_class=HTMLResponse)
async def create_note_get(request: Request, current_user: User = Depends(get_current_user)):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return templates.TemplateResponse("create_note.html", {"request": request})


@app.post("/notes/post", response_class=HTMLResponse)
async def create_note_post(
        request: Request,
        note_name: str = Form(...),
        description: str = Form(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    try:
        new_note = Note(note_name=note_name, description=description, owner_id=current_user.id)
        db.add(new_note)
        db.commit()
        db.refresh(new_note)
        return templates.TemplateResponse("base.html", {"request": request, "note": new_note})
    except Exception as e:
        print(f"An error occurred: {e}")
        return templates.TemplateResponse("error_page.html", {"request": request, "error": str(e)})


@app.delete("/notes/delete/{note_id}", response_class=HTMLResponse)
async def delete_note(
        request: Request,
        note_id: int = Path(..., description="The ID of the note to delete"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    note = db.query(Note).filter(Note.id == note_id, Note.owner_id == current_user.id).first()

    if note is None:
        raise HTTPException(status_code=404, detail="Note not found or not authorized to delete this note")

    db.delete(note)
    db.commit()
    return RedirectResponse("/", status_code=303)


@app.get("/logout", response_class=HTMLResponse)
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="access_token")
    return response