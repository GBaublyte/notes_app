from fastapi import FastAPI, Depends, HTTPException, status, Form, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app import schemas
from app.schemas import UserBase, UserCreate, NoteCreate
from app.database import User, get_db, Note
from app.auth import create_access_token, get_current_user, fake_hash_password, fake_verify_password

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static/"), name="static")
templates = Jinja2Templates(directory="app/templates")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("base.html", {"request": request})

@app.post("/token", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not fake_verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/users", response_model=UserBase)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = fake_hash_password(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, username: str = Form(...), password: str = Form(...),
                     db: Session = Depends(get_db)):
    user = db.query(User).filter_by(username=username).first()

    if user is None:
        print("No user found with username:", username)  # Debugging statement
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

    if not fake_verify_password(password, user.hashed_password):
        print("Incorrect password for user:", username)  # Debugging statement
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

    token = create_access_token(data={"sub": user.username})
    if not token:
        print("Token creation failed for user:", username)  # Debugging statement
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

    response = RedirectResponse("/", status_code=303)
    response.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True)
    return response


@app.post("/notes/", response_model=NoteCreate, response_class=HTMLResponse)
async def create_note(request: Request, note: NoteCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = Note(**note.model_dump(), owner_id=current_user.id)
    db.add(note)
    db.commit()
    db.refresh(note)
    return templates.TemplateResponse("create_note.html", {"request": request})

@app.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="access_token")
    return response