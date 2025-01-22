# Use a lightweight Python base image
FROM python:3.9-slim
FROM nvidia/cuda:12.0-base
# Install necessary system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the requirements file first to leverage Docker layer caching
COPY requirements.txt /app/requirements.txt

# Install compatible NumPy version
RUN pip install --no-cache-dir "numpy<2.0"

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Install the latest yt-dlp directly from GitHub
RUN pip install --no-cache-dir git+https://github.com/yt-dlp/yt-dlp.git

# Copy the rest of the application code
COPY . /app

# Expose the port Flask will run on
EXPOSE 5000

# Run the Flask application
CMD ["python", "app.py"]
