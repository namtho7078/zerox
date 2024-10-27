# Use an official Python image as a base
FROM python:3.12-slim

# Install system dependencies including make, curl, and pre-commit dependencies
RUN apt-get update && \
    apt-get install -y poppler-utils curl make git && \
    python3 -m ensurepip && \
    pip install --upgrade pip setuptools wheel && \
    rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"
# Add PYTHONPATH to locate pyzerox package
ENV PYTHONPATH="/app/py_zerox:$PYTHONPATH"

# Set the working directory
WORKDIR /app

# Copy the entire project into the container
COPY . .

# Install dependencies and build using Makefile
RUN make init
RUN make install-dev

# Expose port 5002 for FastAPI
EXPOSE 5002

# Run the FastAPI app with Uvicorn on port 5002
CMD ["poetry", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5002"]
