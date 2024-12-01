import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base, User
from app.schemas import UserBase
from app.auth import create_access_token, get_current_user, get_password_hash

SQLALCHEMY_DATABASE_URL = "sqlite:///./tests/test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Mock function to replace get_current_user during tests
def override_get_current_user():
    return UserBase(username="testuser", hashed_password="hashed_testpassword", id=1)


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)


def login_client():
    """Simulate user login by creating an access token and setting it as a cookie."""
    db = next(override_get_db())

    # Ensure test user exists
    user = db.query(User).filter(User.username == "testuser").first()
    if not user:
        hashed_password = get_password_hash("testpassword")
        user = User(username="testuser", hashed_password=hashed_password)
        db.add(user)
        db.commit()
        db.refresh(user)

    # Create and set the token
    access_token = create_access_token(data={"sub": "testuser"})
    client.cookies.set("access_token", access_token)


def test_root_redirects_to_login():
    response = client.get("/")
    if response.status_code == 303:
        assert response.headers["location"].endswith("/login")
    else:
        assert response.status_code == 200


def test_create_user_valid_user():
    response = client.post("/users", json={"username": "unique_testuser", "password": "testpassword"})
    assert response.status_code == 201, f"Response data: {response.json()}"


def test_create_user_duplicate_username():
    client.post("/users", json={"username": "unique_user", "password": "testpassword"})
    response = client.post("/users", json={"username": "unique_user", "password": "testpassword"})
    assert response.status_code == 400


def test_get_token_with_valid_credentials():
    client.post("/users", json={"username": "valid_user", "password": "valid_password"})
    response = client.get("/get-token?username=valid_user&password=valid_password")
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"


def test_get_token_with_invalid_credentials():
    response = client.get("/get-token?username=invalid_user&password=invalid_password")
    assert response.status_code == 401


def test_login_get_page():
    response = client.get("/login")
    assert response.status_code == 200


def test_register_no_username():
    response = client.post("/register", data={"password": "test_password"})
    assert response.status_code == 422


def test_register_no_password():
    response = client.post("/register", data={"username": "test_user"})
    assert response.status_code == 422


class TestNotesEndpoints(unittest.TestCase):

    def setUp(self):
        self.user = UserBase(username="testuser", hashed_password="hashed_testpassword", id=1)
        self.access_token = create_access_token(data={"sub": "testuser"})

    def test_get_notes_authenticated(self):
        response = client.get("/notes", headers={"Authorization": f"Bearer {self.access_token}"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("notes", response.text)


    def test_create_note_post_success(self):
        response = client.post("/notes/post", headers={"Authorization": f"Bearer {self.access_token}"},
                               data={"note_name": "Test Note", "description": "This is a test note"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Note created successfully", response.text)

    def test_create_note_post_with_image(self):
        with open("test_image.png", "wb") as f:
            f.write(b"fake image content")
        with open("test_image.png", "rb") as img:
            response = client.post("/notes/post", headers={"Authorization": f"Bearer {self.access_token}"},
                                   data={"note_name": "Test Note", "description": "Test description"},
                                   files={"image": img})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Note created successfully", response.text)

    def tearDown(self):
        # Perform any necessary cleanup
        pass


if __name__ == "__main__":
    unittest.main()