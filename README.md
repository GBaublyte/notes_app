# Notes Application

## Setup

1. Clone the repository
    ```sh
    git clone https://github.com/your-repo/notes_app.git
    cd notes_app
    ```
2. Create and activate a virtual environment
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
3. Install dependencies
    ```sh
    pip install -r requirements.txt
    ```

## Running the Application

```sh
uvicorn app.main:app --reload
```

## Using Docker

1. Build and run the Docker container
    ```sh
    docker-compose up --build
    ```

## Running Tests

```sh
pytest tests/
```