# Use a lightweight Python base image (e.g., python:3.9-slim)
FROM python:3.9-slim

# Install ffmpeg and any needed system packages
RUN apt-get update && apt-get install -y ffmpeg && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create a working directory
WORKDIR /app

# Copy the requirements file first to leverage Docker layer caching
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir git+https://github.com/yt-dlp/yt-dlp.git

# Now copy the rest of the application code
COPY . /app

# Expose the port that Flask will run on
EXPOSE 5000

# By default, we run "app.py" with Python
CMD ["python", "app.py"]
