# Start from the official Python 3.11 slim image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install dependencies needed to build Python packages and run FastAPI
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code to /app
COPY . .

# Ensure the tests will be run when building the image
RUN pytest

# Expose the port FastAPI runs on
EXPOSE 8000

# Run the FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
