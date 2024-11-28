# Start with the official Python base image
FROM python:3.9-slim AS builder

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .

# Install dependencies and collect to a temporary directory
RUN pip install --user --no-cache-dir -r requirements.txt

# Start a new image to keep it lean
FROM python:3.9-slim

WORKDIR /app

# Copy the installed packages from the builder image
COPY --from=builder /root/.local /root/.local

# Update the PATH environment variable to ensure python installed packages can be found
ENV PATH=/root/.local/bin:$PATH

# Copy the application code
COPY . .

# Set the command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]