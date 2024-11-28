# Start with the official Python base image
FROM python:3.9-slim AS builder

# Set the working directory
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies and collect to a temporary directory
# --user installs locally to /root/.local, use this for leaner final images
RUN pip install --user --no-cache-dir -r requirements.txt

# Start a new image to keep it lean
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the installed packages and application code from the builder image
COPY --from=builder /root/.local /root/.local
COPY . .

# Set the environment variable to prioritize local Python dependencies
ENV PATH="/root/.local/bin:${PATH}"

# Set the command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]